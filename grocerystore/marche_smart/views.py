from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db import models

def unified_login(request):
    if request.method == 'POST':
        username = request.POST.get('username') or request.POST.get('email')
        password = request.POST.get('password')
        if not username or not password:
            return render(request, 'unified_login.html', {'error': 'Please provide both username/email and password.'})
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.groups.filter(name='Owner').exists():
                return redirect('marche_smart:owner_dashboard')
            elif user.groups.filter(name='Staff').exists():
                return redirect('marche_smart:staff_dashboard')
            else:
                return redirect('marche_smart:customer_dashboard')
        else:
            return render(request, 'unified_login.html', {'error': 'Invalid credentials'})
    return render(request, 'unified_login.html')

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Owner').exists(), login_url='login')
def owner_dashboard(request):
    sales_total = sum(float(p.price) for p in Product.objects.all())
    customer_count = User.objects.filter(groups__name='Customer').count()
    registrations = customer_count
    inventory = Product.objects.all()
    top_products = Product.objects.order_by('-price')[:5]
    orders_count = 0
    delivery_tracking = 'Not implemented'
    payment_transactions = 'Not implemented'
    context = {
        'sales_total': sales_total,
        'orders_count': orders_count,
        'top_products': top_products,
        'customer_count': customer_count,
        'registrations': registrations,
        'inventory': inventory,
        'delivery_tracking': delivery_tracking,
        'payment_transactions': payment_transactions,
    }
    return render(request, 'owner_dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Staff').exists(), login_url='login')
def staff_dashboard(request):
    return render(request, 'staff_dashboard.html')

@login_required
def customer_dashboard(request):
    if request.user.groups.filter(name__in=['Owner', 'Staff']).exists():
        return redirect('login')
    context = {
        'customer': request.user,
        'current_purchase_total': 42.50,
        'orders': [],
    }
    return render(request, 'customer_dashboard.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')
def customer_signup(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        if not name or not email or not password:
            return render(request, 'customer_signup.html', {'error': 'All fields are required.'})
        if User.objects.filter(email=email).exists():
            return render(request, 'customer_signup.html', {'error': 'Email already registered.'})
        if User.objects.filter(username=email).exists():
            return render(request, 'customer_signup.html', {'error': 'Username already taken.'})
        user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
        # Add user to Customer group
        customer_group, created = Group.objects.get_or_create(name='Customer')
        user.groups.add(customer_group)
        user.save()
        login(request, user)
        return redirect('marche_smart:customer_dashboard')
    return render(request, 'customer_signup.html')

from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, SmartProducts
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.urls import reverse
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from django.conf import settings





def home(request):
    q = request.GET.get('q', '').strip()
    if q:
        products = SmartProducts.objects.using('smart_market').filter(name__icontains=q)
    else:
        products = SmartProducts.objects.using('smart_market').all()[:12]

    return render(request, 'home.html', {'products': products, 'q': q})

def contact(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        question = request.POST.get('question', '').strip()
        
        if not username or not email or not question:
            return render(request, 'contact.html', {'error': 'All fields are required.'})
        
        # Here you can add logic to save the contact form or send an email
        # For now, we'll just show a success message
        # Example: send_mail('Contact Form', f'From: {username} ({email})\n\n{question}', email, ['info@marchesmart.com'])
        
        return render(request, 'contact.html', {'success': True})
    
    return render(request, 'contact.html')

def whatsapp(request):
    user_message = None
    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()
    return render(request, 'whatsapp.html', {'user_message': user_message})

    context = {
        'products': products,
        'query': q,
    }
    return render(request, 'home.html', context)


def shop(request):
    # Get all smart market products
    products = SmartProducts.objects.using('smart_market').all()
    
    # Get unique categories from smart market products
    categories_list = SmartProducts.objects.using('smart_market').values_list('category', flat=True).distinct()
    categories = [{'name': cat, 'id': cat} for cat in categories_list if cat]
    
    # Search filter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(name__icontains=search_query) | products.filter(description__icontains=search_query)
    
    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category=category_filter)
    
    # Price range filter
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except (ValueError, TypeError):
            pass
    
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except (ValueError, TypeError):
            pass
    
    # Get price range for the filter
    all_products = SmartProducts.objects.using('smart_market').all()
    max_price_available = all_products.aggregate(max_price=models.Max('price'))['max_price'] or 0
    
    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_filter,
        'min_price': min_price,
        'max_price': max_price,
        'max_price_available': max_price_available,
    }
    return render(request, 'shop.html', context)


def search(request):
    # simple search endpoint that reuses home template
    return home(request)


def owner_dashboard(request):
    # Sales overview (sum of all product prices as a placeholder)
    sales_total = sum(float(p.price) for p in Product.objects.all())
    # Number of customers (users in Customer group)
    customer_count = User.objects.filter(groups__name='Customer').count()
    registrations = customer_count
    inventory = Product.objects.all()
    top_products = Product.objects.order_by('-price')[:5]
    orders_count = 0
    delivery_tracking = 'Not implemented'
    payment_transactions = 'Not implemented'

    context = {
        'sales_total': sales_total,
        'orders_count': orders_count,
        'top_products': top_products,
        'registrations': registrations,
        'inventory': inventory,
        'delivery_tracking': delivery_tracking,
        'payment_transactions': payment_transactions,
    }
    return render(request, 'owner_dashboard.html', context)


# Export dashboard data to Excel
from django.http import HttpResponse
import openpyxl

