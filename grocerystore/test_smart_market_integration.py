#!/usr/bin/env python3
"""
Test script to verify smart market database integration with Django
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
django.setup()

def test_smart_market_integration():
    """Test accessing smart market data through Django models"""
    from marche_smart.models import (
        Customers, SmartProducts, Orders, Suppliers, 
        Reviews, Inventory, DailySales
    )
    
    print("🔍 Testing Smart Market Database Integration")
    print("=" * 50)
    
    try:
        # Test Customers
        customer_count = Customers.objects.count()
        print(f"📊 Customers: {customer_count}")
        if customer_count > 0:
            latest_customer = Customers.objects.latest('created_at')
            print(f"   Latest: {latest_customer.name}")
        
        # Test Products
        product_count = SmartProducts.objects.count()
        print(f"📦 Products: {product_count}")
        if product_count > 0:
            latest_product = SmartProducts.objects.latest('created_at')
            print(f"   Latest: {latest_product.name} - ${latest_product.price}")
        
        # Test Orders
        order_count = Orders.objects.count()
        print(f"🛒 Orders: {order_count}")
        if order_count > 0:
            latest_order = Orders.objects.latest('order_date')
            print(f"   Latest: Order #{latest_order.id} - ${latest_order.total_amount}")
        
        # Test Suppliers
        supplier_count = Suppliers.objects.count()
        print(f"🏪 Suppliers: {supplier_count}")
        
        # Test Reviews
        review_count = Reviews.objects.count()
        print(f"⭐ Reviews: {review_count}")
        
        # Test Inventory
        inventory_count = Inventory.objects.count()
        print(f"📋 Inventory Records: {inventory_count}")
        
        # Test Daily Sales
        sales_count = DailySales.objects.count()
        print(f"💰 Daily Sales Records: {sales_count}")
        
        print("\n✅ Smart Market Database Integration Successful!")
        print("🔗 All tables are now accessible through Django ORM")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def show_sample_data():
    """Show sample data from smart market database"""
    from marche_smart.models import SmartProducts, Customers, Orders
    
    print("\n" + "=" * 50)
    print("📋 Sample Data from Smart Market")
    print("=" * 50)
    
    try:
        # Show top 5 products
        products = SmartProducts.objects.all()[:5]
        print("\n🛍️ Sample Products:")
        for product in products:
            print(f"  - {product.name}: ${product.price} (Stock: {product.stock_quantity})")
        
        # Show top 5 customers
        customers = Customers.objects.all()[:5]
        print("\n👥 Sample Customers:")
        for customer in customers:
            print(f"  - {customer.name} ({customer.email})")
        
        # Show recent orders
        orders = Orders.objects.all().order_by('-order_date')[:3]
        print("\n📦 Recent Orders:")
        for order in orders:
            print(f"  - Order #{order.id}: {order.customer.name} - ${order.total_amount}")
            
    except Exception as e:
        print(f"❌ Error showing sample data: {e}")

if __name__ == "__main__":
    if test_smart_market_integration():
        show_sample_data()
    else:
        print("\n💡 Check your database connection and credentials in settings.py")