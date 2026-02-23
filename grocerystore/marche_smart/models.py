from django.contrib.auth.models import User
from django.db import models


# Original Marche Smart Models
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    # Extended to match smart_market Products table
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    stock_quantity = models.IntegerField(blank=True, null=True)
    in_stock = models.BooleanField(default=True)
    is_promotional = models.BooleanField(default=False)
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.cart.user.username}'s cart"


# Smart Market Database Models
class Customers(models.Model):
    name = models.CharField(max_length=150)
    email = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    credit_record = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customers'
        verbose_name_plural = "Smart Market Customers"
        app_label = 'marche_smart'

    def __str__(self):
        return self.name


class Employees(models.Model):
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'employees'
        verbose_name_plural = "Employees"
        app_label = 'marche_smart'

    def __str__(self):
        return self.name


class Suppliers(models.Model):
    name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'suppliers'
        verbose_name_plural = "Suppliers"
        app_label = 'marche_smart'

    def __str__(self):
        return self.name


class SmartProducts(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, blank=True, null=True)
    stock_quantity = models.IntegerField(blank=True, null=True)
    is_promotional = models.BooleanField(default=False)
    image_url = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        verbose_name_plural = "Smart Market Products"
        app_label = 'marche_smart'

    def __str__(self):
        return self.name


class Orders(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'orders'
        app_label = 'marche_smart'

    def __str__(self):
        return f"Order #{self.id} - {self.customer.name}"


class OrderItems(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(SmartProducts, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_items'
        app_label = 'marche_smart'

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.id})"


class Payments(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('mobile_payment', 'Mobile Payment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payments'
        app_label = 'marche_smart'

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.amount}"


class Reviews(models.Model):
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    product = models.ForeignKey(SmartProducts, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        app_label = 'marche_smart'

    def __str__(self):
        return f"Review by {self.customer.name} for {self.product.name}"


class Inventory(models.Model):
    CHANGE_TYPES = [
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
    ]
    
    product = models.ForeignKey(SmartProducts, on_delete=models.CASCADE, related_name='inventory_changes')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    quantity_change = models.IntegerField()
    change_date = models.DateTimeField(auto_now_add=True)
    supplier = models.ForeignKey(Suppliers, on_delete=models.SET_NULL, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'inventory'
        verbose_name_plural = "Inventory Changes"
        app_label = 'marche_smart'

    def __str__(self):
        return f"{self.change_type} - {self.product.name} ({self.quantity_change})"


class CustomerSupport(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    subject = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    handled_by = models.ForeignKey(Employees, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'customer_support'
        verbose_name_plural = "Customer Support Tickets"
        app_label = 'marche_smart'

    def __str__(self):
        return f"Ticket: {self.subject} - {self.customer.name}"


class DailySales(models.Model):
    sales_date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'daily_sales'
        verbose_name_plural = "Daily Sales"
        app_label = 'marche_smart'

    def __str__(self):
        return f"Sales for {self.sales_date}: ${self.total_sales}"


class StoreInfo(models.Model):
    store_name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    opening_hours = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'store_info'
        verbose_name_plural = "Store Information"
        app_label = 'marche_smart'

    def __str__(self):
        return self.store_name


class AuditLog(models.Model):
    table_name = models.CharField(max_length=50)
    record_id = models.IntegerField()
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_log'
        verbose_name_plural = "Audit Logs"
        app_label = 'marche_smart'

    def __str__(self):
        return f"Audit: {self.table_name} - Record {self.record_id}"