def export_dashboard_excel(request):
    sales_total = sum(float(p.price) for p in Product.objects.all())
    active_users = User.objects.filter(groups__name='Customer').count()
    registrations = User.objects.filter(groups__name='Customer').count()
    inventory = Product.objects.all()
    top_products = Product.objects.order_by('-price')[:5]
    orders_count = 0
    delivery_tracking = 'Not implemented'
    payment_transactions = 'Not implemented'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Dashboard'

    ws.append(['Owner Dashboard'])
    ws.append([])
    ws.append(['Total Sales', sales_total])
    ws.append(['Active Users', active_users])
    ws.append(['Registrations', registrations])
    ws.append(['Orders', orders_count])
    ws.append(['Delivery Tracking', delivery_tracking])
    ws.append(['Payment Transactions', payment_transactions])
    ws.append([])
    ws.append(['Top Products'])
    ws.append(['Name', 'Price'])
    for p in top_products:
        ws.append([p.name, float(p.price)])
    ws.append([])
    ws.append(['Inventory Management'])
    ws.append(['Name', 'Price', 'In Stock'])
    for p in inventory:
        ws.append([p.name, float(p.price), 'Yes' if p.in_stock else 'No'])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=dashboard.xlsx'
    wb.save(response)
    return response


@login_required
def customer_dashboard(request):
    if request.user.groups.filter(name__in=['Owner', 'Staff']).exists():
        return redirect('login')
    context = {
        'customer': request.user,
        'current_purchase_total': 42.50,
        'orders': [],
    }
    return render(request, 'customer_dashboard.html', context)


def about(request):
    # render a dedicated About page
    return render(request, 'about.html')


def add_to_cart(request, product_id):
    """Add product to cart"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        # Initialize cart in session if it doesn't exist
        if 'cart' not in request.session:
            request.session['cart'] = {}
        
        cart = request.session['cart']
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            cart[product_id_str]['quantity'] += quantity
        else:
            try:
                product = SmartProducts.objects.using('smart_market').get(id=product_id)
                cart[product_id_str] = {
                    'name': product.name,
                    'price': str(product.price),
                    'quantity': quantity,
                    'image_url': product.image_url,
                }
            except SmartProducts.DoesNotExist:
                return redirect('marche_smart:shop')
        
        # Update cart count in session
        total_items = sum(item['quantity'] for item in cart.values())
        request.session['cart_count'] = total_items
        request.session.modified = True
        
        return redirect('smart_market:cart')
    
    return redirect('marche_smart:shop')


def cart(request):
    """Display shopping cart"""
    cart_items = request.session.get('cart', {})
    
    # Calculate totals
    subtotal = 0
    total_items = 0
    
    for item in cart_items.values():
        item_total = float(item['price']) * item['quantity']
        subtotal += item_total
        total_items += item['quantity']
    
    tax = subtotal * 0.1  # 10% tax
    total = subtotal + tax
    
    context = {
        'cart_items': cart_items,
        'subtotal': f"{subtotal:.2f}",
        'tax': f"{tax:.2f}",
        'total': f"{total:.2f}",
        'item_count': total_items,
    }
    
    return render(request, 'cart.html', context)

def checkout(request):
    # Only allow access if cart is not empty
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('marche_smart:cart')
    return render(request, 'checkout.html')



@require_POST
def remove_from_cart(request, product_id):
    """Remove product from cart"""
    if 'cart' in request.session:
        product_id_str = str(product_id)
        if product_id_str in request.session['cart']:
            del request.session['cart'][product_id_str]
            
            # Update cart count
            cart = request.session['cart']
            total_items = sum(item['quantity'] for item in cart.values())
            request.session['cart_count'] = total_items
            request.session.modified = True
    
    return redirect('marche_smart:cart')


def update_cart(request, product_id):
    """Update product quantity in cart"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            return remove_from_cart(request, product_id)
        
        if 'cart' in request.session:
            product_id_str = str(product_id)
            if product_id_str in request.session['cart']:
                request.session['cart'][product_id_str]['quantity'] = quantity
                
                # Update cart count
                cart = request.session['cart']
                total_items = sum(item['quantity'] for item in cart.values())
                request.session['cart_count'] = total_items
                request.session.modified = True
    
    return redirect('marche_smart:cart')


def generate_password_reset_token(email):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    return serializer.dumps(email, salt='password-reset-salt')

def verify_password_reset_token(token, max_age=3600):
    serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=max_age)
        return email
    except (BadSignature, SignatureExpired):
        return None

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = User.objects.filter(email=email).first()
        if user:
            token = generate_password_reset_token(email)
            reset_url = request.build_absolute_uri(
                reverse('marche_smart:reset_password', args=[token])
            )
            send_mail(
                'Password Reset Request',
                f'Click the link below to reset your password:\n{reset_url}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
        return render(request, 'forgot_password.html', {
            'message': 'If this email exists in our system, you will receive password recovery instructions.'
        })
    return render(request, 'forgot_password.html')


def reset_password(request, token):
    email = verify_password_reset_token(token)
    if not email:
        return render(request, 'reset_password.html', {'error': 'Invalid or expired reset link.'})
    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        if not password or not confirm_password:
            return render(request, 'reset_password.html', {'error': 'All fields are required.'})
        if password != confirm_password:
            return render(request, 'reset_password.html', {'error': 'Passwords do not match.'})
        user = User.objects.filter(email=email).first()
        if user:
            user.set_password(password)
            user.save()
            return render(request, 'reset_password.html', {'message': 'Your password has been reset successfully.'})
        return render(request, 'reset_password.html', {'error': 'User not found.'})
    return render(request, 'reset_password.html')
