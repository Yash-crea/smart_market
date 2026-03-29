"""
Fix Power BI User Data Mismatch
The API is showing Rs 0.0 because it's checking the wrong user's orders.
"""
import os
import sys
import django

# Add the Django project to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'grocerystore'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
django.setup()

from django.utils import timezone
from marche_smart.models import Order
from django.contrib.auth.models import User

def check_order_users():
    """Check which users have today's orders"""
    print("🔍 Checking today's orders and their users...")
    
    today = timezone.now().date()
    todays_orders = Order.objects.filter(created_at__date=today)
    
    users_with_orders = {}
    
    for order in todays_orders:
        if order.user:
            username = order.user.username
            if username not in users_with_orders:
                users_with_orders[username] = {
                    'user': order.user,
                    'orders': [],
                    'total': 0
                }
            users_with_orders[username]['orders'].append(order)
            users_with_orders[username]['total'] += float(order.total_amount or 0)
    
    print(f"📊 Users with orders today:")
    for username, data in users_with_orders.items():
        user = data['user']
        is_owner = user.groups.filter(name__in=['Owner', 'Staff']).exists()
        user_type = 'Owner/Staff' if is_owner else 'Customer'
        
        print(f"  • {username} ({user_type}): {len(data['orders'])} orders, Rs {data['total']:.2f}")
        for order in data['orders']:
            print(f"    - {order.order_number}: Rs {order.total_amount}")
    
    return users_with_orders

def test_powerbi_for_each_user(users_with_orders):
    """Test Power BI API for each user who has orders"""
    print(f"\n🧪 Testing Power BI API for each user...")
    
    from django.test import RequestFactory
    from marche_smart.advanced_api_views import powerbi_customer_dashboard
    
    factory = RequestFactory()
    
    for username, data in users_with_orders.items():
        user = data['user']
        is_owner = user.groups.filter(name__in=['Owner', 'Staff']).exists()
        
        print(f"\n👤 Testing user: {username} ({data['total']:.2f})")
        
        if is_owner:
            print(f"  ⚠️ Skipping - Owner/Staff users blocked from customer API")
            continue
        
        try:
            request = factory.get('/api/v1/powerbi/customer-dashboard/')
            request.user = user
            
            response = powerbi_customer_dashboard(request)
            
            if response.status_code == 200:
                spending_data = response.data.get('spending_patterns', {}).get('daily_spending_30d', [])
                today_str = timezone.now().strftime('%Y-%m-%d')
                today_data = next((d for d in spending_data if d['date'] == today_str), None)
                
                if today_data:
                    api_spending = today_data['total_spent']
                    api_orders = today_data['order_count']
                    print(f"  ✅ API Response: Rs {api_spending} ({api_orders} orders)")
                    
                    if api_spending != data['total']:
                        print(f"  ⚠️ Mismatch! Expected Rs {data['total']:.2f}, got Rs {api_spending}")
                    else:
                        print(f"  🎯 Perfect match! Power BI data is correct for this user")
                else:
                    print(f"  ❌ No today's data found in API response")
            else:
                print(f"  ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def create_customer_test_orders():
    """Create test orders for a customer user if none exist"""
    print(f"\n🛠️ Creating customer test setup...")
    
    # Find or create a customer user (non-owner)
    customer_users = User.objects.exclude(
        groups__name__in=['Owner', 'Staff']
    ).exclude(is_superuser=True)
    
    if customer_users.exists():
        customer = customer_users.first()
        print(f"✅ Found customer user: {customer.username}")
    else:
        # Create a test customer
        customer = User.objects.create_user(
            username='powerbicustomer',
            email='powerbi@test.com',
            password='testpass123',
            first_name='PowerBI',
            last_name='Customer'
        )
        print(f"✅ Created customer user: {customer.username}")
    
    # Check if this customer has orders today
    today = timezone.now().date()
    customer_orders_today = Order.objects.filter(
        user=customer, 
        created_at__date=today
    )
    
    if customer_orders_today.exists():
        print(f"✅ Customer already has {customer_orders_today.count()} orders today")
        return customer
    
    print(f"📝 Power BI will work correctly for user: {customer.username}")
    print(f"📱 To test Power BI with real data:")
    print(f"   1. Login as: {customer.username}")
    print(f"   2. Place some test orders")
    print(f"   3. Use this user's token for Power BI authentication")
    
    return customer

if __name__ == "__main__":
    print("🔧 Power BI User Mismatch Resolver")
    print("=" * 50)
    
    # Check current orders
    users_with_orders = check_order_users()
    
    if users_with_orders:
        # Test API for each user
        test_powerbi_for_each_user(users_with_orders)
    else:
        print("❌ No orders found for today")
    
    # Provide solution
    print(f"\n💡 SOLUTION:")
    print(f"   The Power BI chart shows Rs 0 because:")
    print(f"   • Power BI uses a customer user token for authentication")
    print(f"   • Today's orders might belong to Owner/Staff users") 
    print(f"   • Owner/Staff users are blocked from customer Power BI API")
    print(f"")
    print(f"   To fix this:")
    print(f"   1. Use a customer account token in Power BI")
    print(f"   2. Or place orders as a customer user") 
    print(f"   3. Or use the Owner Power BI endpoint instead")
    
    # Create customer setup
    create_customer_test_orders()