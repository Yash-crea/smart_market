from django.urls import path, include
from . import views

app_name = 'smart_market'

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('search/', views.search, name='search'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('whatsapp/', views.whatsapp, name='whatsapp'),
    
    # Legacy ML Recommendations API (keep for backward compatibility)
    path('api/recommendations/', views.get_recommendations_api, name='recommendations_api'),
    
    # NEW: Full REST API
    path('api/', include('marche_smart.api_urls')),

    path('login/', views.unified_login, name='login'),
    path('unified-login/', views.unified_login, name='unified_login'),
    path('signup/', views.customer_signup, name='customer_signup'),
    path('logout/', views.logout_view, name='logout'),
    path('owner/', views.owner_dashboard, name='owner_dashboard'),
    path('owner/orders/', views.all_orders_view, name='all_orders'),
    path('owner/orders/<str:order_number>/status/', views.update_order_status, name='update_order_status'),
    path('owner/inventory/', views.owner_inventory_view, name='owner_inventory'),
    path('owner/inventory/add/', views.add_product, name='add_product'),
    path('owner/inventory/edit/', views.edit_product, name='edit_product'),
    path('owner/inventory/delete/', views.delete_product, name='delete_product'),
    path('owner/inventory/update-stock/', views.update_stock, name='update_stock'),
    path('owner/export_excel/', views.export_dashboard_excel, name='export_dashboard_excel'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('customer/', views.customer_dashboard, name='customer_dashboard'),
    path('cart/', views.cart, name='cart'),
    path('cart/count/', views.cart_count, name='cart_count'),
    path('cart/mini-data/', views.mini_cart_data, name='mini_cart_data'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<str:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('order-confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
]
