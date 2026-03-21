# SSH Connection Guide for Grocery Store Deployment

## 🔐 **SECURE SSH IMPLEMENTATION INCLUDED**

✅ **YES - Your grocery store project now includes a comprehensive secure SSH connection system with:**

### **Security Features Implemented:**
- **🔒 RSA/Ed25519 Key Authentication Only** - No password authentication
- **🛡️ Host Key Verification** - Prevents MITM attacks  
- **⚡ Connection Timeouts & Retry Logic** - Prevents hanging connections
- **🔐 Encrypted SSH Tunnels** - For secure database/cache access
- **👤 Role-Based Access Control** - Staff/Superuser permission levels
- **📝 Audit Logging** - All SSH operations logged
- **🚫 Command Filtering** - Dangerous commands blocked
- **🔄 Automatic Cleanup** - Proper connection management

### **Files Added:**
- `marche_smart/ssh_manager.py` - Secure SSH connection manager
- `marche_smart/ssh_api_views.py` - REST API for SSH operations  
- `marche_smart/management/commands/ssh_deploy.py` - Deployment commands
- `marche_smart/management/commands/ssh_monitor.py` - Server monitoring
- `.env.ssh.example` - Configuration template
- `test_ssh_system.py` - Comprehensive testing script

### **API Endpoints Available:**
- `GET /api/v1/ssh/status/` - Server connection status
- `GET /api/v1/ssh/health/` - Comprehensive health checks
- `POST /api/v1/ssh/deploy/` - Secure deployment
- `POST /api/v1/ssh/execute/` - Command execution (superuser only)
- `GET /api/v1/ssh/config/` - Configuration information
- `POST /api/v1/ssh/tunnel/` - Create secure tunnels

## Overview
This guide covers SSH setup and configuration for deploying and managing your Django grocery store application on remote servers.

## SSH Key Setup

### 1. Generate SSH Keys (if you don't have them)

**Windows (PowerShell):**
```powershell
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Default location: C:\Users\YourUsername\.ssh\id_rsa
# Press Enter to accept default location
# Set a passphrase for security (recommended)
```

**Linux/macOS:**
```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Default location: ~/.ssh/id_rsa
# Press Enter to accept default location
# Set a passphrase for security (recommended)
```

### 2. Copy Public Key to Server

**Method 1: Using ssh-copy-id (Linux/macOS/WSL)**
```bash
ssh-copy-id user@your_server_ip
```

**Method 2: Manual Copy**
```bash
# Copy public key content
cat ~/.ssh/id_rsa.pub

# Then paste it into the server's ~/.ssh/authorized_keys file
ssh user@your_server_ip
echo "your_public_key_content" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

**Windows PowerShell:**
```powershell
# Copy public key content
Get-Content C:\Users\YourUsername\.ssh\id_rsa.pub

# Then manually add it to server's authorized_keys
```

## SSH Configuration

### 1. Create SSH Config File

**Windows:** `C:\Users\YourUsername\.ssh\config`
**Linux/macOS:** `~/.ssh/config`

```bash
# Grocery Store Production Server
Host grocery-prod
    HostName your_production_server_ip
    User ubuntu
    Port 22
    IdentityFile ~/.ssh/id_rsa
    ForwardAgent yes
    ServerAliveInterval 60

# Grocery Store Staging Server
Host grocery-staging
    HostName your_staging_server_ip
    User ubuntu
    Port 22
    IdentityFile ~/.ssh/id_rsa
    ForwardAgent yes
    ServerAliveInterval 60

# Database Server
Host grocery-db
    HostName your_database_server_ip
    User ubuntu
    Port 22
    IdentityFile ~/.ssh/id_rsa
    LocalForward 5432 localhost:5432  # PostgreSQL tunnel
    LocalForward 6379 localhost:6379  # Redis tunnel

