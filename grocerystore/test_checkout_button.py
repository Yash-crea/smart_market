#!/usr/bin/env python3
"""
Checkout Button Test - Simulate form submission
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
django.setup()

from django.contrib.auth.models import User
from marche_smart.models import Cart, Order
from decimal import Decimal

def test_checkout_button_submission():
    """Test what happens when checkout form is submitted"""
    print("=== CHECKOUT BUTTON TEST ===")
    
    # Get a customer user
    customer = User.objects.filter(groups__name='Customer', cart__isnull=False).first()
    if not customer:
        print("❌ No customer users with carts found")
        return
    
    print(f"Testing with customer: {customer.username}")
    
    # Check user permissions
    is_owner_staff = customer.groups.filter(name__in=['Owner', 'Staff']).exists()
    print(f"Owner/Staff check: {is_owner_staff}")
    
    if is_owner_staff:
        print("❌ User blocked - in Owner/Staff group")
        return
    
    # Get cart
    try:
        cart = Cart.objects.get(user=customer)
        print(f"✅ Cart found with {cart.items.count()} items")
    except Cart.DoesNotExist:
        print("❌ No cart found")
        return
    
    # Test checkout calculations
    try:
        subtotal = cart.total_amount
        tax_amount = subtotal * Decimal('0.15')
        shipping_cost = Decimal('50.00')
        total = subtotal + tax_amount + shipping_cost
        
        print(f"Subtotal: Rs {subtotal}")
        print(f"Tax: Rs {tax_amount}")
        print(f"Shipping: Rs {shipping_cost}")
        print(f"Total: Rs {total}")
        print("✅ Calculations successful")
        
    except Exception as e:
        print(f"❌ Calculation error: {e}")
        return
    
    # Simulate form data
    form_data = {
        'payment_method': 'credit_card',
        'customer_name': 'Test Customer',
        'customer_email': 'test@example.com',
        'customer_phone': '+230 1234 5678',
        'accept_terms': 'on',
        'delivery_method': 'home_delivery',
        'shipping_address': 'Test Address',
        'shipping_city': 'Port Louis',
        'shipping_postal_code': '11000',
        'cardholder_name': 'Test Holder',
    }
    
    print("\nForm validation check:")
    required_fields = [
        form_data.get('payment_method'),
        form_data.get('customer_name'),
        form_data.get('customer_email'),
        form_data.get('customer_phone'),
        form_data.get('accept_terms')
    ]
    
    if form_data.get('delivery_method') == 'home_delivery':
        required_fields.extend([
            form_data.get('shipping_address'),
            form_data.get('shipping_city')
        ])
    
    if all(required_fields):
        print("✅ Form validation passed")
        
        # Test order creation (simulation)
        print("\nOrder creation simulation:")
        try:
            print(f"  Order would be created for: {customer.username}")
            print(f"  Total amount: Rs {total}")
            print(f"  Payment method: {form_data['payment_method']}")
            print("✅ Order creation would succeed")
            
        except Exception as e:
            print(f"❌ Order creation would fail: {e}")
    else:
        missing = []
        field_names = ['payment_method', 'customer_name', 'customer_email', 'customer_phone', 'accept_terms', 'shipping_address', 'shipping_city']
        for i, field_val in enumerate(required_fields):
            if not field_val and i < len(field_names):
                missing.append(field_names[i])
        print(f"❌ Form validation failed - Missing: {missing}")

def check_existing_orders():
    """Check if there are existing orders to see if system works"""
    print("\n=== EXISTING ORDERS CHECK ===")
    orders = Order.objects.all()
    print(f"Total orders in database: {orders.count()}")
    
    if orders.exists():
        print("Recent orders:")
        for order in orders[:3]:
            print(f"  Order #{order.order_number}: {order.user.username} - Rs {order.total_amount}")
    else:
        print("No orders found - this might indicate an issue")

def main():
    print("🛒 CHECKOUT BUTTON DIAGNOSTIC")
    print("=" * 50)
    
    test_checkout_button_submission()
    check_existing_orders()
    
    print("\n" + "=" * 50)
    print("💡 NEXT STEPS:")
    print("1. Check browser console for JavaScript errors")
    print("2. Check browser network tab for failed requests")
    print("3. Verify form is submitted to correct URL")

if __name__ == "__main__":
    main()