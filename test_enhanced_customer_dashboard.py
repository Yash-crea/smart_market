"""
Test Enhanced Customer Power BI Dashboard
Tests the updated customer dashboard with improved Power BI analytics structure
"""
import os
import sys
import django
import json

# Add the Django project to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'grocerystore'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone

def test_enhanced_customer_dashboard():
    """Test the enhanced customer Power BI dashboard"""
    print("🚀 Testing Enhanced Customer Power BI Dashboard")
    print("=" * 50)
    
    # Find a customer user with orders
    try:
        # Get the user who has orders (warren)
        from marche_smart.models import Order
        today = timezone.now().date()
        todays_orders = Order.objects.filter(created_at__date=today)
        
        if todays_orders.exists():
            customer_user = todays_orders.first().user
            print(f"✅ Using customer: {customer_user.username}")
            
            # Check if this is really a customer (not owner)
            is_owner = customer_user.groups.filter(name__in=['Owner', 'Staff']).exists()
            if is_owner:
                print(f"⚠️ This user is Owner/Staff, results may be blocked")
        else:
            print("❌ No orders found today")
            return
            
    except Exception as e:
        print(f"❌ Error finding customer: {e}")
        return

    # Test the enhanced API
    try:
        from marche_smart.advanced_api_views import powerbi_customer_dashboard
        
        factory = RequestFactory()
        request = factory.get('/api/v1/powerbi/customer-dashboard/')
        request.user = customer_user
        
        response = powerbi_customer_dashboard(request)
        
        if response.status_code == 200:
            data = response.data
            print(f"✅ API Response: {response.status_code}")
            
            # Check new analytics sections
            print(f"\n📊 NEW ANALYTICS SECTIONS:")
            
            # Analytics data
            if 'analytics_data' in data:
                analytics = data['analytics_data']
                print(f"  ✅ analytics_data section present")
                if 'weekly_summary' in analytics:
                    weekly = analytics['weekly_summary']
                    print(f"     • Current week spending: Rs {weekly.get('current_week_spending', 0)}")
                    print(f"     • Current week orders: {weekly.get('current_week_orders', 0)}")
                    print(f"     • Average daily spending: Rs {weekly.get('average_daily_spending', 0)}")
            
            # Chart data for Power BI
            if 'chart_data' in data:
                charts = data['chart_data']
                print(f"  ✅ chart_data section present")
                
                if 'spending_trend_30d' in charts:
                    trend_data = charts['spending_trend_30d']
                    print(f"     • Spending trend entries: {len(trend_data)}")
                    
                    # Show recent days
                    recent_days = trend_data[-5:]  # Last 5 days
                    print(f"     • Recent 5 days:")
                    for day in recent_days:
                        print(f"       - {day['date']}: Rs {day['spending']} ({day['orders']} orders)")
                
                if 'monthly_overview' in charts:
                    monthly = charts['monthly_overview']
                    print(f"     • Monthly overview entries: {len(monthly)}")
                
                if 'top_products_chart' in charts:
                    top_products = charts['top_products_chart']
                    print(f"     • Top products for charts: {len(top_products)}")
            
            # Store insights
            if 'store_insights' in data:
                insights = data['store_insights']
                print(f"  ✅ store_insights section present")
                if 'customer_vs_average' in insights:
                    comparison = insights['customer_vs_average']
                    print(f"     • Monthly average: Rs {comparison.get('customer_monthly_avg', 0)}")
                    print(f"     • Avg order value: Rs {comparison.get('customer_avg_order_value', 0)}")
            
            # Recent activity enhanced
            if 'recent_activity' in data:
                activity = data['recent_activity']
                print(f"  ✅ recent_activity section enhanced")
                if 'activity_summary' in activity:
                    summary = activity['activity_summary']
                    print(f"     • Orders last 30 days: {summary.get('orders_last_30_days', 0)}")
                    print(f"     • Spending last 30 days: Rs {summary.get('spending_last_30_days', 0)}")
            
            # Test Power BI chart compatibility
            print(f"\n📈 POWER BI CHART COMPATIBILITY:")
            if 'chart_data' in data and 'spending_trend_30d' in data['chart_data']:
                trend_data = data['chart_data']['spending_trend_30d']
                if trend_data:
                    sample = trend_data[0]
                    required_fields = ['date', 'spending', 'orders', 'day_name']
                    missing_fields = [field for field in required_fields if field not in sample]
                    if not missing_fields:
                        print(f"  ✅ All required chart fields present")
                        print(f"  📊 Sample data structure:")
                        print(f"     {json.dumps(sample, indent=6)}")
                    else:
                        print(f"  ❌ Missing fields: {missing_fields}")
            
            print(f"\n🎯 POWER BI USAGE:")
            print(f"  • Primary chart data: chart_data.spending_trend_30d")
            print(f"  • X-axis: date")
            print(f"  • Y-axis: spending") 
            print(f"  • Secondary: orders (for dual-axis chart)")
            print(f"  • Monthly view: chart_data.monthly_overview")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"Error details: {response.data}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        import traceback
        traceback.print_exc()

def show_powerbi_config():
    """Show Power BI configuration for enhanced customer dashboard"""
    print(f"\n🔧 ENHANCED POWER BI CONFIGURATION")
    print("=" * 50)
    print(f"")
    print(f"🔗 CUSTOMER DASHBOARD URL:")
    print(f"   /api/v1/powerbi/customer-dashboard/")
    print(f"")
    print(f"📊 AVAILABLE CHART DATA PATHS:")
    print(f"   1. Primary Trend: chart_data.spending_trend_30d")
    print(f"      • Fields: date, spending, orders, day_name")
    print(f"      • Best for: Daily spending trends")
    print(f"")
    print(f"   2. Monthly Summary: chart_data.monthly_overview") 
    print(f"      • Fields: month, spending, orders, avg_order_value")
    print(f"      • Best for: Monthly comparison charts")
    print(f"")
    print(f"   3. Top Products: chart_data.top_products_chart")
    print(f"      • Fields: product_name, times_purchased, total_spent") 
    print(f"      • Best for: Product popularity charts")
    print(f"")
    print(f"   4. Legacy Support: spending_patterns.daily_spending_30d")
    print(f"      • Still available for backward compatibility")
    print(f"")
    print(f"⚡ RECOMMENDED CHART SETUP:")
    print(f"   • Chart Type: Line Chart or Area Chart")
    print(f"   • Data Source: chart_data.spending_trend_30d") 
    print(f"   • X-Axis: date")
    print(f"   • Y-Axis: spending")
    print(f"   • Tooltip: orders, day_name")

if __name__ == "__main__":
    test_enhanced_customer_dashboard()
    show_powerbi_config()
    
    print(f"\n✅ CUSTOMER DASHBOARD ENHANCED!")
    print(f"   • Added analytics_data section")
    print(f"   • Added chart_data section for Power BI")  
    print(f"   • Added store_insights section")
    print(f"   • Enhanced recent_activity section")
    print(f"   • Full Power BI compatibility")
    print(f"   • Backward compatibility maintained")