# Redis Cache Server
Host grocery-cache
    HostName your_redis_server_ip
    User ubuntu
    Port 22
    IdentityFile ~/.ssh/id_rsa
    LocalForward 6379 localhost:6379
```

### 2. Set Proper Permissions
```bash
# Linux/macOS
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
chmod 700 ~/.ssh

# Windows (PowerShell as Administrator)
icacls C:\Users\YourUsername\.ssh\id_rsa /inheritance:r
icacls C:\Users\YourUsername\.ssh\id_rsa /grant:r %username%:F
```

## Common SSH Commands for Deployment

### 1. Connect to Servers
```bash
# Connect to production server
ssh grocery-prod

# Connect to staging server
ssh grocery-staging

# Connect with port forwarding for Redis
ssh -L 6379:localhost:6379 grocery-cache
```

### 2. File Transfer with SCP
```bash
# Upload Django project to server
scp -r /path/to/grocery_store grocery-prod:/home/ubuntu/

# Upload specific files
scp manage.py grocery-prod:/home/ubuntu/grocery_store/
scp requirements.txt grocery-prod:/home/ubuntu/grocery_store/

# Download log files
scp grocery-prod:/var/log/django/error.log ./logs/
```

### 3. File Transfer with rsync (Recommended)
```bash
# Sync entire project (excluding .git, __pycache__, etc.)
rsync -avz --exclude='.git' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.env' \
  /path/to/grocery_store/ grocery-prod:/home/ubuntu/grocery_store/

# Sync only changed files
rsync -avz --delete /path/to/grocery_store/ grocery-prod:/home/ubuntu/grocery_store/
```

## Server Configuration Scripts

### 1. Initial Server Setup Script

Save as `server_setup.sh` and run on remote server:

```bash
#!/bin/bash
# Initial Ubuntu server setup for Django grocery store

set -e

echo "🚀 Setting up Ubuntu server for Django Grocery Store..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv nginx postgresql redis-server
sudo apt install -y git curl wget htop nano

# Create application user
sudo useradd -m -s /bin/bash grocery
sudo usermod -aG sudo grocery

# Create directories
sudo mkdir -p /var/www/grocery_store
sudo mkdir -p /var/log/django
sudo chown -R grocery:grocery /var/www/grocery_store
sudo chown -R grocery:grocery /var/log/django

# Configure PostgreSQL
sudo -u postgres createdb grocery_store_db
sudo -u postgres createuser grocery --no-createdb --no-createrole --no-superuser
sudo -u postgres psql -c "ALTER USER grocery WITH PASSWORD 'secure_password_here';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE grocery_store_db TO grocery;"

# Configure Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Configure firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

echo "✅ Server setup completed!"
echo "Next steps:"
echo "1. Upload your Django project"
echo "2. Set up virtual environment"
echo "3. Configure Nginx"
echo "4. Set up SSL certificates"
```

### 2. Django Deployment Script

Save as `deploy.sh`:

```bash
#!/bin/bash
# Deploy Django grocery store application

set -e

PROJECT_DIR="/var/www/grocery_store"
VENV_DIR="$PROJECT_DIR/venv"

echo "🚀 Deploying Django Grocery Store..."

# Navigate to project directory
cd $PROJECT_DIR

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

# Activate virtual environment
source $VENV_DIR/bin/activate

# Install/update dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r cache_requirements.txt

# Database migrations
cd grocerystore
python manage.py collectstatic --noinput
python manage.py migrate

# Create superuser (if needed)
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'secure_admin_password')" | python manage.py shell

# Test the application
python manage.py check

# Restart services
sudo systemctl restart grocery_gunicorn
sudo systemctl restart nginx

echo "✅ Deployment completed!"
```

## SSH Security Best Practices

### 1. Server Security Configuration

Edit `/etc/ssh/sshd_config` on the server:

```bash
# Disable root login
PermitRootLogin no

# Use key-based authentication only
PasswordAuthentication no
PubkeyAuthentication yes

