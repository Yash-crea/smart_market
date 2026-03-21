# 🔐 Unified Authentication System - Smart Market Grocery Store

This document explains the enhanced unified login system that merges old customer and owner credentials into a modern Django authentication system.

## 🎯 Overview

The new system provides:
- **Single login page** for all user types (Customers, Owners, Staff)
- **Automatic role detection** and dashboard redirection
- **Enhanced security** using Django's built-in authentication
- **Personalized dashboards** for each user type
- **Seamless migration** from old credential system

## 🚀 Quick Setup

1. **Run the setup command** to migrate old users and prepare the system:
   ```bash
   python manage.py setup_auth
   ```

2. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

3. **Access the login page**:
   - http://localhost:8000/login/
   - http://localhost:8000/unified-login/

## 👥 Test Accounts

### 📱 Customer Accounts (Customer Dashboard)
- **Email:** customer@example.com | **Password:** customer123
- **Email:** jane.smith@email.com | **Password:** password123  
- **Email:** mike@example.com | **Password:** mike2024

### 👔 Owner Accounts (Owner Dashboard)
- **Email:** owner@smartmarket.com | **Password:** owner123
- **Email:** manager@smartmarket.com | **Password:** manager456
- **Email:** admin@smartmarket.com | **Password:** admin123 (SuperAdmin)

## 🔄 How It Works

### 1. Unified Login Process
```python
# User enters email/username and password
# System authenticates against Django User model
# Checks user's group membership (Customer, Owner, Staff)
# Redirects to appropriate dashboard automatically
```

### 2. Dashboard Routing
- **Customers** → Customer Dashboard (personalized orders, cart, recommendations)
- **Owners** → Owner Dashboard (business metrics, inventory, sales)
- **Staff** → Staff Dashboard (order management, inventory alerts)

### 3. User Migration
Old Customer and Owner models with password fields have been migrated to Django's User model with Group-based roles:

```python
# Old System
Customer.objects.filter(email="customer@example.com", password="hashed_password")
Owner.objects.filter(email="owner@example.com", password="hashed_password")

# New System  
User.objects.filter(username="customer@example.com").groups.filter(name="Customer")
User.objects.filter(username="owner@example.com").groups.filter(name="Owner")
```

## 🛠 Management Commands

### `migrate_old_users`
Migrates old customer and owner credentials to Django User system:
```bash
python manage.py migrate_old_users
python manage.py migrate_old_users --reset  # Reset and recreate users
```

### `setup_auth`
Complete setup of unified authentication system:
```bash
python manage.py setup_auth
```

## 🎨 Enhanced Dashboard Features

### Customer Dashboard
- ✅ Personal order history
- ✅ Shopping cart status
- ✅ Product recommendations
- ✅ Customer loyalty information
- ✅ Account statistics

### Owner Dashboard  
- ✅ Business metrics and KPIs
- ✅ Inventory value and low-stock alerts
- ✅ Customer and user statistics
- ✅ Recent orders overview
- ✅ Top-selling products

### Staff Dashboard
- ✅ Order management
- ✅ Inventory alerts
- ✅ Customer service information
- ✅ Task-focused interface

## 🔒 Security Features

- **Password hashing** using Django's built-in security
- **Group-based access control** for different user types
- **Session management** with automatic logout
- **Input validation** and CSRF protection
- **User activity tracking** and audit trails

## 📝 File Structure

```
marche_smart/
├── management/commands/
│   ├── migrate_old_users.py    # Migrate old credentials
│   └── setup_auth.py           # Complete setup command
├── views.py                    # Enhanced login and dashboard views
├── urls.py                     # Updated URL routing
└── models.py                   # User models and groups
```

## 🎭 User Experience

### Login Flow
1. User visits `/login/` or `/unified-login/`
2. Enters email/username and password
3. System shows welcome message with user's name
4. Automatically redirects to appropriate dashboard
5. Dashboard displays personalized content

### Error Handling
- Clear error messages for invalid credentials
- Account deactivation notifications
- Graceful fallbacks for missing data
- User-friendly error pages

## 🔧 Extending the System

### Adding New User Types
1. Create new Group: `Group.objects.create(name='NewRole')`
2. Update login logic in `unified_login` function
3. Create new dashboard view and template
4. Add URL routing for new dashboard

### Customizing Dashboards
Each dashboard template can be customized in `templates/`:
- `customer_dashboard.html`
- `owner_dashboard.html`  
- `staff_dashboard.html`

## 📞 Support

For issues or questions about the unified authentication system:
1. Check Django logs for authentication errors
2. Verify user groups are assigned correctly
3. Ensure all migrations have been applied
4. Test with provided sample accounts first

---

**Last Updated:** February 2026  
**Version:** 1.0  
**Django Version:** 6.0+