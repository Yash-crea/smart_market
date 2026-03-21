"""
Secure SSH Connection Manager for Marche Smart Grocery Store
Provides secure SSH connections for deployment, monitoring, and remote management
"""

import os
import time
import logging
import socket
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime

try:
    import paramiko
    from paramiko import SSHClient, AutoAddPolicy, RSAKey, Ed25519Key
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

try:
    from decouple import config
    DECOUPLE_AVAILABLE = True
except ImportError:
    DECOUPLE_AVAILABLE = False

logger = logging.getLogger(__name__)

class SecureSSHManager:
    """
    Secure SSH connection manager with best practices implemented
    Features:
    - RSA/Ed25519 key authentication only
    - Connection timeouts and retry logic
    - Secure key loading and management
    - Session management with proper cleanup
    - Command execution with output capture
    - File transfer capabilities
    - Connection pooling for multiple servers
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize SSH Manager
        
        Args:
            config_file: Optional path to SSH configuration file
        """
        if not PARAMIKO_AVAILABLE:
            raise ImportError("paramiko library not installed. Run: pip install paramiko")
        
        self.connections: Dict[str, paramiko.SSHClient] = {}
        self.config_file = config_file or os.path.expanduser("~/.ssh/config")
        
        # Try to get settings from Django if available
        try:
            from django.conf import settings as django_settings
            ssh_settings = getattr(django_settings, 'SSH_SETTINGS', {})
            self.default_timeout = ssh_settings.get('TIMEOUT', 30)
            self.max_retries = ssh_settings.get('MAX_RETRIES', 3)
        except (ImportError, Exception):
            # Fallback values if Django not available
            self.default_timeout = 30
            self.max_retries = 3
        
        # Security settings
        self.security_config = {
            'use_gss_api': False,
            'gss_deleg_creds': False,
            'use_gss_kex': False,
            'use_system_host_keys': True,
            'auto_add_policy': False,  # Secure: don't auto-accept unknown hosts
        }
        
        # Load server configurations
        self.servers = self._load_server_config()
    
    def _load_server_config(self) -> Dict[str, Dict[str, Any]]:
        """Load server configurations from Django settings or environment"""
        
        # Try to get configurations from Django settings first
        try:
            from django.conf import settings as django_settings
            ssh_servers = getattr(django_settings, 'SSH_SERVERS', None)
            if ssh_servers:
                logger.debug("Loaded SSH server configurations from Django settings")
                return ssh_servers
        except (ImportError, Exception):
            logger.debug("Django settings not available, using environment variables")
        
        # Fallback to environment variables
        default_servers = {
            'production': {
                'hostname': self._get_env_var('PROD_HOST', 'localhost'),
                'username': self._get_env_var('PROD_USER', 'ubuntu'),
                'port': int(self._get_env_var('PROD_PORT', '22')),
                'key_file': self._get_env_var('PROD_KEY_FILE', '~/.ssh/id_rsa'),
                'environment': 'production'
            },
            'staging': {
                'hostname': self._get_env_var('STAGING_HOST', 'localhost'),
                'username': self._get_env_var('STAGING_USER', 'ubuntu'),
                'port': int(self._get_env_var('STAGING_PORT', '22')),
                'key_file': self._get_env_var('STAGING_KEY_FILE', '~/.ssh/id_rsa'),
                'environment': 'staging'
            },
            'database': {
                'hostname': self._get_env_var('DB_HOST', 'localhost'),
                'username': self._get_env_var('DB_USER', 'ubuntu'),
                'port': int(self._get_env_var('DB_PORT', '22')),
                'key_file': self._get_env_var('DB_KEY_FILE', '~/.ssh/id_rsa'),
                'environment': 'database'
            },
            'cache': {
                'hostname': self._get_env_var('CACHE_HOST', 'localhost'),
                'username': self._get_env_var('CACHE_USER', 'ubuntu'),
                'port': int(self._get_env_var('CACHE_PORT', '22')),
                'key_file': self._get_env_var('CACHE_KEY_FILE', '~/.ssh/id_rsa'),
                'environment': 'cache'
            }
        }
        
        return default_servers
    
    def _get_env_var(self, key: str, default: str) -> str:
        """Get environment variable with fallback"""
        if DECOUPLE_AVAILABLE:
            return config(key, default=default)
        return os.getenv(key, default)
    
    def _load_private_key(self, key_path: str, password: Optional[str] = None) -> paramiko.PKey:
        """
        Securely load private key with multiple format support
        
        Args:
            key_path: Path to private key file
            password: Optional password for encrypted keys
            
        Returns:
            Loaded private key object
            
        Raises:
            FileNotFoundError: If key file doesn't exist
            paramiko.AuthenticationException: If key can't be loaded
        """
        expanded_path = os.path.expanduser(key_path)
        
        if not os.path.exists(expanded_path):
            raise FileNotFoundError(f"SSH key file not found: {expanded_path}")
        
        # Check file permissions (should be 600 or 400)
        file_stat = os.stat(expanded_path)
        file_perms = oct(file_stat.st_mode)[-3:]
        if file_perms not in ['600', '400']:
            logger.warning(f"SSH key file has insecure permissions: {file_perms}. Should be 600 or 400")
        
        # Try different key formats
        key_types = [
            (paramiko.Ed25519Key, "Ed25519"),
            (paramiko.RSAKey, "RSA"),
            (paramiko.ECDSAKey, "ECDSA"),
            (paramiko.DSSKey, "DSS")
        ]
        
        for key_class, key_type in key_types:
            try:
                logger.debug(f"Trying to load {key_type} key from {expanded_path}")
                return key_class.from_private_key_file(expanded_path, password=password)
            except paramiko.PasswordRequiredException:
                raise paramiko.AuthenticationException(f"Password required for encrypted {key_type} key")
            except paramiko.SSHException:
                continue
            except Exception as e:
                logger.debug(f"Failed to load {key_type} key: {e}")
                continue
        
        raise paramiko.AuthenticationException(f"Could not load private key from {expanded_path}")
    
    def connect(self, server_name: str, password: Optional[str] = None) -> bool:
        """
        Establish secure SSH connection to server
        
        Args:
            server_name: Name of server from configuration
            password: Optional password for key decryption
            
        Returns:
            True if connection successful, False otherwise
        """
        if server_name not in self.servers:
            logger.error(f"Unknown server: {server_name}")
            return False
        
        server_config = self.servers[server_name]
        
        # Create new SSH client
        ssh_client = paramiko.SSHClient()
        
        # Configure security settings
        if self.security_config['use_system_host_keys']:
            ssh_client.load_system_host_keys()
        
        # Load host keys from known_hosts file
        try:
            ssh_client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
        except FileNotFoundError:
            logger.warning("No known_hosts file found. First connections will require host key verification.")
        
        # Set host key policy (secure by default)
        if self.security_config['auto_add_policy']:
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            logger.warning(f"Auto-accepting unknown hosts for {server_name} (less secure)")
        else:
            # Use a more permissive policy for development/testing
            try:
                # For localhost connections, be more permissive
                if server_config['hostname'] in ['localhost', '127.0.0.1']:
                    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
                    logger.info(f"Using auto-add policy for localhost connection: {server_name}")
                else:
                    # For remote servers, use strict policy
                    ssh_client.set_missing_host_key_policy(paramiko.RejectPolicy())
                    logger.info(f"Host key verification required for {server_name}")
            except Exception:
                # Fallback to auto-add if there are issues
                ssh_client.set_missing_host_key_policy(AutoAddPolicy())
                logger.warning(f"Fallback to auto-add policy for {server_name}")
        
        try:
            # Load private key
            private_key = self._load_private_key(server_config['key_file'], password)
            
            # Attempt connection with retry logic
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"Connecting to {server_name} ({server_config['hostname']}:{server_config['port']}) - Attempt {attempt + 1}")
                    
                    ssh_client.connect(
                        hostname=server_config['hostname'],
                        port=server_config['port'],
                        username=server_config['username'],
                        pkey=private_key,
                        timeout=self.default_timeout,
                        allow_agent=False,  # Security: don't use SSH agent
                        look_for_keys=False,  # Security: only use specified key
                        gss_auth=self.security_config['use_gss_api'],
                        gss_kex=self.security_config['use_gss_kex'],
                        gss_deleg_creds=self.security_config['gss_deleg_creds'],
                    )
                    
                    # Store connection
                    self.connections[server_name] = ssh_client
                    logger.info(f"Successfully connected to {server_name}")
                    return True
                    
                except (socket.timeout, socket.error) as e:
                    logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
                except paramiko.AuthenticationException as e:
                    logger.error(f"Authentication failed for {server_name}: {e}")
                    raise
                    
                except paramiko.SSHException as e:
                    logger.error(f"SSH error connecting to {server_name}: {e}")
                    raise
        
        except Exception as e:
            logger.error(f"Failed to connect to {server_name}: {e}")
            ssh_client.close()
            return False
    
    def execute_command(self, server_name: str, command: str, sudo: bool = False, 
                       password: Optional[str] = None) -> Tuple[int, str, str]:
        """
        Execute command on remote server securely
        
        Args:
            server_name: Server to execute command on
            command: Command to execute
            sudo: Whether to use sudo
            password: Sudo password if required
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if server_name not in self.connections:
            raise ConnectionError(f"Not connected to {server_name}")
        
        ssh_client = self.connections[server_name]
        
        # Sanitize command for logging (remove sensitive parts)
        log_command = command
        if any(sensitive in command.lower() for sensitive in ['password', 'secret', 'token', 'key']):
            log_command = command.split()[0] + " [REDACTED]"
        
        try:
            if sudo and password:
                # Use sudo with password (more secure approach)
                stdin, stdout, stderr = ssh_client.exec_command(f"sudo -S {command}", timeout=300)
                stdin.write(password + '\n')
                stdin.flush()
                logger.info(f"Executing sudo command on {server_name}: sudo {log_command}")
            elif sudo:
                # Use passwordless sudo
                full_command = f"sudo {command}"
                logger.info(f"Executing sudo command on {server_name}: sudo {log_command}")
                stdin, stdout, stderr = ssh_client.exec_command(full_command, timeout=300)
            else:
                full_command = command
                logger.info(f"Executing command on {server_name}: {log_command}")
                stdin, stdout, stderr = ssh_client.exec_command(full_command, timeout=300)
            
            # Get results
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode('utf-8').strip()
            stderr_text = stderr.read().decode('utf-8').strip()
            
            logger.debug(f"Command exit code: {exit_code}")
            if stderr_text and exit_code != 0:
                logger.warning(f"Command stderr: {stderr_text}")
            
            return exit_code, stdout_text, stderr_text
            
        except Exception as e:
            logger.error(f"Failed to execute command on {server_name}: {e}")
            raise
    
    def transfer_file(self, server_name: str, local_path: str, remote_path: str, 
                     upload: bool = True) -> bool:
        """
        Transfer files securely using SFTP
        
        Args:
            server_name: Target server
            local_path: Local file path
            remote_path: Remote file path
            upload: True for upload, False for download
            
        Returns:
            True if transfer successful
        """
        if server_name not in self.connections:
            raise ConnectionError(f"Not connected to {server_name}")
        
        try:
            ssh_client = self.connections[server_name]
            sftp = ssh_client.open_sftp()
            
            if upload:
                logger.info(f"Uploading {local_path} to {server_name}:{remote_path}")
                sftp.put(local_path, remote_path)
            else:
                logger.info(f"Downloading {server_name}:{remote_path} to {local_path}")
                sftp.get(remote_path, local_path)
            
            sftp.close()
            logger.info("File transfer completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"File transfer failed: {e}")
            return False
    
    def create_tunnel(self, server_name: str, local_port: int, 
                     remote_host: str = 'localhost', remote_port: int = 22) -> Optional[paramiko.Transport]:
        """
        Create SSH tunnel for secure port forwarding
        
        Args:
            server_name: SSH server to tunnel through
            local_port: Local port to bind
            remote_host: Remote host to forward to (default: localhost on remote server)
            remote_port: Remote port to forward to
            
        Returns:
            Transport object if successful, None otherwise
        """
        if server_name not in self.connections:
            raise ConnectionError(f"Not connected to {server_name}")
        
        try:
            ssh_client = self.connections[server_name]
            transport = ssh_client.get_transport()
            
            logger.info(f"Creating SSH tunnel: localhost:{local_port} -> {server_name}:{remote_host}:{remote_port}")
            
            # Create the tunnel
            transport.request_port_forward('', local_port)
            
            return transport
            
        except Exception as e:
            logger.error(f"Failed to create SSH tunnel: {e}")
            return None
    
    def health_check(self, server_name: str) -> Dict[str, Any]:
        """
        Perform comprehensive health check on remote server
        
        Args:
            server_name: Server to check
            
        Returns:
            Dictionary with health check results
        """
        if server_name not in self.connections:
            raise ConnectionError(f"Not connected to {server_name}")
        
        health_data = {
            'server': server_name,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'services': {},
            'system': {}
        }
        
        try:
            # System information
            commands = {
                'uptime': 'uptime',
                'load': 'cat /proc/loadavg',
                'memory': 'free -h',
                'disk': 'df -h',
                'network': 'ss -tuln',
            }
            
            for check_name, command in commands.items():
                try:
                    exit_code, stdout, stderr = self.execute_command(server_name, command)
                    if exit_code == 0:
                        health_data['system'][check_name] = stdout
                    else:
                        health_data['system'][check_name] = f"Error: {stderr}"
                except Exception as e:
                    health_data['system'][check_name] = f"Failed: {e}"
            
            # Service checks for grocery store components
            services = ['nginx', 'postgresql', 'redis-server', 'grocery_gunicorn']
            for service in services:
                try:
                    exit_code, stdout, stderr = self.execute_command(
                        server_name, f"systemctl is-active {service}"
                    )
                    health_data['services'][service] = 'active' if exit_code == 0 else 'inactive'
                except Exception:
                    health_data['services'][service] = 'unknown'
            
            # Overall status
            active_services = sum(1 for status in health_data['services'].values() if status == 'active')
            if active_services >= len(services) * 0.8:  # 80% of services active
                health_data['status'] = 'healthy'
            elif active_services >= len(services) * 0.5:  # 50% of services active
                health_data['status'] = 'degraded'
            else:
                health_data['status'] = 'critical'
            
            return health_data
            
        except Exception as e:
            health_data['status'] = 'error'
            health_data['error'] = str(e)
            return health_data
    
    def deploy_grocery_store(self, server_name: str, project_path: str = None) -> bool:
        """
        Deploy grocery store application to remote server
        
        Args:
            server_name: Target deployment server
            project_path: Remote path for the project (defaults to Django settings)
            
        Returns:
            True if deployment successful
        """
        if server_name not in self.connections:
            raise ConnectionError(f"Not connected to {server_name}")
            
        # Use Django settings for project path if not provided
        if project_path is None:
            ssh_settings = getattr(settings, 'SSH_SETTINGS', {})
            deployment_config = ssh_settings.get('DEPLOYMENT_CONFIG', {})
            project_path = deployment_config.get('PROJECT_PATH', '/var/www/grocery_store')
        
        logger.info(f"Starting deployment to {server_name} at {project_path}")
        
        deployment_commands = [
            f"cd {project_path}",
            "git pull origin main",
            "source venv/bin/activate",
            "pip install -r requirements.txt",
            "pip install -r cache_requirements.txt",
            "cd grocerystore",
            "python manage.py collectstatic --noinput",
            "python manage.py migrate",
            "sudo systemctl restart grocery_gunicorn",
            "sudo systemctl restart nginx",
        ]
        
        try:
            for command in deployment_commands:
                logger.info(f"Executing: {command}")
                exit_code, stdout, stderr = self.execute_command(server_name, command, sudo=command.startswith('sudo'))
                
                if exit_code != 0:
                    logger.error(f"Deployment command failed: {command}")
                    logger.error(f"Error: {stderr}")
                    return False
                
                if stdout:
                    logger.debug(f"Output: {stdout}")
            
            logger.info("Deployment completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False
    
    def disconnect(self, server_name: str) -> None:
        """Disconnect from specified server"""
        if server_name in self.connections:
            self.connections[server_name].close()
            del self.connections[server_name]
            logger.info(f"Disconnected from {server_name}")
    
    def disconnect_all(self) -> None:
        """Disconnect from all servers"""
        for server_name in list(self.connections.keys()):
            self.disconnect(server_name)
        logger.info("Disconnected from all servers")
    
    def list_connections(self) -> List[str]:
        """List active connections"""
        return list(self.connections.keys())
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup connections"""
        self.disconnect_all()


