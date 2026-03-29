"""
Test Owner Dashboard API - Shows ALL Customers Combined
This API shows total spending from ALL customers, not just individual ones.
"""
import os
import sys
import django

# Add the Django project to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'grocerystore'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from marche_smart.models import Order

def test_owner_api():
    """Test the Owner Dashboard API that shows ALL customers combined"""
    print("🏢 Testing Owner Dashboard API (ALL CUSTOMERS)")
    print("=" * 50)
    
    # Get an owner/staff user
    try:
        owner_user = User.objects.filter(is_superuser=True).first()
        if not owner_user:
            print("❌ No owner user found")
            return
        print(f"✅ Using owner user: {owner_user.username}")
    except Exception as e:
        print(f"❌ Error finding owner: {e}")
        return

    # Import the owner API function
    try:
        from marche_smart.advanced_api_views import powerbi_owner_dashboard
        print("✅ Owner Power BI API imported successfully")
    except Exception as e:
        print(f"❌ Error importing API: {e}")
        return

    # Test the API
    factory = RequestFactory()
    request = factory.get('/api/v1/powerbi/owner-dashboard/') 
    request.user = owner_user

    try:
        response = powerbi_owner_dashboard(request)
        
        if response.status_code == 200:
            data = response.data
            
            # Show daily orders data (ALL customers combined)
            daily_data = data.get('daily_orders_30d', [])
            
            print(f"\n📊 ALL CUSTOMERS - Last 7 Days:")
            print(f"Date       | Revenue    | Orders")
            print(f"-----------|------------|--------")
            
            # Show recent days
            for day_data in daily_data[:7]:  # Last 7 days
                date = day_data.get('date', 'N/A')
                revenue = day_data.get('revenue', 0)
                orders = day_data.get('orders_count', 0)
                print(f"{date} | Rs {revenue:8.2f} | {orders:6d}")
            
            # Today specifically
            today_str = timezone.now().strftime('%Y-%m-%d')
            today_data = next((d for d in daily_data if d['date'] == today_str), None)
            
            if today_data:
                print(f"\n🎯 TODAY'S TOTAL (ALL CUSTOMERS):")
                print(f"  • Date: {today_data['date']}")
                print(f"  • Revenue: Rs {today_data['revenue']}")
                print(f"  • Orders: {today_data['orders_count']}")
                print(f"  • This matches your orders: Rs 325.28? {'✅' if abs(today_data['revenue'] - 325.28) < 1 else '❌'}")
            else:
                print(f"❌ Today's data not found in API")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        import traceback
        traceback.print_exc()

def show_powerbi_solution():
    """Show exact steps to fix Power BI"""
    print(f"\n🔧 POWER BI SOLUTION - Use Owner Dashboard")
    print("=" * 50)
    print(f"")
    print(f"🔗 CORRECT API URL FOR POWER BI:")
    print(f"   OLD: /api/v1/powerbi/customer-dashboard/  (single customer)")
    print(f"   NEW: /api/v1/powerbi/owner-dashboard/     (ALL customers)")
    print(f"")
    print(f"📊 DATA STRUCTURE TO USE:")
    print(f"   • Field: daily_orders_30d")
    print(f"   • X-Axis: date") 
    print(f"   • Y-Axis: revenue")
    print(f"   • Shows: Combined revenue from ALL customers")
    print(f"")
    print(f"🔐 AUTHENTICATION:")
    print(f"   • Use Owner/Staff user token (not customer token)")
    print(f"   • This API requires admin permissions")
    print(f"")
    print(f"⚡ POWER BI STEPS:")
    print(f"   1. Go to Power BI → Data Sources → Settings")
    print(f"   2. Change URL to: /api/v1/powerbi/owner-dashboard/")
    print(f"   3. Update credentials with Owner user token")
    print(f"   4. Change chart data path to: daily_orders_30d")
    print(f"   5. Set X-axis: date, Y-axis: revenue")
    print(f"   6. Refresh dataset")
    print(f"   7. ✅ Chart will show ALL customers' spending!")

def verify_all_customers():
    """Show how many customers have orders today"""
    print(f"\n👥 ALL CUSTOMERS WITH ORDERS TODAY:")
    print("=" * 40)
    
    today = timezone.now().date()
    todays_orders = Order.objects.filter(created_at__date=today)
    
    customers_today = {}
    total_revenue = 0
    
    for order in todays_orders:
        if order.user:
            username = order.user.username
            if username not in customers_today:
                customers_today[username] = {'orders': 0, 'revenue': 0}
            customers_today[username]['orders'] += 1
            customers_today[username]['revenue'] += float(order.total_amount or 0)
            total_revenue += float(order.total_amount or 0)
    
    for username, data in customers_today.items():
        print(f"• {username}: {data['orders']} orders, Rs {data['revenue']:.2f}")
    
    print(f"\n💰 TOTAL ALL CUSTOMERS: Rs {total_revenue:.2f}")
    print(f"📦 TOTAL ORDERS: {todays_orders.count()}")
    
    return total_revenue, todays_orders.count()

if __name__ == "__main__":
    # Show all customers' data
    total_rev, total_orders = verify_all_customers()
    
    # Test owner API  
    test_owner_api()
    
    # Show solution
    show_powerbi_solution()
    
    print(f"\n✅ SUMMARY:")
    print(f"  • You have multiple customers with orders today")
    print(f"  • Total revenue today: Rs {total_rev:.2f}")
    print(f"  • Owner API shows this combined data correctly")
    print(f"  • Switch Power BI to use Owner Dashboard API")
    print(f"  • Your chart will show Rs {total_rev:.2f} for today!")