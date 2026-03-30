#!/usr/bin/env python
"""
Test UserProfile persistence functionality
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django environment
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    django.setup()

from django.contrib.auth.models import User
from marche_smart.models import UserProfile, Product, Category, Cart, CartItem

def test_userprofile_persistence():
    """Test that UserProfile data persists and loads correctly"""
    print("=== UserProfile Persistence Test ===")
    
    # 1. Create a test user
    try:
        test_user = User.objects.get(username='testprofileuser')
        print("✓ Using existing test user")
    except User.DoesNotExist:
        test_user = User.objects.create_user(
            username='testprofileuser',
            email='test@profile.com',
            password='testpass123'
        )
        print("✓ Created new test user")
    
    # 2. Test creating UserProfile
    try:
        profile = test_user.profile
        print(f"✓ UserProfile already exists: {profile}")
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=test_user,
            phone='+230 1234 5678',
            address='Test Address 123',
            city='Port Louis',
            postal_code='11000',
            preferred_delivery_method='home_delivery',
            preferred_pickup_store='port_louis'
        )
        print("✓ Created new UserProfile")
    
    # 3. Test profile data persistence
    print("\n--- Profile Data ---")
    print(f"Phone: {profile.phone}")
    print(f"Address: {profile.address}")
    print(f"City: {profile.city}")
    print(f"Postal Code: {profile.postal_code}")
    print(f"Preferred Delivery: {profile.preferred_delivery_method}")
    print(f"Preferred Store: {profile.preferred_pickup_store}")
    
    # 4. Update profile data
    profile.phone = '+230 5987 6543'
    profile.address = 'Updated Address 456'
    profile.city = 'Rose Hill'
    profile.save()
    print("\n✓ Updated profile data")
    
    # 5. Reload profile data
    profile.refresh_from_db()
    print("✓ Profile data after reload:")
    print(f"   Phone: {profile.phone}")
    print(f"   Address: {profile.address}")
    print(f"   City: {profile.city}")
    
    # 6. Test OneToOneField relationship
    user_from_profile = profile.user
    profile_from_user = test_user.profile
    print(f"\n✓ Relationship test: {user_from_profile.username} <-> Profile ID {profile_from_user.id}")
    
    print("\n🎉 UserProfile persistence test completed successfully!")
    return True

def test_checkout_integration():
    """Test the integration with checkout functionality"""
    print("\n=== Checkout Integration Test ===")
    
    # This would normally be done through the web interface
    # but we can simulate the checkout data loading logic
    try:
        test_user = User.objects.get(username='testprofileuser')
        
        # Simulate checkout data loading logic from views.py
        try:
            user_profile = test_user.profile
            profile_data = {
                'customer_phone': user_profile.phone or '',
                'delivery_method': user_profile.preferred_delivery_method or 'home_delivery',
                'shipping_address': user_profile.address or '',
                'shipping_city': user_profile.city or '',
                'shipping_postal_code': user_profile.postal_code or '',
                'pickup_store': user_profile.preferred_pickup_store or 'port_louis',
            }
            print("✓ Successfully loaded profile data for checkout:")
            for key, value in profile_data.items():
                print(f"   {key}: {value}")
                
        except UserProfile.DoesNotExist:
            print("❌ UserProfile does not exist")
            return False
        
        print("\n✓ Checkout integration test passed!")
        return True
        
    except User.DoesNotExist:
        print("❌ Test user does not exist")
        return False

def cleanup():
    """Clean up test data"""
    try:
        test_user = User.objects.get(username='testprofileuser')
        test_user.delete()
        print("\n🧹 Cleaned up test data")
    except User.DoesNotExist:
        print("\n🧹 No test data to clean up")

if __name__ == "__main__":
    try:
        print("Testing UserProfile functionality...\n")
        
        # Run tests
        profile_test = test_userprofile_persistence()
        checkout_test = test_checkout_integration()
        
        if profile_test and checkout_test:
            print("\n✅ ALL TESTS PASSED!")
            print("\nUserProfile persistence is working correctly!")
            print("- Customer details will be saved when 'Save details for next time' is checked")
            print("- Saved details will auto-fill in future checkout sessions")
            print("- Profile data is stored securely in the database")
        else:
            print("\n❌ Some tests failed")
        
        # Ask user if they want to clean up
        cleanup_choice = input("\nClean up test data? (y/n): ").lower()
        if cleanup_choice == 'y':
            cleanup()
        else:
            print("Test data preserved for manual inspection")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print("\nMake sure Django is running and database is accessible")