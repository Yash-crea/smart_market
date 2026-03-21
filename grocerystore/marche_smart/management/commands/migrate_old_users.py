from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from django.db import transaction


class Command(BaseCommand):
    help = 'Migrate old Customer, Owner, and Admin credentials to Django User system'

    def handle(self, *args, **options):
        self.stdout.write("Starting migration of old users to unified authentication system...")
        
        # Create groups if they don't exist
        customer_group, created = Group.objects.get_or_create(name='Customer')
        owner_group, created = Group.objects.get_or_create(name='Owner')
        staff_group, created = Group.objects.get_or_create(name='Staff')
        
        if created:
            self.stdout.write("Created user groups")
        
        # Your actual users (as requested)
        old_customers = [
            {'name': 'yash', 'email': 'yash@smartmarket.com', 'password': 'Customer@2026!Shop'},
            {'name': 'raguvir', 'email': 'raguvir@smartmarket.com', 'password': 'Raguvir#2026!Shop'},
        ]
        
        old_owners = [
            {'name': 'Nazeer', 'email': 'nazeer@smartmarket.com', 'password': 'Owner@2026!Shop'},
        ]
        
        migrated_count = 0
        
        with transaction.atomic():
            # === INTEGRATE ORPHANED ADMIN USERS FROM ADMIN PANEL ===
            self.stdout.write("\n🔧 Integrating existing admin panel users...")
            orphaned_admin_users = User.objects.filter(groups=None, is_staff=True)
            
            for admin_user in orphaned_admin_users:
                # Assign admin users to Owner group since they have admin privileges
                admin_user.groups.add(owner_group)
                migrated_count += 1
                
                self.stdout.write(f"✅ Integrated admin user: {admin_user.username} ({admin_user.email}) → Owner Group")
                self.stdout.write(f"   - Staff: {admin_user.is_staff}")
                self.stdout.write(f"   - Superuser: {admin_user.is_superuser}")
                self.stdout.write(f"   - Can now access Owner Dashboard via unified login\n")
            
            # === MIGRATE PREDEFINED USERS ===
            self.stdout.write("\n👥 Migrating predefined customer accounts...")
            
            # Migrate old customers
            for customer_data in old_customers:
                email = customer_data['email']
                
                # Check if user already exists
                if not User.objects.filter(username=email).exists():
                    user = User.objects.create(
                        username=email,
                        email=email,
                        first_name=customer_data['name'].split()[0],
                        last_name=' '.join(customer_data['name'].split()[1:]) if len(customer_data['name'].split()) > 1 else '',
                        password=make_password(customer_data['password']),
                        is_active=True
                    )
                    user.groups.add(customer_group)
                    migrated_count += 1
                    self.stdout.write(f"✅ Migrated customer: {customer_data['name']} ({email})")
                else:
                    # Update existing user's group if not assigned
                    existing_user = User.objects.get(username=email)
                    if not existing_user.groups.exists():
                        existing_user.groups.add(customer_group)
                        self.stdout.write(f"✅ Updated existing customer with group: {email}")
                    else:
                        self.stdout.write(f"⚠️  Customer already exists: {email}")
            
            self.stdout.write("\n👔 Migrating predefined owner accounts...")
            
            # Migrate old owners
            for owner_data in old_owners:
                email = owner_data['email']
                
                # Check if user already exists
                if not User.objects.filter(username=email).exists():
                    user = User.objects.create(
                        username=email,
                        email=email,
                        first_name=owner_data['name'].split()[0],
                        last_name=' '.join(owner_data['name'].split()[1:]) if len(owner_data['name'].split()) > 1 else '',
                        password=make_password(owner_data['password']),
                        is_active=True,
                        is_staff=True  # Owners get staff privileges
                    )
                    user.groups.add(owner_group)
                    migrated_count += 1
                    self.stdout.write(f"✅ Migrated owner: {owner_data['name']} ({email})")
                else:
                    # Update existing user's group if not assigned
                    existing_user = User.objects.get(username=email)
                    if not existing_user.groups.exists():
                        existing_user.groups.add(owner_group)
                        existing_user.is_staff = True
                        existing_user.save()
                        self.stdout.write(f"✅ Updated existing owner with group: {email}")
                    else:
                        self.stdout.write(f"⚠️  Owner already exists: {email}")
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully migrated {migrated_count} users to the unified authentication system!')
        )
        
        # Display comprehensive user status
        self.stdout.write("\n" + "="*80)
        self.stdout.write("🎯 UNIFIED LOGIN SYSTEM - CURRENT USER STATUS")
        self.stdout.write("="*80)
        
        # Show all integrated users
        all_users = User.objects.all().order_by('is_superuser', 'is_staff', 'groups__name')
        
        self.stdout.write("\n👥 ALL SYSTEM USERS:")
        for user in all_users:
            groups = [g.name for g in user.groups.all()]
            group_text = ', '.join(groups) if groups else "No Group"
            status_icons = []
            if user.is_superuser:
                status_icons.append("🔑")
            if user.is_staff:
                status_icons.append("👔")
            
            self.stdout.write(f"   {''.join(status_icons)} {user.username} | {user.email}")
            self.stdout.write(f"      Groups: {group_text}")
            self.stdout.write(f"      Dashboard Access: {self._get_dashboard_access(user)}\n")
        
        # Display login credentials for testing
        self.stdout.write("="*80)
        self.stdout.write("🔐 LOGIN CREDENTIALS FOR TESTING")
        self.stdout.write("="*80)
        
        # Admin/Owner logins (from admin panel)
        admin_users = User.objects.filter(is_superuser=True, groups__name='Owner')
        if admin_users.exists():
            self.stdout.write("\n🔑 ADMIN PANEL USERS (now integrated):")
            for admin in admin_users:
                self.stdout.write(f"   Email/Username: {admin.username}")
                self.stdout.write(f"   Use existing admin password")
                self.stdout.write(f"   Access: Owner Dashboard + Admin Panel")
                self.stdout.write(f"   Login URL: /login/ (unified system)\n")
        
        self.stdout.write("📱 PREDEFINED CUSTOMER LOGINS:")
        for customer in old_customers:
            self.stdout.write(f"   Email: {customer['email']}")
            self.stdout.write(f"   Password: {customer['password']}")
            self.stdout.write(f"   Dashboard: Customer Dashboard\n")
        
        self.stdout.write("👔 PREDEFINED OWNER LOGINS:")
        for owner in old_owners:
            self.stdout.write(f"   Email: {owner['email']}")
            self.stdout.write(f"   Password: {owner['password']}")
            self.stdout.write(f"   Dashboard: Owner Dashboard\n")
        
        self.stdout.write("="*80)
        self.stdout.write("📋 NEXT STEPS:")
        self.stdout.write("1. All users can now log in via /login/ (unified system)")
        self.stdout.write("2. Users are automatically redirected to their appropriate dashboard")
        self.stdout.write("3. Admin users retain admin panel access + get Owner dashboard")
        self.stdout.write("4. Test the login system with any of the above credentials")
        self.stdout.write("="*80)

    def _get_dashboard_access(self, user):
        """Determine which dashboard a user can access"""
        groups = [g.name for g in user.groups.all()]
        access = []
        
        if 'Owner' in groups:
            access.append("Owner Dashboard")
        if 'Staff' in groups:
            access.append("Staff Dashboard") 
        if 'Customer' in groups:
            access.append("Customer Dashboard")
        if user.is_superuser:
            access.append("Admin Panel")
            
        return ' + '.join(access) if access else "Basic Access Only"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset and recreate all migrated users (WARNING: This will delete existing users!)',
        )