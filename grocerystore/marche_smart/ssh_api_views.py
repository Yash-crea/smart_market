"""
SSH API endpoints for secure server management
Provides RESTful API access to SSH operations for authorized users
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
import logging
import json

try:
    from .ssh_manager import SecureSSHManager, quick_health_check, quick_deploy
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False

logger = logging.getLogger(__name__)


def is_staff_user(user):
    """Check if user has staff permissions"""
    return user.is_authenticated and user.is_staff


def is_superuser(user):
    """Check if user is superuser"""
    return user.is_authenticated and user.is_superuser


def check_ssh_enabled():
    """Check if SSH features are enabled"""
    return getattr(settings, 'SSH_ENABLED', False) and SSH_AVAILABLE


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_staff_user)
def ssh_server_status(request):
    """
    Get status of all configured SSH servers
    GET /api/v1/ssh/status/
    """
    if not check_ssh_enabled():
        return Response({
            'error': 'SSH features not available',
            'ssh_enabled': check_ssh_enabled(),
            'ssh_available': SSH_AVAILABLE
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    server_names = request.query_params.get('servers', '').split(',') or ['production']
    server_names = [name.strip() for name in server_names if name.strip()]
    
    results = []
    ssh_servers = getattr(settings, 'SSH_SERVERS', {})
    
    for server_name in server_names:
        if server_name not in ssh_servers:
            results.append({
                'server': server_name,
                'status': 'not_configured',
                'error': f'Server {server_name} not configured'
            })
            continue
        
        try:
            # Quick connection test
            with SecureSSHManager() as ssh_manager:
                if ssh_manager.connect(server_name):
                    server_info = {
                        'server': server_name,
                        'status': 'connected',
                        'hostname': ssh_servers[server_name]['hostname'],
                        'username': ssh_servers[server_name]['username'],
                        'port': ssh_servers[server_name]['port'],
                        'environment': ssh_servers[server_name]['environment'],
                        'connected_at': timezone.now().isoformat()
                    }
                    results.append(server_info)
                else:
                    results.append({
                        'server': server_name,
                        'status': 'connection_failed',
                        'hostname': ssh_servers[server_name]['hostname'],
                        'error': 'SSH connection failed'
                    })
        
        except Exception as e:
            logger.error(f"SSH status check failed for {server_name}: {e}")
            results.append({
                'server': server_name,
                'status': 'error',
                'error': str(e)
            })
    
    return Response({
        'servers': results,
        'total_servers': len(results),
        'timestamp': timezone.now(),
        'ssh_enabled': True
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_staff_user)
def ssh_health_check(request):
    """
    Perform comprehensive health check on specified servers
    GET /api/v1/ssh/health/
    """
    if not check_ssh_enabled():
        return Response({
            'error': 'SSH features not available'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    server_names = request.query_params.get('servers', 'production').split(',')
    server_names = [name.strip() for name in server_names if name.strip()]
    
    results = []
    
    for server_name in server_names:
        try:
            logger.info(f"Performing health check on {server_name}")
            health_data = quick_health_check(server_name)
            results.append(health_data)
            
        except Exception as e:
            logger.error(f"Health check failed for {server_name}: {e}")
            results.append({
                'server': server_name,
                'status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            })
    
    # Calculate summary statistics
    total_servers = len(results)
    healthy_servers = sum(1 for r in results if r.get('status') == 'healthy')
    
    return Response({
        'health_checks': results,
        'summary': {
            'total_servers': total_servers,
            'healthy_servers': healthy_servers,
            'health_percentage': (healthy_servers / total_servers * 100) if total_servers > 0 else 0,
            'overall_status': 'healthy' if healthy_servers == total_servers else 'degraded' if healthy_servers > 0 else 'critical'
        },
        'checked_at': timezone.now()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_staff_user)
def ssh_deploy(request):
    """
    Deploy application to specified server
    POST /api/v1/ssh/deploy/
    Body: {
        "server": "production",
        "project_path": "/var/www/grocery_store" (optional)
    }
    """
    if not check_ssh_enabled():
        return Response({
            'error': 'SSH features not available'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    server_name = request.data.get('server', 'production')
    project_path = request.data.get('project_path', getattr(settings, 'DEPLOYMENT_SETTINGS', {}).get('REMOTE_PROJECT_PATH', '/var/www/grocery_store'))
    
    # Additional security check for production deployments
    if server_name == 'production' and not request.user.is_superuser:
        return Response({
            'error': 'Production deployment requires superuser privileges'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        logger.info(f"Starting deployment to {server_name} by user {request.user.username}")
        
        # Pre-deployment health check
        pre_health = quick_health_check(server_name)
        
        # Perform deployment
        success = quick_deploy(server_name, project_path)
        
        if success:
            # Post-deployment health check
            post_health = quick_health_check(server_name)
            
            # Log deployment
            logger.info(f"Deployment to {server_name} successful by {request.user.username}")
            
            return Response({
                'message': f'Deployment to {server_name} completed successfully',
                'server': server_name,
                'project_path': project_path,
                'deployed_by': request.user.username,
                'deployed_at': timezone.now(),
                'pre_deployment_health': pre_health.get('status', 'unknown'),
                'post_deployment_health': post_health.get('status', 'unknown'),
                'deployment_successful': True
            })
        else:
            logger.error(f"Deployment to {server_name} failed for user {request.user.username}")
            return Response({
                'error': f'Deployment to {server_name} failed',
                'deployment_successful': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        return Response({
            'error': f'Deployment failed: {str(e)}',
            'deployment_successful': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_superuser)  # Only superusers can execute commands
def ssh_execute(request):
    """
    Execute command on remote server (SUPERUSER ONLY)
    POST /api/v1/ssh/execute/
    Body: {
        "server": "staging",
        "command": "systemctl status nginx",
        "sudo": false
    }
    """
    if not check_ssh_enabled():
        return Response({
            'error': 'SSH features not available'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    server_name = request.data.get('server')
    command = request.data.get('command')
    use_sudo = request.data.get('sudo', False)
    
    if not server_name or not command:
        return Response({
            'error': 'Both server and command are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Security: Block potentially dangerous commands
    dangerous_commands = ['rm -rf', 'dd if=', 'mkfs', 'fdisk', 'parted', 'shutdown', 'init 0', 'halt']
    if any(dangerous in command.lower() for dangerous in dangerous_commands):
        logger.warning(f"Blocked dangerous command from user {request.user.username}: {command}")
        return Response({
            'error': 'Command blocked for security reasons'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        logger.info(f"Executing command on {server_name} by user {request.user.username}: {command}")
        
        with SecureSSHManager() as ssh_manager:
            if ssh_manager.connect(server_name):
                exit_code, stdout, stderr = ssh_manager.execute_command(
                    server_name, command, sudo=use_sudo
                )
                
                response_data = {
                    'server': server_name,
                    'command': command,
                    'exit_code': exit_code,
                    'stdout': stdout,
                    'stderr': stderr,
                    'executed_by': request.user.username,
                    'executed_at': timezone.now(),
                    'success': exit_code == 0
                }
                
                # Log command execution
                logger.info(f"Command executed on {server_name} with exit code {exit_code}")
                
                return Response(response_data)
            else:
                return Response({
                    'error': f'Failed to connect to {server_name}'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return Response({
            'error': f'Command execution failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@user_passes_test(is_staff_user)
def ssh_config(request):
    """
    Get SSH configuration information
    GET /api/v1/ssh/config/
    """
    if not request.user.is_staff:
        return Response({
            'error': 'Staff access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    ssh_servers = getattr(settings, 'SSH_SERVERS', {})
    ssh_settings = getattr(settings, 'SSH_SETTINGS', {})
    deployment_settings = getattr(settings, 'DEPLOYMENT_SETTINGS', {})
    
    # Remove sensitive information (key file paths)
    safe_servers = {}
    for name, config in ssh_servers.items():
        safe_servers[name] = {
            'hostname': config['hostname'],
            'username': config['username'],
            'port': config['port'],
            'environment': config['environment'],
            'key_configured': bool(config.get('key_file'))
        }
    
    return Response({
        'ssh_enabled': check_ssh_enabled(),
        'ssh_available': SSH_AVAILABLE,
        'servers': safe_servers,
        'ssh_settings': ssh_settings,
        'deployment_settings': deployment_settings,
        'permissions': getattr(settings, 'SSH_PERMISSIONS', {}),
        'user_permissions': {
            'can_monitor': request.user.is_staff,
            'can_deploy': request.user.is_staff,
            'can_execute_commands': request.user.is_superuser
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])  
@user_passes_test(is_staff_user)
def ssh_tunnel(request):
    """
    Create SSH tunnel for database/cache access
    POST /api/v1/ssh/tunnel/
    Body: {
        "server": "database",
        "local_port": 5432,
        "remote_host": "localhost",
        "remote_port": 5432
    }
    """
    if not check_ssh_enabled():
        return Response({
            'error': 'SSH features not available'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    server_name = request.data.get('server')
    local_port = request.data.get('local_port')
    remote_host = request.data.get('remote_host', 'localhost')
    remote_port = request.data.get('remote_port')
    
    if not all([server_name, local_port, remote_port]):
        return Response({
            'error': 'server, local_port, and remote_port are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        logger.info(f"Creating SSH tunnel to {server_name} by user {request.user.username}")
        
        with SecureSSHManager() as ssh_manager:
            if ssh_manager.connect(server_name):
                transport = ssh_manager.create_tunnel(
                    server_name, local_port, remote_host, remote_port
                )
                
                if transport:
                    return Response({
                        'message': f'SSH tunnel created successfully',
                        'server': server_name,
                        'local_port': local_port,
                        'remote_host': remote_host,
                        'remote_port': remote_port,
                        'created_by': request.user.username,
                        'created_at': timezone.now(),
                        'tunnel_active': True
                    })
                else:
                    return Response({
                        'error': 'Failed to create SSH tunnel'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    'error': f'Failed to connect to {server_name}'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    except Exception as e:
        logger.error(f"SSH tunnel creation error: {e}")
        return Response({
            'error': f'Tunnel creation failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)