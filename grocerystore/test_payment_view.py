#!/usr/bin/env python3
"""
Direct Test of Process Payment View
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
from marche_smart.views import process_payment
from django.http import HttpRequest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from unittest.mock import Mock

def test_process_payment_view():
    """Test the actual process_payment view function"""
    print("=== PROCESS PAYMENT VIEW TEST ===")
    
    # Get customer user
    customer = User.objects.filter(groups__name='Customer', cart__isnull=False).first()
    if not customer:
        print("❌ No customer found")
        return False
    
    print(f"Testing with customer: {customer.username}")
    
    # Create mock request
    request = HttpRequest()
    request.method = 'POST'
    request.user = customer
    
    # Add required middleware attributes
    request.session = SessionStore()
    request._messages = FallbackStorage(request)
    
    # Add form data
    request.POST = {
        'payment_method': 'credit_card',
        'customer_name': 'Test Customer',
        'customer_email': 'test@example.com',
        'customer_phone': '+230 1234 5678',
        'accept_terms': 'on',
        'delivery_method': 'home_delivery',
        'shipping_address': 'Test Address',
        'shipping_city': 'Port Louis',
        'shipping_postal_code': '11000',
        'cardholder_name': 'Test Cardholder',
    }
    
    try:
        # Get cart
        cart = Cart.objects.get(user=customer)
        print(f"Cart items: {cart.items.count()}")
        print(f"Cart total: Rs {cart.total_amount}")
        
        # Count orders before
        orders_before = Order.objects.count()
        print(f"Orders before: {orders_before}")
        
        # Call the view function
        print("Calling process_payment view...")
        response = process_payment(request, cart=cart)
        
        # Check response
        print(f"Response status: {response.status_code}")
        
        # Count orders after
        orders_after = Order.objects.count()
        print(f"Orders after: {orders_after}")
        
        if orders_after > orders_before:
            print("✅ Order created successfully!")
            new_order = Order.objects.latest('created_at')
            print(f"New order: #{new_order.order_number} - Rs {new_order.total_amount}")
        else:
            print("❌ No new order created")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_process_payment_view()