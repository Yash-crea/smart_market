#!/usr/bin/env python
"""
Test script to verify Customer Dashboard date range functionality
"""
import requests
import json
from datetime import date, datetime, timedelta

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
CUSTOMER_DASHBOARD_URL = f"{BASE_URL}/api/v1/powerbi/customer-dashboard/"

def test_customer_date_range():
    print("🗓️  Testing Customer Dashboard Date Range...")
    print("=" * 55)
    
    # Expected today's date
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    
    print(f"📅 Expected Date Range Context:")
    print(f"   Yesterday: {yesterday.strftime('%B %d, %Y')}")
    print(f"   Today: {today.strftime('%B %d, %Y')}")
    print(f"   Tomorrow: {tomorrow.strftime('%B %d, %Y')}")
    print()
    
    try:
        # Test the customer dashboard endpoint
        response = requests.get(CUSTOMER_DASHBOARD_URL)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check date range info from chart_data
            if 'chart_data' in data and 'date_range_info' in data['chart_data']:
                date_range_info = data['chart_data']['date_range_info']
                print("📊 Chart Data Date Range Info:")
                print(f"   Current Range: {date_range_info.get('current_range')}")
                print(f"   Start Date: {date_range_info.get('start_date')}")
                print(f"   End Date: {date_range_info.get('end_date')}")
                print(f"   Total Days: {date_range_info.get('total_days')}")
                print()
            
            # Check tracking period from analytics_data
            if 'analytics_data' in data and 'tracking_period' in data['analytics_data']:
                tracking_period = data['analytics_data']['tracking_period']
                print("📈 Analytics Tracking Period:")
                print(f"   Date Range Display: {tracking_period.get('date_range_display')}")
                print(f"   Period Start: {tracking_period.get('period_start')}")
                print(f"   Period End: {tracking_period.get('period_end')}")
                print(f"   Current Date: {tracking_period.get('current_date')}")
                print(f"   Tracking Days: {tracking_period.get('tracking_days')}")
                print()
            
            # Check debug info
            if 'debug_info' in data:
                debug_info = data['debug_info']
                print("🔍 Debug Information:")
                print(f"   Date Range Tracking: {debug_info.get('date_range_tracking')}")
                print(f"   Range Start: {debug_info.get('range_start')}")
                print(f"   Range End: {debug_info.get('range_end')}")
                print(f"   Data Generated At: {debug_info.get('data_generated_at')}")
                print()
            
            # Check that today's date is included
            today_str = today.strftime('%Y-%m-%d')
            end_date = data.get('chart_data', {}).get('date_range_info', {}).get('end_date')
            if end_date:
                print(f"✅ Today's Date Check:")
                print(f"   Today: {today_str}")
                print(f"   End Date: {end_date}")
                print(f"   Match: {'YES ✅' if today_str == end_date else 'NO ❌'}")
                print()
            
            # Predict tomorrow's range
            tomorrow_str = tomorrow.strftime('%Y-%m-%d')
            print(f"🔮 Tomorrow's Expected Behavior:")
            print(f"   Tomorrow: {tomorrow_str}")
            print(f"   Should see range like: '{tomorrow.strftime('%B %d')}' or similar")
            print(f"   Range will include: {tomorrow.strftime('%B %d, %Y')}")
            print()
            
            print("✅ Customer Dashboard Date Range Test Completed!")
            
        elif response.status_code == 403:
            print("⚠️  Access denied - customer account required")
            print("   Test demonstrates that the endpoint exists and is secured")
        elif response.status_code == 401:
            print("⚠️  Authentication required - customer login needed")
            print("   Test demonstrates that the endpoint exists and is secured")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server")
        print("   Make sure server is running: python manage.py runserver")
    except Exception as e:
        print(f"❌ Test error: {e}")

def simulate_date_range():
    """Simulate what the date range would look like"""
    print("\n🎯 Date Range Simulation:")
    print("=" * 40)
    
    from datetime import date, timedelta
    
    today = date.today()
    
    # Test different scenarios
    scenarios = [
        ("Today", today),
        ("Tomorrow", today + timedelta(days=1)),
        ("Day after tomorrow", today + timedelta(days=2)),
        ("End of week", today + timedelta(days=7)),
    ]
    
    for scenario_name, test_date in scenarios:
        # Simulate the range logic
        end_date = test_date  
        start_date = end_date - timedelta(days=30)
        
        # Format like the function does
        if start_date.month == end_date.month and start_date.year == end_date.year:
            month_name = start_date.strftime('%B')
            if (end_date - start_date).days <= 7:
                days = []
                current = end_date - timedelta(days=min(6, (end_date - start_date).days))
                while current <= end_date:
                    days.append(str(current.day))
                    current += timedelta(days=1)
                date_range = f"{month_name} {', '.join(days)}"
            else:
                date_range = f"{month_name} {start_date.day} - {end_date.day}, {end_date.year}"
        else:
            date_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
        
        print(f"   {scenario_name}: {date_range}")
    
    print()

if __name__ == '__main__':
    test_customer_date_range()
    simulate_date_range()