# Change default port (optional)
Port 2222

# Limit user access
AllowUsers ubuntu grocery

# Disable empty passwords
PermitEmptyPasswords no

# Set connection limits
MaxAuthTries 3
MaxSessions 2

# Use Protocol 2 only
Protocol 2
```

Restart SSH service after changes:
```bash
sudo systemctl restart ssh
```

### 2. SSH Connection with Custom Port
```bash
# Connect to server with custom port
ssh -p 2222 grocery-prod

# Update SSH config for custom port
Host grocery-prod
    HostName your_server_ip
    User ubuntu
    Port 2222
    IdentityFile ~/.ssh/id_rsa
```

### 3. SSH Tunneling for Secure Database Access
```bash
# Create SSH tunnel for PostgreSQL
ssh -L 5432:localhost:5432 grocery-prod

# Create SSH tunnel for Redis
ssh -L 6379:localhost:6379 grocery-prod

# Now you can connect to databases as if they're local
psql -h localhost -U grocery grocery_store_db
redis-cli -h localhost -p 6379
```

## Troubleshooting SSH Issues

### 1. Permission Denied
```bash
# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Verify SSH agent
ssh-add ~/.ssh/id_rsa
ssh-add -l  # List loaded keys
```

### 2. Connection Timeouts
```bash
# Add keep-alive settings to SSH config
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### 3. Key Not Accepted
```bash
# Debug SSH connection
ssh -v grocery-prod

# Check server authorized_keys
ssh grocery-prod "cat ~/.ssh/authorized_keys"
```

### 4. Port Already in Use (for tunneling)
```bash
# Kill process using port
sudo lsof -ti:6379 | xargs kill -9

# Use different local port
ssh -L 6380:localhost:6379 grocery-prod
```

## Automated Deployment with SSH

### 1. GitHub Actions Deployment

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /var/www/grocery_store
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          cd grocerystore
          python manage.py migrate
          python manage.py collectstatic --noinput
          sudo systemctl restart grocery_gunicorn
```

### 2. Simple Deployment Script

```bash
#!/bin/bash
# deploy_local.sh - Run from development machine

echo "🚀 Deploying to production..."

# Sync files
rsync -avz --exclude='.git' --exclude='__pycache__' \
  --exclude='*.pyc' --exclude='.env' --exclude='db.sqlite3' \
  ./ grocery-prod:/var/www/grocery_store/

# Run deployment commands on server
ssh grocery-prod << 'EOF'
  cd /var/www/grocery_store
  source venv/bin/activate
  pip install -r requirements.txt
  cd grocerystore
  python manage.py migrate
  python manage.py collectstatic --noinput
  sudo systemctl restart grocery_gunicorn
  sudo systemctl restart nginx
EOF

echo "✅ Deployment completed!"
```

## Monitoring and Maintenance

### 1. Server Health Check
```bash
# Check server status
ssh grocery-prod "
  echo 'System Status:'
  uptime
  df -h
  free -h
  systemctl status nginx
  systemctl status grocery_gunicorn
  systemctl status postgresql
  systemctl status redis-server
"
```

### 2. Log Monitoring
```bash
# Monitor Django logs
ssh grocery-prod "tail -f /var/log/django/error.log"

# Monitor Nginx logs
ssh grocery-prod "tail -f /var/log/nginx/access.log"

# Monitor system logs
ssh grocery-prod "journalctl -f -u grocery_gunicorn"
```

### 3. Database Backup
```bash
# Create database backup
ssh grocery-prod "
  pg_dump -U grocery -W grocery_store_db > /home/ubuntu/backups/db_backup_\$(date +%Y%m%d_%H%M%S).sql
"

# Download backup
scp grocery-prod:/home/ubuntu/backups/db_backup_*.sql ./backups/
```

This SSH setup will help you securely connect to and manage your Django grocery store application on remote servers.