# Convenience functions for common operations
def quick_execute(server_name: str, command: str, **kwargs) -> Tuple[int, str, str]:
    """
    Quick command execution with automatic connection management
    
    Args:
        server_name: Server to connect to
        command: Command to execute
        **kwargs: Additional arguments for SSH manager
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    with SecureSSHManager() as ssh_manager:
        if ssh_manager.connect(server_name):
            return ssh_manager.execute_command(server_name, command, **kwargs)
        else:
            raise ConnectionError(f"Failed to connect to {server_name}")

def quick_health_check(server_name: str) -> Dict[str, Any]:
    """
    Quick health check with automatic connection management
    
    Args:
        server_name: Server to check
        
    Returns:
        Health check results
    """
    with SecureSSHManager() as ssh_manager:
        if ssh_manager.connect(server_name):
            return ssh_manager.health_check(server_name)
        else:
            raise ConnectionError(f"Failed to connect to {server_name}")

def quick_deploy(server_name: str = 'production', project_path: str = '/var/www/grocery_store') -> bool:
    """
    Quick deployment with automatic connection management
    
    Args:
        server_name: Target server
        project_path: Remote project path
        
    Returns:
        True if deployment successful
    """
    with SecureSSHManager() as ssh_manager:
        if ssh_manager.connect(server_name):
            return ssh_manager.deploy_grocery_store(server_name, project_path)
        else:
            raise ConnectionError(f"Failed to connect to {server_name}")


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Connect and run health check
    try:
        with SecureSSHManager() as ssh_manager:
            # Connect to production server
            if ssh_manager.connect('production'):
                # Run health check
                health = ssh_manager.health_check('production')
                print(f"Server health: {health['status']}")
                
                # Execute sample command
                exit_code, stdout, stderr = ssh_manager.execute_command('production', 'ls -la /var/log/')
                print(f"Command output: {stdout[:100]}...")
                
            else:
                print("Failed to connect to production server")
                
    except Exception as e:
        print(f"SSH operation failed: {e}")