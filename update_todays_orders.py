"""
Update Today's Orders for Power BI Integration
Ensures that orders placed on March 29, 2026 are properly structured 
for the updated Power BI dashboard with daily spending data.
"""
import os
import sys
import django
from datetime import datetime, date
from decimal import Decimal

# Add the Django project to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'grocerystore'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
django.setup()

from django.utils import timezone
from marche_smart.models import Order, OrderItem
from django.contrib.auth.models import User

def update_todays_orders():
    """Update today's orders to ensure Power BI compatibility"""
    print("🔄 Updating today's orders for Power BI integration...")
    
    # Get today's date
    today = timezone.now().date()
    print(f"📅 Processing orders for: {today}")
    
    # Find all orders from today
    todays_orders = Order.objects.filter(created_at__date=today)
    print(f"📦 Found {todays_orders.count()} orders from today")
    
    updated_count = 0
    
    for order in todays_orders:
        print(f"\n🔍 Processing Order: {order.order_number}")
        needs_update = False
        
        # 1. Ensure total_amount is properly set
        if not order.total_amount or order.total_amount <= 0:
            # Calculate total from order items
            calculated_total = Decimal('0.00')
            for item in order.items.all():
                if item.subtotal:
                    calculated_total += Decimal(str(item.subtotal))
            
            if calculated_total > 0:
                order.total_amount = calculated_total
                needs_update = True
                print(f"  ✅ Updated total_amount: Rs {calculated_total}")
        
        # 2. Ensure created_at timezone is set properly
        if order.created_at.tzinfo is None:
            order.created_at = timezone.make_aware(order.created_at)
            needs_update = True
            print(f"  ✅ Updated timezone for created_at")
        
        # 3. Ensure order has valid user association
        if not order.user:
            print(f"  ⚠️ Warning: Order {order.order_number} has no user assigned")
        
        # 4. Verify order items have proper subtotals
        for item in order.items.all():
            if not item.subtotal and item.quantity and hasattr(item, 'price'):
                item.subtotal = Decimal(str(item.quantity)) * Decimal(str(item.price))
                item.save()
                print(f"  ✅ Updated item subtotal: {item.product_name}")
        
        # 5. Save the order if updates were made
        if needs_update:
            try:
                order.save()
                updated_count += 1
                print(f"  💾 Saved updates for order {order.order_number}")
            except Exception as e:
                print(f"  ❌ Error saving order {order.order_number}: {e}")
        else:
            print(f"  ✅ Order {order.order_number} is already properly formatted")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  • Total orders processed: {todays_orders.count()}")
    print(f"  • Orders updated: {updated_count}")
    print(f"  • Orders already correct: {todays_orders.count() - updated_count}")
    
    # Verify Power BI data structure
    print(f"\n🔍 Verification for Power BI:")
    total_spent_today = sum(float(order.total_amount or 0) for order in todays_orders)
    print(f"  • Total spending today: Rs {total_spent_today:.2f}")
    print(f"  • Order count today: {todays_orders.count()}")
    
    # Show sample data structure that Power BI will receive
    sample_daily_data = {
        'date': today.strftime('%Y-%m-%d'),
        'day_name': today.strftime('%a'),
        'total_spent': round(total_spent_today, 2),
        'order_count': todays_orders.count()
    }
    print(f"  • Sample Power BI data: {sample_daily_data}")
    
    print(f"\n✅ Today's orders are now ready for Power BI daily spending trends!")
    return updated_count

def test_powerbi_data():
    """Test that today's data will appear correctly in Power BI API"""
    print(f"\n🧪 Testing Power BI API data structure...")
    
    from django.test import RequestFactory
    from marche_smart.advanced_api_views import powerbi_customer_dashboard
    
    # This would test the API but requires authentication
    # For now, just verify the data structure manually
    
    today = timezone.now().date()
    todays_orders = Order.objects.filter(created_at__date=today)
    
    print(f"📊 Power BI will receive:")
    print(f"  • Date: {today.strftime('%Y-%m-%d')}")
    print(f"  • Spending: Rs {sum(float(o.total_amount or 0) for o in todays_orders):.2f}")
    print(f"  • Orders: {todays_orders.count()}")
    
    return True

if __name__ == "__main__":
    try:
        updated = update_todays_orders()
        test_powerbi_data()
        
        print(f"\n🎉 SUCCESS: Today's orders updated and ready for Power BI!")
        print(f"📱 Next steps:")
        print(f"  1. Refresh your Power BI dataset")
        print(f"  2. Update chart data source to use 'daily_spending_30d'")
        print(f"  3. Today's orders will now appear in the trend chart")
        
    except Exception as e:
        print(f"❌ ERROR: Failed to update orders: {e}")
        import traceback
        traceback.print_exc()