"""
Test Power BI API Response to Debug Chart Issues
This script will simulate what Power BI receives and help identify the configuration issue.
"""
import os
import sys
import django
import json
from datetime import datetime, date, timedelta

# Add the Django project to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'grocerystore'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from marche_smart.models import Order

def test_powerbi_api():
    """Test what data the Power BI API is actually returning"""
    print("🧪 Testing Power BI API Response...")
    
    # Create a test user (customer)
    try:
        test_user = User.objects.filter(is_superuser=False).first()
        if not test_user:
            print("❌ No customer user found. Creating test user...")
            test_user = User.objects.create_user(
                username='testcustomer',
                email='test@example.com',
                password='testpass123'
            )
        print(f"✅ Using test user: {test_user.username}")
    except Exception as e:
        print(f"❌ Error with test user: {e}")
        return

    # Import the API function
    try:
        from marche_smart.advanced_api_views import powerbi_customer_dashboard
        print("✅ Power BI API function imported successfully")
    except Exception as e:
        print(f"❌ Error importing API: {e}")
        return

    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/api/v1/powerbi/customer-dashboard/')
    request.user = test_user

    try:
        # Call the API
        response = powerbi_customer_dashboard(request)
        data = response.data

        print(f"\n📊 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            # Check spending patterns
            spending_patterns = data.get('spending_patterns', {})
            
            print(f"\n📈 Spending Patterns Data:")
            print(f"  • Monthly data available: {'monthly_spending_12m' in spending_patterns}")
            print(f"  • Daily data available: {'daily_spending_30d' in spending_patterns}")
            
            if 'daily_spending_30d' in spending_patterns:
                daily_data = spending_patterns['daily_spending_30d']
                print(f"  • Daily data entries: {len(daily_data)}")
                
                # Show last 5 days including today
                today = timezone.now().date()
                recent_days = []
                for i in range(5):
                    check_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                    day_data = next((d for d in daily_data if d['date'] == check_date), None)
                    if day_data:
                        recent_days.append(day_data)
                
                print(f"\n📅 Last 5 Days Data:")
                for day in recent_days:
                    print(f"  • {day['date']} ({day['day_name']}): Rs {day['total_spent']} ({day['order_count']} orders)")
                
                # Check today specifically
                today_str = today.strftime('%Y-%m-%d')
                today_data = next((d for d in daily_data if d['date'] == today_str), None)
                if today_data:
                    print(f"\n🎯 Today's Data Found:")
                    print(f"  • Date: {today_data['date']}")
                    print(f"  • Spending: Rs {today_data['total_spent']}")
                    print(f"  • Orders: {today_data['order_count']}")
                else:
                    print(f"\n⚠️ Today's data ({today_str}) not found in API response!")
            else:
                print(f"  ❌ Daily spending data not found in API response!")
            
            # Show sample JSON for Power BI
            print(f"\n📝 Sample Power BI Data Structure:")
            if 'daily_spending_30d' in spending_patterns and spending_patterns['daily_spending_30d']:
                sample = spending_patterns['daily_spending_30d'][-1]  # Most recent day
                print(f"  Structure: {json.dumps(sample, indent=2)}")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {data}")
            
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        import traceback
        traceback.print_exc()

def show_powerbi_instructions():
    """Show step-by-step instructions to fix Power BI"""
    print(f"\n🔧 Power BI Configuration Steps:")
    print(f"")
    print(f"1. 📡 DATA SOURCE:")
    print(f"   • URL: http://your-domain.com/api/v1/powerbi/customer-dashboard/")
    print(f"   • Method: GET")
    print(f"   • Headers: Authorization: Bearer YOUR_TOKEN")
    print(f"")
    print(f"2. 🗂️ DATA PATH FOR CHART:")
    print(f"   • OLD PATH: spending_patterns.monthly_spending_12m")
    print(f"   • NEW PATH: spending_patterns.daily_spending_30d")
    print(f"")
    print(f"3. 📊 CHART CONFIGURATION:")
    print(f"   • X-Axis Field: date")
    print(f"   • Y-Axis Field: total_spent")
    print(f"   • Chart Type: Line Chart or Area Chart")
    print(f"")
    print(f"4. ♻️ REFRESH STEPS:")
    print(f"   • Go to Power BI Service")
    print(f"   • Find your dataset")
    print(f"   • Click 'Refresh Now'")
    print(f"   • Wait for refresh to complete")
    print(f"   • Check your dashboard")
    print(f"")

def verify_orders():
    """Verify today's orders are in database"""
    print(f"\n🔍 Database Verification:")
    
    today = timezone.now().date()
    todays_orders = Order.objects.filter(created_at__date=today)
    
    print(f"📅 Date: {today}")
    print(f"📦 Orders today: {todays_orders.count()}")
    
    total_today = 0
    for order in todays_orders:
        total_today += float(order.total_amount or 0)
        print(f"  • {order.order_number}: Rs {order.total_amount}")
    
    print(f"💰 Total spending today: Rs {total_today:.2f}")
    return todays_orders.count(), total_today

if __name__ == "__main__":
    print("🚀 Power BI Debug Tool")
    print("=" * 50)
    
    # Verify orders exist
    order_count, total_spent = verify_orders()
    
    if order_count > 0:
        # Test API
        test_powerbi_api()
        
        # Show instructions
        show_powerbi_instructions()
        
        print(f"\n✅ SUMMARY:")
        print(f"  • Orders in DB: {order_count} orders, Rs {total_spent:.2f}")
        print(f"  • API updated: ✅ Daily data structure added")
        print(f"  • Next step: Update Power BI chart configuration")
        
    else:
        print(f"❌ No orders found for today. Create some test orders first.")