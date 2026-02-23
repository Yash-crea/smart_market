from django.urls import path
from . import views

app_name = 'smart_market'

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('search/', views.search, name='search'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('whatsapp/', views.whatsapp, name='whatsapp'),

    path('login/', views.unified_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/export_excel/', views.export_dashboard_excel, name='export_dashboard_excel'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('customer/', views.customer_dashboard, name='customer_dashboard'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<str:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
]
