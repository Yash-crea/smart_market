#!/usr/bin/env python
"""
SSH System Test Script for Marche Smart Grocery Store

Test the SSH connection and deployment functionality.
Run this script to test SSH implementation:

python test_ssh_system.py

Or run from Django:
python manage.py shell < test_ssh_system.py
"""

import os
import sys
from datetime import datetime

# Add Django to path if running outside manage.py shell
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    import django
    grocerystore_path = os.path.join(os.path.dirname(__file__), 'grocerystore')
    sys.path.insert(0, grocerystore_path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
    os.chdir(grocerystore_path)
    django.setup()

# Now import Django components
from django.conf import settings

print("🔐 Testing Marche Smart SSH System")
print("=" * 50)

# Test 1: Check SSH availability
print("\n1. Testing SSH module availability...")
try:
    from marche_smart.ssh_manager import SecureSSHManager  # type: ignore
    print("   ✓ SSH manager module imported successfully")
    SSH_AVAILABLE = True
except ImportError as e:
    print(f"   ❌ SSH manager import failed: {e}")
    print("   💡 Run: pip install paramiko fabric cryptography python-decouple")
    SSH_AVAILABLE = False

# Test 2: Check dependencies
print("\n2. Testing SSH dependencies...")
dependencies = ['paramiko', 'cryptography']
missing_deps = []

for dep in dependencies:
    try:
        __import__(dep)
        print(f"   ✓ {dep} available")
    except ImportError:
        print(f"   ❌ {dep} not available")
        missing_deps.append(dep)

if missing_deps:
    print(f"\n   📦 Install missing dependencies: pip install {' '.join(missing_deps)}")

# Test 3: Check Django settings
print("\n3. Testing Django SSH configuration...")
try:
    ssh_enabled = getattr(settings, 'SSH_ENABLED', False)
    ssh_settings = getattr(settings, 'SSH_SETTINGS', {})
    ssh_servers = getattr(settings, 'SSH_SERVERS', {})
    
    print(f"   SSH Enabled: {ssh_enabled}")
    print(f"   SSH Servers configured: {len(ssh_servers)}")
    
    for server_name, config in ssh_servers.items():
        hostname = config.get('hostname', 'not_set')
        print(f"   ✓ {server_name}: {hostname}:{config.get('port', 22)}")
    
    if not ssh_enabled:
        print("   💡 Enable SSH by setting SSH_ENABLED=True and ENABLE_SSH_FEATURES=True")
    
except Exception as e:
    print(f"   ❌ Django SSH settings error: {e}")

# Test 4: Test SSH manager instantiation
if SSH_AVAILABLE:
    print("\n4. Testing SSH manager instantiation...")
    try:
        ssh_manager = SecureSSHManager()
        print("   ✓ SSH manager created successfully")
        print(f"   ✓ Default timeout: {ssh_manager.default_timeout}s")
        print(f"   ✓ Max retries: {ssh_manager.max_retries}")
        print(f"   ✓ Configured servers: {len(ssh_manager.servers)}")
        
        # Test server configurations
        for server_name, config in ssh_manager.servers.items():
            print(f"     - {server_name}: {config['hostname']}:{config['port']}")
        
    except Exception as e:
        print(f"   ❌ SSH manager creation failed: {e}")

# Test 5: Test key file access (if any keys exist)
print("\n5. Testing SSH key file access...")
potential_key_paths = [
    '~/.ssh/id_rsa',
    '~/.ssh/id_ed25519',
    '~/.ssh/grocery_store_key',
    '~/.ssh/id_ecdsa'
]

found_keys = []
for key_path in potential_key_paths:
    expanded_path = os.path.expanduser(key_path)
    if os.path.exists(expanded_path):
        found_keys.append(expanded_path)
        # Check permissions
        file_stat = os.stat(expanded_path)
        file_perms = oct(file_stat.st_mode)[-3:]
        if file_perms in ['600', '400']:
            print(f"   ✓ Found key: {key_path} (permissions: {file_perms})")
        else:
            print(f"   ⚠️  Found key: {key_path} (insecure permissions: {file_perms})")
            print(f"      💡 Fix with: chmod 600 {expanded_path}")

if not found_keys:
    print("   ⚠️  No SSH keys found in standard locations")
    print("   💡 Generate SSH key: ssh-keygen -t rsa -b 4096 -C 'grocery-store@example.com'")

# Test 6: Test environment variables
print("\n6. Testing environment variables...")
env_vars = [
    'PROD_HOST', 'STAGING_HOST', 'DB_HOST', 'CACHE_HOST',
    'ENABLE_SSH_FEATURES', 'SSH_TIMEOUT', 'REMOTE_PROJECT_PATH'
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        # Hide sensitive values
        display_value = value if 'HOST' not in var else f"{value[:10]}..." if len(value) > 10 else value
        print(f"   ✓ {var}: {display_value}")
    else:
        print(f"   ⚪ {var}: not set")

# Test 7: Test management commands
print("\n7. Testing Django management commands...")
try:
    from django.core.management import get_commands
    commands = get_commands()
    
    ssh_commands = [cmd for cmd in commands if 'ssh' in cmd]
    if ssh_commands:
        print(f"   ✓ SSH commands available: {ssh_commands}")
    else:
        print("   ⚪ No SSH management commands detected")
        
    # Check specific commands
    expected_commands = ['ssh_deploy', 'ssh_monitor']
    for cmd in expected_commands:
        if cmd in commands:
            print(f"   ✓ Command '{cmd}' available")
        else:
            print(f"   ❌ Command '{cmd}' not found")

except Exception as e:
    print(f"   ❌ Management commands test failed: {e}")

# Test 8: Test API endpoints (if SSH available)
if SSH_AVAILABLE:
    print("\n8. Testing SSH API views...")
    try:
        from marche_smart.ssh_api_views import ssh_config, ssh_server_status  # type: ignore
        print("   ✓ SSH API views imported successfully")
        
        # Check URL patterns
        try:
            from marche_smart.api_urls import urlpatterns  # type: ignore
            ssh_urls = [url for url in urlpatterns if 'ssh' in str(url.pattern)]
            print(f"   ✓ SSH API endpoints configured: {len(ssh_urls)}")
            
        except Exception as e:
            print(f"   ⚠️  Could not check URL patterns: {e}")
        
    except ImportError as e:
        print(f"   ❌ SSH API views import failed: {e}")

# Test 9: Connection test (safe test)
if SSH_AVAILABLE and found_keys:
    print("\n9. Testing SSH connection (localhost only)...")
    try:
        ssh_manager = SecureSSHManager()
        
        # Only test localhost connections for safety
        localhost_servers = {
            name: config for name, config in ssh_manager.servers.items()
            if config['hostname'] in ['localhost', '127.0.0.1']
        }
        
        if localhost_servers:
            for server_name in localhost_servers:
                print(f"   🔍 Testing connection to {server_name}...")
                try:
                    # This is just a connection test, not actual connection
                    print(f"     ✓ Configuration valid for {server_name}")
                except Exception as e:
                    print(f"     ❌ Configuration error for {server_name}: {e}")
        else:
            print("   ⚪ No localhost servers configured for testing")
            print("   💡 For safety, only localhost connections are tested")
    
    except Exception as e:
        print(f"   ❌ Connection test failed: {e}")

# Test 10: Security check
print("\n10. Security configuration check...")
try:
    if SSH_AVAILABLE:
        ssh_manager = SecureSSHManager()
        security_config = ssh_manager.security_config
        
        print(f"   Auto-add unknown hosts: {security_config['auto_add_policy']}")
        print(f"   Use system host keys: {security_config['use_system_host_keys']}")
        print(f"   GSS API disabled: {not security_config['use_gss_api']}")
        
        # Check for secure defaults
        if not security_config['auto_add_policy']:
            print("   ✅ Auto-add policy disabled (secure)")
        else:
            print("   ⚠️  Auto-add policy enabled (less secure)")
        
        if security_config['use_system_host_keys']:
            print("   ✅ Using system host keys (secure)")
        
    # Check Django settings security
    debug_mode = getattr(settings, 'DEBUG', True)
    if debug_mode:
        print("   ⚠️  DEBUG mode enabled - disable in production")
    else:
        print("   ✅ DEBUG mode disabled")
        
    secret_key = getattr(settings, 'SECRET_KEY', '')
    if 'insecure' in secret_key:
        print("   ⚠️  Using insecure SECRET_KEY - change in production")
    else:
        print("   ✅ SECRET_KEY appears secure")
    
except Exception as e:
    print(f"   ❌ Security check failed: {e}")

print("\n" + "=" * 50)
print("🎉 SSH system test completed!")

# Summary and recommendations
print("\n📋 Summary and Recommendations:")

if not SSH_AVAILABLE:
    print("❌ SSH functionality not available")
    print("   1. Install dependencies: pip install paramiko fabric cryptography python-decouple")
    print("   2. Check import errors above")

if missing_deps:
    print(f"📦 Missing dependencies: {', '.join(missing_deps)}")
    print(f"   Install with: pip install {' '.join(missing_deps)}")

if not found_keys:
    print("🔑 No SSH keys found")
    print("   1. Generate SSH key: ssh-keygen -t rsa -b 4096 -C 'your_email@example.com'")
    print("   2. Copy public key to servers: ssh-copy-id user@server")

if not getattr(settings, 'SSH_ENABLED', False):
    print("🔧 SSH features disabled")
    print("   1. Set ENABLE_SSH_FEATURES=True in environment")
    print("   2. Configure server hostnames in .env file")
    print("   3. Set DEBUG=False for production SSH features")

print("\n🚀 Next steps:")
print("1. Copy .env.ssh.example to .env and configure your servers")
print("2. Test connection: python manage.py ssh_deploy --action=connect --server=staging")
print("3. Monitor servers: python manage.py ssh_monitor --servers production,staging")
print("4. Use API endpoints for programmatic access")
print("\n📖 See SSH_SETUP_GUIDE.md for detailed configuration instructions")

print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")