#!/usr/bin/env python
"""
Test script to verify Power BI Customer Dashboard date fixes
"""
import requests
import json
from datetime import date

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
CUSTOMER_DASHBOARD_URL = f"{BASE_URL}/api/v1/powerbi/customer-dashboard/"

def test_customer_dashboard_dates():
    print("🔍 Testing Power BI Customer Dashboard Date Fix...")
    print("=" * 60)
    
    try:
        # Test the customer dashboard endpoint
        response = requests.get(CUSTOMER_DASHBOARD_URL)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check debug info
            if 'debug_info' in data:
                debug_info = data['debug_info']
                print("📅 Debug Information:")
                print(f"   Current UTC: {debug_info.get('current_utc')}")
                print(f"   Current Local: {debug_info.get('current_local')}")
                print(f"   Timezone: {debug_info.get('timezone_name')}")
                print(f"   Generated At: {debug_info.get('data_generated_at')}")
                print()
            
            # Check monthly spending dates
            if 'spending_patterns' in data:
                spending_patterns = data['spending_patterns']
                if spending_patterns.get('monthly_spending_12m'):
                    latest_month = spending_patterns['monthly_spending_12m'][-1]
                    print(f"📊 Latest Monthly Spending Entry:")
                    print(f"   Month: {latest_month.get('month')}")
                    print(f"   Expected: 2026-03 (March 2026)")
                    print(f"   ✅ Match: {'YES' if '2026-03' in latest_month.get('month', '') else 'NO'}")
                    print()
            
            # Check daily spending dates  
            if 'spending_patterns' in data:
                spending_patterns = data['spending_patterns']
                if spending_patterns.get('daily_spending_30d'):
                    latest_day = spending_patterns['daily_spending_30d'][-1]
                    print(f"📈 Latest Daily Spending Entry:")
                    print(f"   Date: {latest_day.get('date')}")
                    expected_date = str(date.today())
                    print(f"   Expected: {expected_date}")
                    print(f"   ✅ Match: {'YES' if expected_date in latest_day.get('date', '') else 'NO'}")
                    print()
            
            # Check report generation timestamp
            report_time = data.get('report_generated')
            if report_time:
                print(f"⏰ Report Generated: {report_time}")
                recent = "2026-03-29" in report_time
                print(f"   ✅ Recent Date: {'YES' if recent else 'NO'}")
                print()
            
            print("✅ Customer Dashboard Date Fix Test Completed!")
            
        elif response.status_code == 403:
            print("⚠️  Access denied - customer account required for testing")
            print("   This is expected if no customer user is logged in")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server")
        print("   Make sure server is running: python manage.py runserver")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == '__main__':
    test_customer_dashboard_dates()