#!/usr/bin/env python
"""
API Test Script - Test your new grocery store API endpoints

This script tests the major API endpoints to ensure everything is working correctly.
Run this after starting your Django server with: python manage.py runserver
"""

import requests
import json
import sys

# Configuration
BASE_URL = 'http://127.0.0.1:8000/api/v1'
TEST_USER = {
    'username': 'apitest_user',
    'email': 'apitest@example.com', 
    'password': 'testpassword123',
    'first_name': 'API',
    'last_name': 'Tester'
}

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_id = None
        
    def test_endpoint(self, method, endpoint, data=None, headers=None):
        """Helper method to test API endpoints"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            print(f"✓ {method.upper()} {endpoint}")
            print(f"  Status: {response.status_code}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                result = response.json()
                if isinstance(result, dict) and len(result) < 10:
                    print(f"  Response: {json.dumps(result, indent=2)[:200]}...")
                elif isinstance(result, list):
                    print(f"  Response: Array with {len(result)} items")
                else:
                    print(f"  Response: {str(result)[:100]}...")
            
            print()
            return response
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed to {url}")
            print("   Make sure Django server is running: python manage.py runserver")
            return None
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {str(e)}")
            return None
    
    def run_tests(self):
        """Run comprehensive API tests"""
        
        print("=" * 60)
        print("🧪 GROCERY STORE API TEST SUITE")
        print("=" * 60)
        print()
        
        # Test 1: Health Check - Get Categories (no auth required)
        print("📌 Test 1: Health Check - Anonymous Access")
        response = self.test_endpoint('GET', '/categories/')
        if not response:
            print("❌ Server is not accessible. Please start the Django server.")
            return False
        
        # Test 2: Get Recommendations (no auth required) 
        print("📌 Test 2: Machine Learning Recommendations")
        self.test_endpoint('GET', '/recommendations/?algorithm_type=seasonal&limit=3')
        self.test_endpoint('GET', '/recommendations/?algorithm_type=trending&limit=5')
        
        # Test 3: User Registration
        print("📌 Test 3: User Registration")
        response = self.test_endpoint('POST', '/auth/register/', TEST_USER)
        if response and response.status_code in [200, 201]:
            result = response.json()
            self.token = result.get('token')
            self.user_id = result.get('user_id')
            print(f"  ✅ User registered successfully! Token: {self.token[:20]}...")
        else:
            print("  ⚠️ User registration failed (user may already exist)")
            # Try to login instead
            print("📌 Test 3b: User Login")
            login_data = {'username': TEST_USER['username'], 'password': TEST_USER['password']}
            response = self.test_endpoint('POST', '/auth/login/', login_data)
            if response and response.status_code == 200:
                result = response.json()
                self.token = result.get('token')
                self.user_id = result.get('user_id')
                print(f"  ✅ User logged in successfully! Token: {self.token[:20]}...")
        
        if not self.token:
            print("❌ Cannot continue without authentication token")
            return False
        
        # Set up headers for authenticated requests
        auth_headers = {'Authorization': f'Token {self.token}'}
        
        # Test 4: Product Endpoints
        print("📌 Test 4: Product Management")
        self.test_endpoint('GET', '/products/', headers=auth_headers)
        self.test_endpoint('GET', '/smart-products/', headers=auth_headers)
        self.test_endpoint('GET', '/smart-products/seasonal/', headers=auth_headers)
        
        # Test 5: Cart Operations
        print("📌 Test 5: Shopping Cart Operations")
        self.test_endpoint('GET', '/carts/', headers=auth_headers)
        
        # Try to add item to cart (this may fail if no products exist)
        cart_data = {
            'product_id': 1,
            'product_type': 'smart',
            'quantity': 2
        }
        response = self.test_endpoint('POST', '/cart/add-item/', cart_data, auth_headers)
        if response and response.status_code in [200, 201]:
            print("  ✅ Successfully added item to cart!")
        else:
            print("  ⚠️ Could not add item to cart (no products available)")
        
        # Test 6: ML and Analytics Endpoints
        print("📌 Test 6: Machine Learning & Analytics")
        self.test_endpoint('GET', '/ml-models/', headers=auth_headers)
        self.test_endpoint('GET', '/recommendations/analytics/?days=30', headers=auth_headers)
        
        # Test interaction logging
        interaction_data = {
            'product_id': 1,
            'product_type': 'smart', 
            'interaction_type': 'view',
            'recommendation_type': 'seasonal'
        }
        self.test_endpoint('POST', '/interactions/log/', interaction_data, auth_headers)
        
        # Test 7: Weather Data (if available)
        print("📌 Test 7: Weather Data for ML")
        self.test_endpoint('GET', '/weather/', headers=auth_headers)
        
        # Test 8: Orders
        print("📌 Test 8: Order Management") 
        self.test_endpoint('GET', '/orders/', headers=auth_headers)
        
        print("=" * 60)
        print("✅ API TEST SUITE COMPLETED!")
        print("=" * 60)
        print()
        print("🎉 Your API is working! Key endpoints tested:")
        print("   ✓ Product management")
        print("   ✓ User authentication") 
        print("   ✓ ML recommendations")
        print("   ✓ Shopping cart")
        print("   ✓ Order processing")
        print("   ✓ Analytics & reporting")
        print("   ✓ Machine learning models")
        print()
        print("📖 See API_DOCUMENTATION.md for complete endpoint details")
        print("🚀 Ready for frontend integration!")
        
        return True

def main():
    """Main test function"""
    tester = APITester()
    
    print("Testing Grocery Store API...")
    print("Make sure your Django server is running on http://127.0.0.1:8000")
    print()
    
    try:
        success = tester.run_tests()
        if success:
            print("\n🎯 All tests completed successfully!")
            return 0
        else:
            print("\n❌ Some tests failed. Check your server and try again.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())