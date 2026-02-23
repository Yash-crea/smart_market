from django.contrib import admin
from .models import (
    Product, Category, Cart, CartItem,
    Customers, Employees, Suppliers, SmartProducts, Orders, OrderItems,
    Payments, Reviews, Inventory, CustomerSupport, DailySales, StoreInfo, AuditLog
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity', 'in_stock', 'is_promotional')
    list_filter = ('category', 'in_stock', 'is_promotional', 'created_at')
    search_fields = ('name', 'description')
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock_quantity', 'in_stock', 'is_promotional')
        }),
        ('Media', {
            'fields': ('image_url',)
        }),
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    search_fields = ('cart__user__username', 'product__name')


# Smart Market Models Admin
@admin.register(Customers)
class CustomersAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'credit_record', 'created_at')
    list_filter = ('created_at', 'credit_record')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at',)


@admin.register(Employees)
class EmployeesAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'email', 'contact_number', 'hire_date')
    list_filter = ('role', 'hire_date')
    search_fields = ('name', 'email', 'role')


@admin.register(Suppliers)
class SuppliersAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'contact_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'email')
    readonly_fields = ('created_at',)


@admin.register(SmartProducts)
class SmartProductsAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity', 'is_promotional', 'created_at')
    list_filter = ('category', 'is_promotional', 'created_at')
    search_fields = ('name', 'description', 'category')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'total_amount', 'order_date')
    list_filter = ('status', 'order_date')
    search_fields = ('customer__name', 'customer__email')
    readonly_fields = ('order_date',)
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing completed orders
        if obj and obj.status == 'completed':
            return False
        return True


@admin.register(OrderItems)
class OrderItemsAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    search_fields = ('order__customer__name', 'product__name')
    list_filter = ('order__status',)


@admin.register(Payments)
class PaymentsAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_method', 'amount', 'status', 'transaction_date')
    list_filter = ('payment_method', 'status', 'transaction_date')
    search_fields = ('order__customer__name',)
    readonly_fields = ('transaction_date',)


@admin.register(Reviews)
class ReviewsAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('customer__name', 'product__name', 'comment')
    readonly_fields = ('created_at',)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'change_type', 'quantity_change', 'supplier', 'change_date')
    list_filter = ('change_type', 'change_date', 'supplier')
    search_fields = ('product__name', 'notes')
    readonly_fields = ('change_date',)


@admin.register(CustomerSupport)
class CustomerSupportAdmin(admin.ModelAdmin):
    list_display = ('subject', 'customer', 'status', 'handled_by', 'created_at')
    list_filter = ('status', 'created_at', 'handled_by')
    search_fields = ('subject', 'customer__name', 'description')
    readonly_fields = ('created_at',)


@admin.register(DailySales)
class DailySalesAdmin(admin.ModelAdmin):
    list_display = ('sales_date', 'total_sales')
    list_filter = ('sales_date',)
    date_hierarchy = 'sales_date'


@admin.register(StoreInfo)
class StoreInfoAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'contact_number', 'email')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'record_id', 'updated_by', 'updated_at')
    list_filter = ('table_name', 'updated_at', 'updated_by')
    search_fields = ('table_name', 'updated_by')
    readonly_fields = ('updated_at',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
