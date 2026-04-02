"""
Template context processors for marche_smart app
"""

def user_role_context(request):
    """
    Add user role information and cart data to template context
    """
    context = {
        'is_owner': False,
        'is_staff_member': False,
        'is_customer': True,
        'can_access_cart': True,
        'cart_count': 0,
    }
    
    if request.user.is_authenticated:
        user_groups = request.user.groups.values_list('name', flat=True)
        
        if 'Owner' in user_groups:
            context.update({
                'is_owner': True,
                'is_customer': False,
                'can_access_cart': False,
                'cart_count': 0,
            })
        elif 'Staff' in user_groups:
            context.update({
                'is_staff_member': True,
                'is_customer': False,
                'can_access_cart': False,
                'cart_count': 0,
            })
        else:
            # Regular customer/authenticated user - get cart count
            try:
                from .models import Cart
                cart = Cart.objects.get(user=request.user)
                cart_count = cart.total_items
            except Cart.DoesNotExist:
                cart_count = 0
            
            context.update({
                'is_customer': True,
                'can_access_cart': True,
                'cart_count': cart_count,
            })
    else:
        # Anonymous user - get session cart count
        try:
            from .views import get_session_cart_items
            _, cart_count, _ = get_session_cart_items(request)
        except:
            cart_count = 0
            
        context.update({
            'is_customer': False,  # Not a registered customer but can shop
            'can_access_cart': True,
            'cart_count': cart_count,
        })
    
    return context