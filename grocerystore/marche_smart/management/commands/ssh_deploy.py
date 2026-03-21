"""
Django management command for SSH-based deployment operations
Usage: python manage.py ssh_deploy [options]
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging
import sys
import os

try:
    from marche_smart.ssh_manager import SecureSSHManager, quick_deploy, quick_health_check
    SSH_AVAILABLE = True
except ImportError as e:
    SSH_AVAILABLE = False
    SSH_ERROR = str(e)


class Command(BaseCommand):
    help = 'Secure SSH deployment and server management for Grocery Store'

    def add_arguments(self, parser):
        parser.add_argument(
            '--server',
            type=str,
            default='production',
            help='Target server name (production, staging, database, cache)'
        )
        
        parser.add_argument(
            '--action',
            type=str,
            choices=['deploy', 'health-check', 'connect', 'execute'],
            default='health-check',
            help='Action to perform on remote server'
        )
        
        parser.add_argument(
            '--command',
            type=str,
            help='Command to execute (for --action=execute)'
        )
        
        parser.add_argument(
            '--project-path',
            type=str,
            default='/var/www/grocery_store',
            help='Remote project path for deployment'
        )
        
        parser.add_argument(
            '--sudo',
            action='store_true',
            help='Use sudo for command execution'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging'
        )

    def handle(self, *args, **options):
        if not SSH_AVAILABLE:
            raise CommandError(f"SSH functionality not available: {SSH_ERROR}")

        # Configure logging
        if options['verbose']:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        server_name = options['server']
        action = options['action']

        self.stdout.write(
            self.style.SUCCESS(f'🚀 Starting SSH operation: {action} on {server_name}')
        )

        try:
            if action == 'health-check':
                self._health_check(server_name)
            
            elif action == 'deploy':
                self._deploy(server_name, options['project_path'])
            
            elif action == 'connect':
                self._test_connection(server_name)
            
            elif action == 'execute':
                if not options['command']:
                    raise CommandError("--command is required for execute action")
                self._execute_command(server_name, options['command'], options['sudo'])

        except Exception as e:
            raise CommandError(f"SSH operation failed: {e}")

    def _health_check(self, server_name):
        """Perform health check on remote server"""
        self.stdout.write(f"🔍 Performing health check on {server_name}...")
        
        try:
            health_data = quick_health_check(server_name)
            
            # Display results
            status = health_data['status']
            if status == 'healthy':
                status_style = self.style.SUCCESS
            elif status == 'degraded':
                status_style = self.style.WARNING
            else:
                status_style = self.style.ERROR
            
            self.stdout.write(f"Server Status: {status_style(status.upper())}")
            
            # System information
            if 'system' in health_data:
                self.stdout.write("\n📊 System Information:")
                system = health_data['system']
                if 'uptime' in system:
                    self.stdout.write(f"  Uptime: {system['uptime']}")
                if 'load' in system:
                    self.stdout.write(f"  Load: {system['load']}")
                if 'memory' in system:
                    self.stdout.write(f"  Memory: {system['memory'].split()[1:3]}")
            
            # Services
            if 'services' in health_data:
                self.stdout.write("\n🔧 Services Status:")
                for service, status in health_data['services'].items():
                    if status == 'active':
                        style = self.style.SUCCESS
                    else:
                        style = self.style.ERROR
                    self.stdout.write(f"  {service}: {style(status)}")
            
            self.stdout.write(f"\n✅ Health check completed at {health_data.get('timestamp', 'unknown')}")
            
        except Exception as e:
            raise CommandError(f"Health check failed: {e}")

    def _deploy(self, server_name, project_path):
        """Deploy application to remote server"""
        self.stdout.write(f"🚀 Deploying to {server_name} at {project_path}...")
        
        try:
            success = quick_deploy(server_name, project_path)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS("✅ Deployment completed successfully!")
                )
                
                # Run post-deployment health check
                self.stdout.write("🔍 Running post-deployment health check...")
                health_data = quick_health_check(server_name)
                status = health_data['status']
                
                if status == 'healthy':
                    self.stdout.write(
                        self.style.SUCCESS(f"🎉 Server is {status} after deployment")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Server status: {status} - please investigate")
                    )
            else:
                raise CommandError("Deployment failed")
                
        except Exception as e:
            raise CommandError(f"Deployment failed: {e}")

    def _test_connection(self, server_name):
        """Test SSH connection to server"""
        self.stdout.write(f"🔗 Testing connection to {server_name}...")
        
        try:
            with SecureSSHManager() as ssh_manager:
                if ssh_manager.connect(server_name):
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Successfully connected to {server_name}")
                    )
                    
                    # Get basic server info
                    exit_code, stdout, stderr = ssh_manager.execute_command(
                        server_name, 'uname -a && whoami'
                    )
                    
                    if exit_code == 0:
                        self.stdout.write(f"📋 Server info:\n{stdout}")
                    
                else:
                    raise CommandError(f"Failed to connect to {server_name}")
                    
        except Exception as e:
            raise CommandError(f"Connection test failed: {e}")

    def _execute_command(self, server_name, command, use_sudo):
        """Execute command on remote server"""
        self.stdout.write(f"⚡ Executing command on {server_name}: {command}")
        
        try:
            with SecureSSHManager() as ssh_manager:
                if ssh_manager.connect(server_name):
                    exit_code, stdout, stderr = ssh_manager.execute_command(
                        server_name, command, sudo=use_sudo
                    )
                    
                    self.stdout.write(f"Exit Code: {exit_code}")
                    
                    if stdout:
                        self.stdout.write("📤 Output:")
                        self.stdout.write(stdout)
                    
                    if stderr and exit_code != 0:
                        self.stdout.write(
                            self.style.ERROR(f"❌ Error:\n{stderr}")
                        )
                    
                    if exit_code == 0:
                        self.stdout.write(
                            self.style.SUCCESS("✅ Command executed successfully")
                        )
                    
                else:
                    raise CommandError(f"Failed to connect to {server_name}")
                    
        except Exception as e:
            raise CommandError(f"Command execution failed: {e}")