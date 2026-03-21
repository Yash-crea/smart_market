from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
import os
import sys


class Command(BaseCommand):
    help = 'Setup the unified authentication system for the grocery store'

    def handle(self, *args, **options):
        self.stdout.write("="*80)
        self.stdout.write("🛒 SMART MARKET GROCERY STORE - UNIFIED AUTH SETUP")
        self.stdout.write("="*80)
        
        # Run the migration command
        self.stdout.write("\n📂 Step 1: Migrating old users to unified system...")
        
        try:
            from django.core.management import call_command
            call_command('migrate_old_users')
            self.stdout.write(self.style.SUCCESS("✅ User migration completed successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Migration failed: {e}"))
            return
        
        # Create additional admin user if needed
        self.stdout.write("\n👑 Step 2: Setting up admin access...")
        
        admin_email = "admin@smartmarket.com"
        admin_password = "admin123"
        
        if not User.objects.filter(username=admin_email).exists():
            admin_user = User.objects.create_superuser(
                username=admin_email,
                email=admin_email,
                password=admin_password,
                first_name="System",
                last_name="Administrator"
            )
            
            # Add to Owner group
            owner_group, _ = Group.objects.get_or_create(name='Owner')
            admin_user.groups.add(owner_group)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Admin user created: {admin_email}"))
        else:
            self.stdout.write("ℹ️  Admin user already exists")
        
        # Display usage instructions
        self.stdout.write("\n" + "="*80)
        self.stdout.write("🎯 SETUP COMPLETE - HOW TO TEST THE SYSTEM")
        self.stdout.write("="*80)
        
        self.stdout.write(f"""
🌐 Start the development server:
   python manage.py runserver

🔗 Access the unified login at:
   http://localhost:8000/login/
   http://localhost:8000/unified-login/

📱 TEST ACCOUNTS:

👤 CUSTOMERS (Access Customer Dashboard):
   • Email: customer@example.com | Password: customer123
   • Email: jane.smith@email.com | Password: password123
   • Email: mike@example.com | Password: mike2024

👔 OWNERS (Access Owner Dashboard):
   • Email: owner@smartmarket.com | Password: owner123
   • Email: manager@smartmarket.com | Password: manager456
   • Email: admin@smartmarket.com | Password: admin123 (Admin)

🎪 TESTING INSTRUCTIONS:
   1. Go to the login page
   2. Enter any of the above credentials
   3. The system will automatically detect user type
   4. Redirect to appropriate dashboard (Customer/Owner/Staff)
   5. Each dashboard shows personalized content

⚡ FEATURES:
   ✅ Unified login for all user types
   ✅ Automatic role detection and dashboard routing
   ✅ Enhanced user experience with welcome messages
   ✅ Personalized dashboard content
   ✅ Migrated old user credentials to new system

🔧 Need to add more users?
   Use the Django admin panel or run:
   python manage.py migrate_old_users --reset

""")
        
        self.stdout.write("="*80)