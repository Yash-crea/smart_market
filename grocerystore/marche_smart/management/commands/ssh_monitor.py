"""
Django management command for SSH-based server monitoring
Usage: python manage.py ssh_monitor [options]
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging
import sys
import os
import time
import json
from datetime import datetime

try:
    from marche_smart.ssh_manager import SecureSSHManager
    SSH_AVAILABLE = True
except ImportError as e:
    SSH_AVAILABLE = False
    SSH_ERROR = str(e)


class Command(BaseCommand):
    help = 'Monitor remote servers via SSH for Grocery Store application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--servers',
            type=str,
            nargs='+',
            default=['production'],
            help='Server names to monitor (production, staging, database, cache)'
        )
        
        parser.add_argument(
            '--interval',
            type=int,
            default=300,  # 5 minutes
            help='Monitoring interval in seconds'
        )
        
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run monitoring check once instead of continuous monitoring'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            choices=['console', 'json', 'file'],
            default='console',
            help='Output format'
        )
        
        parser.add_argument(
            '--output-file',
            type=str,
            help='File path for output (required if --output=file)'
        )
        
        parser.add_argument(
            '--alerts',
            action='store_true',
            help='Enable alert notifications for critical issues'
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

        servers = options['servers']
        interval = options['interval']
        run_once = options['once']
        output_format = options['output']
        alerts_enabled = options['alerts']

        self.stdout.write(
            self.style.SUCCESS(f'🔍 Starting SSH monitoring for servers: {", ".join(servers)}')
        )

        if output_format == 'file' and not options['output_file']:
            raise CommandError("--output-file is required when --output=file")

        try:
            if run_once:
                self._monitor_once(servers, output_format, options.get('output_file'), alerts_enabled)
            else:
                self._monitor_continuous(servers, interval, output_format, options.get('output_file'), alerts_enabled)

        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\n🛑 Monitoring stopped by user"))
        except Exception as e:
            raise CommandError(f"Monitoring failed: {e}")

    def _monitor_once(self, servers, output_format, output_file, alerts_enabled):
        """Run monitoring check once"""
        results = self._check_all_servers(servers)
        self._output_results(results, output_format, output_file)
        
        if alerts_enabled:
            self._check_alerts(results)

    def _monitor_continuous(self, servers, interval, output_format, output_file, alerts_enabled):
        """Run continuous monitoring"""
        self.stdout.write(f"📊 Continuous monitoring every {interval} seconds")
        self.stdout.write("Press Ctrl+C to stop monitoring")
        
        iteration = 0
        while True:
            iteration += 1
            
            self.stdout.write(f"\n🔄 Monitoring iteration #{iteration} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            results = self._check_all_servers(servers)
            self._output_results(results, output_format, output_file, iteration)
            
            if alerts_enabled:
                self._check_alerts(results)
            
            # Summary for console output
            if output_format == 'console':
                healthy = sum(1 for r in results if r['status'] == 'healthy')
                total = len(results)
                self.stdout.write(f"📈 Summary: {healthy}/{total} servers healthy")
            
            time.sleep(interval)

    def _check_all_servers(self, servers):
        """Check health of all specified servers"""
        results = []
        
        with SecureSSHManager() as ssh_manager:
            for server_name in servers:
                self.stdout.write(f"🔍 Checking {server_name}...", ending='')
                
                try:
                    # Attempt connection
                    if ssh_manager.connect(server_name):
                        health_data = ssh_manager.health_check(server_name)
                        
                        # Add server connection info
                        health_data['connected'] = True
                        health_data['connection_time'] = datetime.now().isoformat()
                        
                        # Get additional metrics
                        health_data.update(self._get_additional_metrics(ssh_manager, server_name))
                        
                        results.append(health_data)
                        
                        status = health_data['status']
                        if status == 'healthy':
                            self.stdout.write(self.style.SUCCESS(" ✅"))
                        elif status == 'degraded':
                            self.stdout.write(self.style.WARNING(" ⚠️"))
                        else:
                            self.stdout.write(self.style.ERROR(" ❌"))
                    
                    else:
                        # Connection failed
                        error_data = {
                            'server': server_name,
                            'timestamp': datetime.now().isoformat(),
                            'status': 'connection_failed',
                            'connected': False,
                            'error': 'SSH connection failed'
                        }
                        results.append(error_data)
                        self.stdout.write(self.style.ERROR(" 🔌❌"))
                
                except Exception as e:
                    # Error during health check
                    error_data = {
                        'server': server_name,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'error',
                        'connected': False,
                        'error': str(e)
                    }
                    results.append(error_data)
                    self.stdout.write(self.style.ERROR(f" ❌ ({str(e)[:30]}...)"))
        
        return results

    def _get_additional_metrics(self, ssh_manager, server_name):
        """Get additional monitoring metrics"""
        additional_metrics = {}
        
        try:
            # CPU usage
            exit_code, stdout, stderr = ssh_manager.execute_command(
                server_name, "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"
            )
            if exit_code == 0 and stdout:
                additional_metrics['cpu_usage'] = stdout.strip()
            
            # Memory percentage
            exit_code, stdout, stderr = ssh_manager.execute_command(
                server_name, "free | awk '/Mem:/ {printf \"%.1f\", $3/$2 * 100}'"
            )
            if exit_code == 0 and stdout:
                additional_metrics['memory_usage_percent'] = f"{stdout.strip()}%"
            
            # Disk usage for root
            exit_code, stdout, stderr = ssh_manager.execute_command(
                server_name, "df / | awk 'NR==2 {print $5}'"
            )
            if exit_code == 0 and stdout:
                additional_metrics['disk_usage_root'] = stdout.strip()
            
            # Active connections
            exit_code, stdout, stderr = ssh_manager.execute_command(
                server_name, "ss -tuln | wc -l"
            )
            if exit_code == 0 and stdout:
                additional_metrics['active_connections'] = stdout.strip()
            
            # Check if grocery store application is responding
            exit_code, stdout, stderr = ssh_manager.execute_command(
                server_name, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/cache/stats/ || echo 'connection_failed'"
            )
            if exit_code == 0:
                if '200' in stdout or '401' in stdout or '403' in stdout:  # API responding
                    additional_metrics['api_status'] = 'responding'
                else:
                    additional_metrics['api_status'] = 'not_responding'
            
        except Exception as e:
            additional_metrics['metrics_error'] = str(e)
        
        return additional_metrics

    def _output_results(self, results, output_format, output_file, iteration=None):
        """Output monitoring results in specified format"""
        
        if output_format == 'json':
            if output_file:
                # Append to file
                with open(output_file, 'a') as f:
                    for result in results:
                        f.write(json.dumps(result) + '\n')
            else:
                # Output to console
                for result in results:
                    self.stdout.write(json.dumps(result, indent=2))
        
        elif output_format == 'file':
            # Write formatted output to file
            with open(output_file, 'a') as f:
                if iteration:
                    f.write(f"\n=== Monitoring Iteration #{iteration} ===\n")
                
                for result in results:
                    f.write(f"Server: {result['server']}\n")
                    f.write(f"Status: {result['status']}\n")
                    f.write(f"Time: {result['timestamp']}\n")
                    
                    if 'services' in result:
                        f.write("Services:\n")
                        for service, status in result['services'].items():
                            f.write(f"  {service}: {status}\n")
                    
                    if 'api_status' in result:
                        f.write(f"API Status: {result['api_status']}\n")
                    
                    f.write(f"Connected: {result.get('connected', False)}\n")
                    f.write("---\n")
        
        elif output_format == 'console':
            # Already handled in _check_all_servers for console output
            pass

    def _check_alerts(self, results):
        """Check for critical issues and display alerts"""
        alerts = []
        
        for result in results:
            server = result['server']
            status = result['status']
            
            # Critical status alerts
            if status == 'critical':
                alerts.append(f"🚨 CRITICAL: {server} is in critical state")
            elif status == 'connection_failed':
                alerts.append(f"🔌 CONNECTION FAILED: Cannot connect to {server}")
            elif status == 'error':
                error = result.get('error', 'Unknown error')
                alerts.append(f"❌ ERROR: {server} - {error}")
            
            # Service-specific alerts
            if 'services' in result:
                for service, service_status in result['services'].items():
                    if service_status != 'active':
                        alerts.append(f"🔧 SERVICE DOWN: {service} on {server} is {service_status}")
            
            # API alerts
            if result.get('api_status') == 'not_responding':
                alerts.append(f"🌐 API DOWN: Grocery Store API not responding on {server}")
            
            # Resource usage alerts (if available)
            if 'disk_usage_root' in result:
                disk_usage = result['disk_usage_root'].replace('%', '')
                try:
                    if int(disk_usage) > 90:
                        alerts.append(f"💾 DISK SPACE: {server} disk usage at {disk_usage}%")
                except ValueError:
                    pass
            
            if 'memory_usage_percent' in result:
                memory_usage = result['memory_usage_percent'].replace('%', '')
                try:
                    if float(memory_usage) > 90:
                        alerts.append(f"🧠 MEMORY: {server} memory usage at {memory_usage}%")
                except ValueError:
                    pass
        
        # Display alerts
        if alerts:
            self.stdout.write(self.style.ERROR("\n🚨 ALERTS:"))
            for alert in alerts:
                self.stdout.write(self.style.ERROR(f"  {alert}"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ No critical alerts"))

    def _get_server_summary(self, results):
        """Get summary statistics for servers"""
        total_servers = len(results)
        healthy_servers = sum(1 for r in results if r['status'] == 'healthy')
        degraded_servers = sum(1 for r in results if r['status'] == 'degraded')
        critical_servers = sum(1 for r in results if r['status'] == 'critical')
        failed_connections = sum(1 for r in results if not r.get('connected', False))
        
        return {
            'total': total_servers,
            'healthy': healthy_servers,
            'degraded': degraded_servers,
            'critical': critical_servers,
            'connection_failed': failed_connections,
            'health_percentage': (healthy_servers / total_servers * 100) if total_servers > 0 else 0
        }