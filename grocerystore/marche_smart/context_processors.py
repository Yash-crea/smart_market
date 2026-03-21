"""
Template context processors for marche_smart app
"""

def user_role_context(request):
    """
    Add user role information to template context
    """
    context = {
        'is_owner': False,
        'is_staff_member': False,
        'is_customer': True,
        'can_access_cart': True,
    }
    
    if request.user.is_authenticated:
        user_groups = request.user.groups.values_list('name', flat=True)
        
        if 'Owner' in user_groups:
            context.update({
                'is_owner': True,
                'is_customer': False,
                'can_access_cart': False,
            })
        elif 'Staff' in user_groups:
            context.update({
                'is_staff_member': True,
                'is_customer': False,
                'can_access_cart': False,
            })
        else:
            # Regular customer/authenticated user
            context.update({
                'is_customer': True,
                'can_access_cart': True,
            })
    else:
        # Anonymous user - can access cart
        context.update({
            'is_customer': False,  # Not a registered customer but can shop
            'can_access_cart': True,
        })
    
    return context