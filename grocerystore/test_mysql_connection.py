#!/usr/bin/env python3
"""
Script to test MySQL database connection and generate Django models
from existing smart_market database tables.
"""
import os
import sys
import django
from django.conf import settings

# Add the Django project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
django.setup()

def test_connection():
    """Test MySQL database connection"""
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE();")
            result = cursor.fetchone()
            print(f"✅ Successfully connected to database: {result[0]}")
            
            # Show all tables in the database
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print(f"\n📋 Found {len(tables)} tables in smart_market database:")
            for table in tables:
                print(f"  - {table[0]}")
                
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def generate_models():
    """Generate Django models from existing database tables"""
    from django.core.management import execute_from_command_line
    
    print("\n🔄 Generating Django models from existing database...")
    try:
        # Generate models and save to file
        execute_from_command_line(['manage.py', 'inspectdb'])
        return True
    except Exception as e:
        print(f"❌ Failed to generate models: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing MySQL Connection to smart_market database...")
    print("=" * 50)
    
    if test_connection():
        print("\n" + "=" * 50)
        generate_models()
    else:
        print("\n📝 To fix connection issues:")
        print("1. Update USERNAME in settings.py")
        print("2. Update PASSWORD in settings.py") 
        print("3. Ensure MySQL server is running")
        print("4. Verify 'smart_market' database exists")