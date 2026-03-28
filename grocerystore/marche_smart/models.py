from django.contrib.auth.models import User
from django.db import models
from decimal import Decimal


# Original Marche Smart Models
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    # Seasonal and Festival Choices
    SEASON_CHOICES = [
        ('spring', 'Spring (March-May)'),
        ('summer', 'Summer (June-August)'),
        ('monsoon', 'Monsoon (September-November)'),
        ('winter', 'Winter (December-February)'),
        ('all_year', 'All Year Round'),
    ]
    
    FESTIVAL_CHOICES = [
        ('diwali', 'Diwali'),
        ('holi', 'Holi'),
        ('eid', 'Eid'),
        ('christmas', 'Christmas'),
        ('easter', 'Easter'),
        ('new_year', 'New Year'),
        ('durga_puja', 'Durga Puja'),
        ('ganesh_chaturthi', 'Ganesh Chaturthi'),
        ('karwa_chauth', 'Karwa Chauth'),
        ('dussehra', 'Dussehra'),
        ('raksha_bandhan', 'Raksha Bandhan'),
        ('valentine', 'Valentine\'s Day'),
        ('mother_day', 'Mother\'s Day'),
        ('father_day', 'Father\'s Day'),
        ('none', 'No Festival Association'),
    ]

    # Extended to match smart_market Products table
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    stock_quantity = models.IntegerField(blank=True, null=True)
    in_stock = models.BooleanField(default=True)
    is_promotional = models.BooleanField(default=False)
    image_url = models.URLField(blank=True, null=True)
    
    # Seasonal and Temporal Fields for Recommendations
    peak_season = models.CharField(max_length=20, choices=SEASON_CHOICES, default='all_year', 
                                   help_text="Primary season when this product sells most")
    festival_association = models.CharField(max_length=20, choices=FESTIVAL_CHOICES, default='none',
                                           help_text="Festival period when this product is in high demand")
    weekend_boost = models.BooleanField(default=False, 
                                       help_text="Product sells significantly more on weekends")
    weekend_sales_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.0,
                                                   help_text="Weekend sales multiplier (e.g., 1.5 = 50% more sales)")
    
    # Monthly Sales Pattern (JSON field to store sales data per month)
    monthly_sales_pattern = models.JSONField(default=dict, blank=True,
                                           help_text="Sales pattern by month {1: 120, 2: 85, ...} representing relative sales")
    
    # Festival Period Performance
    festival_sales_boost = models.DecimalField(max_digits=3, decimal_places=2, default=1.0,
                                             help_text="Sales multiplier during associated festival period")
    
    # Recommendation Priority
    seasonal_priority = models.IntegerField(default=1, 
                                          help_text="Priority for seasonal recommendations (1-10, higher = more priority)")
    
    # ML Forecasting and Time-Series Analysis Fields
    demand_trend = models.CharField(max_length=20, choices=[
        ('increasing', 'Increasing'),
        ('decreasing', 'Decreasing'), 
        ('stable', 'Stable'),
        ('volatile', 'Volatile'),
        ('seasonal', 'Seasonal Pattern'),
    ], default='stable', help_text="Overall demand trend for ML forecasting")
    
    # Historical sales velocity (units per week)
    avg_weekly_sales = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                         help_text="Average weekly sales for forecasting")
    avg_monthly_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                          help_text="Average monthly sales for forecasting")
    
    # Price elasticity for demand forecasting
    price_elasticity = models.DecimalField(max_digits=4, decimal_places=3, default=1.0,
                                         help_text="Price elasticity coefficient for ML models")
    
    # External factors affecting demand
    weather_dependent = models.BooleanField(default=False, 
                                          help_text="Sales affected by weather patterns")
    economic_sensitive = models.BooleanField(default=False,
                                           help_text="Sales sensitive to economic conditions")
    
    # ML Model Predictions (updated by forecasting system)
    predicted_demand_7d = models.IntegerField(default=0, help_text="ML predicted demand for next 7 days")
    predicted_demand_30d = models.IntegerField(default=0, help_text="ML predicted demand for next 30 days")
    predicted_revenue_30d = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                              help_text="ML predicted revenue for next 30 days")
    
    # Forecasting accuracy metrics
    forecast_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                          help_text="ML model accuracy percentage (0-100)")
    last_forecast_update = models.DateTimeField(null=True, blank=True,
                                               help_text="Last time ML predictions were updated")
    
    # Seasonal coefficients for different time periods (JSON)
    seasonal_coefficients = models.JSONField(default=dict, blank=True,
                                            help_text="Seasonal multipliers by month/week for ML models")
    
    # Promotional impact data
    promotion_lift = models.DecimalField(max_digits=4, decimal_places=2, default=1.0,
                                       help_text="Average sales lift during promotions")
    
    # Stock-out frequency for demand planning
    stockout_frequency = models.DecimalField(max_digits=4, decimal_places=2, default=0,
                                           help_text="Stock-out frequency (times per year)")
    
    # Lead time for restocking (for inventory forecasting)
    lead_time_days = models.IntegerField(default=7, help_text="Lead time for restocking (days)")
    
    # Minimum and maximum stock levels (for ML inventory optimization)
    min_stock_level = models.IntegerField(default=0, help_text="Minimum stock level for alerts")
    max_stock_level = models.IntegerField(default=1000, help_text="Maximum stock capacity")
    reorder_point = models.IntegerField(default=0, help_text="Automatic reorder point")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def is_seasonal_product(self):
        """Check if product has specific seasonal patterns"""
        return self.peak_season != 'all_year' or self.festival_association != 'none'
    
    def get_current_season_multiplier(self):
        """Get sales multiplier for current season"""
        import datetime
        current_month = datetime.datetime.now().month
        
        # Define seasons
        season_months = {
            'spring': [3, 4, 5],
            'summer': [6, 7, 8], 
            'monsoon': [9, 10, 11],
            'winter': [12, 1, 2]
        }
        
        current_season = None
        for season, months in season_months.items():
            if current_month in months:
                current_season = season
                break
                
        # Return higher multiplier if current season matches peak season
        if current_season == self.peak_season:
            return 1.5  # 50% boost during peak season
        elif self.peak_season == 'all_year':
            return 1.0
        else:
            return 0.8  # 20% reduction during non-peak season
    
    def is_weekend_favorite(self):
        """Check if product has weekend boost"""
        return self.weekend_boost
    
    def get_festival_recommendation_score(self):
        """Get recommendation score during festival period"""
        if self.festival_association != 'none':
            return self.seasonal_priority * self.festival_sales_boost
        return self.seasonal_priority
    
    def update_ml_predictions(self, demand_7d, demand_30d, revenue_30d, accuracy):
        """Update ML predictions for this product"""
        from django.utils import timezone
        self.predicted_demand_7d = demand_7d
        self.predicted_demand_30d = demand_30d
        self.predicted_revenue_30d = revenue_30d
        self.forecast_accuracy = accuracy
        self.last_forecast_update = timezone.now()
        self.save()
    
    def needs_restock(self):
        """Check if product needs restocking based on current stock and predictions"""
        if self.stock_quantity is None:
            return False
        return self.stock_quantity <= self.reorder_point
    
    def get_demand_forecast_features(self):
        """Get features for ML demand forecasting"""
        import datetime
        current_date = datetime.datetime.now()
        return {
            'current_stock': self.stock_quantity or 0,
            'price': float(self.price),
            'price_elasticity': float(self.price_elasticity),
            'avg_weekly_sales': float(self.avg_weekly_sales),
            'weekend_multiplier': float(self.weekend_sales_multiplier),
            'seasonal_multiplier': self.get_current_season_multiplier(),
            'month': current_date.month,
            'day_of_week': current_date.weekday(),
            'is_promotional': self.is_promotional,
            'weather_dependent': self.weather_dependent,
            'economic_sensitive': self.economic_sensitive,
            'seasonal_coefficients': self.seasonal_coefficients,
        }


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"
    
    @property
    def total_amount(self):
        subtotals = [item.subtotal for item in self.items.all()]
        return Decimal('0') if not subtotals else sum(subtotals)
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    smart_product = models.ForeignKey('SmartProducts', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        product_name = self.product.name if self.product else self.smart_product.name
        return f"{self.quantity} x {product_name} in {self.cart.user.username}'s cart"
    
    @property
    def unit_price(self):
        return self.product.price if self.product else self.smart_product.price
    
    @property
    def subtotal(self):
        return self.unit_price * self.quantity
    
    @property
    def product_name(self):
        return self.product.name if self.product else self.smart_product.name


# Smart Market Database Models (now using SQLite)
class Customers(models.Model):
    name = models.CharField(max_length=150)
    email = models.CharField(max_length=150, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    credit_record = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Smart Market Customers"

    def __str__(self):
        return self.name


class Employees(models.Model):
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Employees"

    def __str__(self):
        return self.name


class Suppliers(models.Model):
    name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Suppliers"

    def __str__(self):
        return self.name


class SmartProducts(models.Model):
    # Seasonal and Festival Choices
    SEASON_CHOICES = [
        ('spring', 'Spring (March-May)'),
        ('summer', 'Summer (June-August)'),
        ('monsoon', 'Monsoon (September-November)'),
        ('winter', 'Winter (December-February)'),
        ('all_year', 'All Year Round'),
    ]
    
    FESTIVAL_CHOICES = [
        ('diwali', 'Diwali'),
        ('holi', 'Holi'),
        ('eid', 'Eid'),
        ('christmas', 'Christmas'),
        ('easter', 'Easter'),
        ('new_year', 'New Year'),
        ('durga_puja', 'Durga Puja'),
        ('ganesh_chaturthi', 'Ganesh Chaturthi'),
        ('karwa_chauth', 'Karwa Chauth'),
        ('dussehra', 'Dussehra'),
        ('raksha_bandhan', 'Raksha Bandhan'),
        ('valentine', 'Valentine\'s Day'),
        ('mother_day', 'Mother\'s Day'),
        ('father_day', 'Father\'s Day'),
        ('none', 'No Festival Association'),
    ]

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, blank=True, null=True)
    stock_quantity = models.IntegerField(blank=True, null=True)
    is_promotional = models.BooleanField(default=False)
    image_url = models.CharField(max_length=255, blank=True, null=True)
    
    # Seasonal and Temporal Fields for Recommendations
    peak_season = models.CharField(max_length=20, choices=SEASON_CHOICES, default='all_year', 
                                   help_text="Primary season when this product sells most")
    festival_association = models.CharField(max_length=20, choices=FESTIVAL_CHOICES, default='none',
                                           help_text="Festival period when this product is in high demand")
    weekend_boost = models.BooleanField(default=False, 
                                       help_text="Product sells significantly more on weekends")
    weekend_sales_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.0,
                                                   help_text="Weekend sales multiplier (e.g., 1.5 = 50% more sales)")
    
    # Monthly Sales Pattern (JSON field to store sales data per month)
    monthly_sales_pattern = models.JSONField(default=dict, blank=True,
                                           help_text="Sales pattern by month {1: 120, 2: 85, ...} representing relative sales")
    
    # Festival Period Performance
    festival_sales_boost = models.DecimalField(max_digits=3, decimal_places=2, default=1.0,
                                             help_text="Sales multiplier during associated festival period")
    
    # Recommendation Priority
    seasonal_priority = models.IntegerField(default=1, 
                                          help_text="Priority for seasonal recommendations (1-10, higher = more priority)")
    
    # ML Forecasting and Time-Series Analysis Fields
    demand_trend = models.CharField(max_length=20, choices=[
        ('increasing', 'Increasing'),
        ('decreasing', 'Decreasing'), 
        ('stable', 'Stable'),
        ('volatile', 'Volatile'),
        ('seasonal', 'Seasonal Pattern'),
    ], default='stable', help_text="Overall demand trend for ML forecasting")
    
    # Historical sales velocity (units per week)
    avg_weekly_sales = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                         help_text="Average weekly sales for forecasting")
    avg_monthly_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                          help_text="Average monthly sales for forecasting")
    
    # Price elasticity for demand forecasting
    price_elasticity = models.DecimalField(max_digits=4, decimal_places=3, default=1.0,
                                         help_text="Price elasticity coefficient for ML models")
    
    # External factors affecting demand
    weather_dependent = models.BooleanField(default=False, 
                                          help_text="Sales affected by weather patterns")
    economic_sensitive = models.BooleanField(default=False,
                                           help_text="Sales sensitive to economic conditions")
    
    # ML Model Predictions (updated by forecasting system)
    predicted_demand_7d = models.IntegerField(default=0, help_text="ML predicted demand for next 7 days")
    predicted_demand_30d = models.IntegerField(default=0, help_text="ML predicted demand for next 30 days")
    predicted_revenue_30d = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                              help_text="ML predicted revenue for next 30 days")
    
    # Forecasting accuracy metrics
    forecast_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                          help_text="ML model accuracy percentage (0-100)")
    last_forecast_update = models.DateTimeField(null=True, blank=True,
                                               help_text="Last time ML predictions were updated")
    
    # Seasonal coefficients for different time periods (JSON)
    seasonal_coefficients = models.JSONField(default=dict, blank=True,
                                            help_text="Seasonal multipliers by month/week for ML models")
    
    # Promotional impact data
    promotion_lift = models.DecimalField(max_digits=4, decimal_places=2, default=1.0,
                                       help_text="Average sales lift during promotions")
    
    # Stock-out frequency for demand planning
    stockout_frequency = models.DecimalField(max_digits=4, decimal_places=2, default=0,
                                           help_text="Stock-out frequency (times per year)")
    
    # Lead time for restocking (for inventory forecasting)
    lead_time_days = models.IntegerField(default=7, help_text="Lead time for restocking (days)")
    
    # Minimum and maximum stock levels (for ML inventory optimization)
    min_stock_level = models.IntegerField(default=0, help_text="Minimum stock level for alerts")
    max_stock_level = models.IntegerField(default=1000, help_text="Maximum stock capacity")
    reorder_point = models.IntegerField(default=0, help_text="Automatic reorder point")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Smart Market Products"

    def __str__(self):
        return self.name
    
    def is_seasonal_product(self):
        """Check if product has specific seasonal patterns"""
        return self.peak_season != 'all_year' or self.festival_association != 'none'
    
    def get_current_season_multiplier(self):
        """Get sales multiplier for current season"""
        import datetime
        current_month = datetime.datetime.now().month
        
        # Define seasons
        season_months = {
            'spring': [3, 4, 5],
            'summer': [6, 7, 8], 
            'monsoon': [9, 10, 11],
            'winter': [12, 1, 2]
        }
        
        current_season = None
        for season, months in season_months.items():
            if current_month in months:
                current_season = season
                break
                
        # Return higher multiplier if current season matches peak season
        if current_season == self.peak_season:
            return 1.5  # 50% boost during peak season
        elif self.peak_season == 'all_year':
            return 1.0
        else:
            return 0.8  # 20% reduction during non-peak season
    
    def is_weekend_favorite(self):
        """Check if product has weekend boost"""
        return self.weekend_boost
    
    def get_festival_recommendation_score(self):
        """Get recommendation score during festival period"""
        if self.festival_association != 'none':
            return self.seasonal_priority * self.festival_sales_boost
        return self.seasonal_priority
    
    def update_ml_predictions(self, demand_7d, demand_30d, revenue_30d, accuracy):
        """Update ML predictions for this product"""
        from django.utils import timezone
        self.predicted_demand_7d = demand_7d
        self.predicted_demand_30d = demand_30d
        self.predicted_revenue_30d = revenue_30d
        self.forecast_accuracy = accuracy
        self.last_forecast_update = timezone.now()
        self.save()
    
    def needs_restock(self):
        """Check if product needs restocking based on current stock and predictions"""
        if self.stock_quantity is None:
            return False
        return self.stock_quantity <= self.reorder_point
    
    def get_demand_forecast_features(self):
        """Get features for ML demand forecasting"""
        import datetime
        current_date = datetime.datetime.now()
        return {
            'current_stock': self.stock_quantity or 0,
            'price': float(self.price),
            'price_elasticity': float(self.price_elasticity),
            'avg_weekly_sales': float(self.avg_weekly_sales),
            'weekend_multiplier': float(self.weekend_sales_multiplier),
            'seasonal_multiplier': self.get_current_season_multiplier(),
            'month': current_date.month,
            'day_of_week': current_date.weekday(),
            'is_promotional': self.is_promotional,
            'weather_dependent': self.weather_dependent,
            'economic_sensitive': self.economic_sensitive,
            'seasonal_coefficients': self.seasonal_coefficients,
        }


# Enhanced Order System
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Link to Django User instead of Customers for unified auth
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Customer details for order
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Shipping address
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    
    # Order totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    smart_product = models.ForeignKey(SmartProducts, on_delete=models.CASCADE, null=True, blank=True)
    
    # Store product details at time of order
    product_name = models.CharField(max_length=150)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name} (Order #{self.order.order_number})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate subtotal
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('apple_pay', 'Apple Pay'),
        ('google_pay', 'Google Pay'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment details
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_gateway = models.CharField(max_length=50, blank=True, null=True)
    
    # Card details (encrypted in real system)
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    card_brand = models.CharField(max_length=20, blank=True, null=True)
    
    # Billing address
    billing_name = models.CharField(max_length=150, blank=True)
    billing_address = models.TextField(blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    # Additional info
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} for Order #{self.order.order_number} - Rs {self.amount}"


class Reviews(models.Model):
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    product = models.ForeignKey(SmartProducts, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
        verbose_name_plural = "Inventory Changes"

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
        verbose_name_plural = "Customer Support Tickets"

    def __str__(self):
        return f"Ticket: {self.subject} - {self.customer.name}"


class DailySales(models.Model):
    sales_date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name_plural = "Daily Sales"

    def __str__(self):
        return f"Sales for {self.sales_date}: Rs {self.total_sales}"


class StoreInfo(models.Model):
    store_name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    opening_hours = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Store Information"

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
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return f"Audit: {self.table_name} - Record {self.record_id}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_order', 'New Order'),
        ('order_cancelled', 'Order Cancelled'),
        ('payment_received', 'Payment Received'),
        ('low_stock', 'Low Stock Alert'),
        ('new_customer', 'New Customer Registration'),
        ('support_ticket', 'Support Ticket'),
        ('system', 'System Notification'),
    ]
    
    recipient_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.recipient_user.username}"


class SeasonalSalesData(models.Model):
    """Track sales data for products by time period to improve seasonal recommendations"""
    
    # Link to both product types
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True, related_name='seasonal_sales')
    smart_product = models.ForeignKey(SmartProducts, on_delete=models.CASCADE, null=True, blank=True, related_name='seasonal_sales')
    
    # Time period tracking
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    week_of_year = models.IntegerField()  # 1-52
    is_weekend = models.BooleanField(default=False)
    is_festival_period = models.BooleanField(default=False)
    festival_name = models.CharField(max_length=50, blank=True, null=True)
    
    # Sales metrics
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    units_sold = models.IntegerField(default=0)
    average_daily_sales = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Derived metrics
    season = models.CharField(max_length=20, blank=True)  # Auto-calculated based on month
    performance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Relative performance score
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['product', 'year', 'month'], ['smart_product', 'year', 'month']]
        ordering = ['-year', '-month']
        
    def save(self, *args, **kwargs):
        # Auto-calculate season based on month
        season_map = {
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'monsoon', 10: 'monsoon', 11: 'monsoon'
        }
        self.season = season_map.get(self.month, 'unknown')
        super().save(*args, **kwargs)
    
    def __str__(self):
        product_name = self.product.name if self.product else self.smart_product.name
        return f"{product_name} - {self.year}/{self.month} - {self.units_sold} units"
    
    @classmethod
    def get_seasonal_recommendations(cls, season=None, festival=None, is_weekend=False):
        """Get products recommended for current season/time"""
        from django.db.models import Avg, Sum
        
        queryset = cls.objects.all()
        
        if season:
            queryset = queryset.filter(season=season)
        if festival:
            queryset = queryset.filter(festival_name=festival, is_festival_period=True)
        if is_weekend:
            queryset = queryset.filter(is_weekend=True)
            
        # Get products with high performance in the specified time period
        return queryset.values('product__name', 'smart_product__name').annotate(
            avg_performance=Avg('performance_score'),
            total_units=Sum('units_sold')
        ).filter(avg_performance__gte=1.2).order_by('-avg_performance')


class ProductRecommendationLog(models.Model):
    """Log recommendations made to track effectiveness"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_logs')
    
    # Product recommended
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    smart_product = models.ForeignKey(SmartProducts, on_delete=models.CASCADE, null=True, blank=True)
    
    # Recommendation context
    recommendation_type = models.CharField(max_length=30, choices=[
        ('seasonal', 'Seasonal Recommendation'),
        ('festival', 'Festival Recommendation'),
        ('weekend', 'Weekend Favorite'),
        ('trending', 'Trending Product'),
    ])
    
    context_data = models.JSONField(default=dict, help_text="Context like season, festival, etc.")
    
    # User interaction
    was_viewed = models.BooleanField(default=False)
    was_added_to_cart = models.BooleanField(default=False)
    was_purchased = models.BooleanField(default=False)
    
    # Timestamps
    recommended_at = models.DateTimeField(auto_now_add=True)
    last_interaction = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-recommended_at']
        
    def __str__(self):
        product_name = self.product.name if self.product else self.smart_product.name
        return f"{self.recommendation_type} - {product_name} to {self.user.username}"


class MLForecastModel(models.Model):
    """Store ML model configurations and performance metrics"""
    
    MODEL_TYPES = [
        ('arima', 'ARIMA Time Series'),
        ('lstm', 'LSTM Neural Network'),
        ('prophet', 'Facebook Prophet'),
        ('regression', 'Linear Regression'),
        ('random_forest', 'Random Forest'),
        ('xgboost', 'XGBoost'),
        ('ensemble', 'Ensemble Model'),
    ]
    
    FORECAST_TYPES = [
        ('demand', 'Demand Forecasting'),
        ('revenue', 'Revenue Forecasting'),
        ('inventory', 'Inventory Optimization'),
        ('pricing', 'Price Optimization'),
        ('seasonal', 'Seasonal Analysis'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    forecast_type = models.CharField(max_length=20, choices=FORECAST_TYPES)
    
    # Model configuration
    parameters = models.JSONField(default=dict, help_text="Model hyperparameters")
    features_used = models.JSONField(default=list, help_text="List of features used in the model")
    
    # Performance metrics
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    mae = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Mean Absolute Error")
    rmse = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Root Mean Square Error")
    mape = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Mean Absolute Percentage Error")
    
    # Model status
    is_active = models.BooleanField(default=True)
    last_trained = models.DateTimeField(null=True, blank=True)
    next_retrain_date = models.DateTimeField(null=True, blank=True)
    
    # Model file path (for storing model artifacts)
    model_file_path = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-accuracy_score', '-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.model_type}) - {self.accuracy_score}% accuracy"


class ForecastPrediction(models.Model):
    """Store individual forecast predictions for tracking and evaluation"""
    
    PREDICTION_HORIZONS = [
        ('1d', '1 Day'),
        ('7d', '7 Days'),
        ('30d', '30 Days'),
        ('90d', '90 Days'),
        ('1y', '1 Year'),
    ]
    
    # Link to model and product
    model = models.ForeignKey(MLForecastModel, on_delete=models.CASCADE, related_name='predictions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    smart_product = models.ForeignKey(SmartProducts, on_delete=models.CASCADE, null=True, blank=True)
    
    # Prediction details
    prediction_date = models.DateTimeField(auto_now_add=True)
    target_date = models.DateTimeField(help_text="Date this prediction is for")
    horizon = models.CharField(max_length=10, choices=PREDICTION_HORIZONS)
    
    # Prediction values
    predicted_value = models.DecimalField(max_digits=12, decimal_places=2)
    confidence_interval_lower = models.DecimalField(max_digits=12, decimal_places=2)
    confidence_interval_upper = models.DecimalField(max_digits=12, decimal_places=2)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Actual results (filled in after the prediction date)
    actual_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    prediction_error = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_accurate = models.BooleanField(null=True, blank=True, help_text="Within confidence interval")
    
    # Additional context
    context_data = models.JSONField(default=dict, help_text="Additional context for this prediction")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-prediction_date']
        unique_together = [['model', 'product', 'target_date'], ['model', 'smart_product', 'target_date']]
    
    def __str__(self):
        product_name = self.product.name if self.product else self.smart_product.name
        return f"{product_name} - {self.predicted_value} ({self.horizon})"
    
    def calculate_error(self):
        """Calculate prediction error when actual value is known"""
        if self.actual_value is not None:
            self.prediction_error = abs(self.actual_value - self.predicted_value)
            # Check if prediction is within confidence interval
            self.is_accurate = (
                self.confidence_interval_lower <= self.actual_value <= self.confidence_interval_upper
            )
            self.save()


class WeatherData(models.Model):
    """Store weather data for weather-dependent product forecasting"""
    
    WEATHER_CONDITIONS = [
        ('sunny', 'Sunny'),
        ('rainy', 'Rainy'),
        ('cloudy', 'Cloudy'),
        ('stormy', 'Stormy'),
        ('snowy', 'Snowy'),
        ('hot', 'Hot'),
        ('cold', 'Cold'),
        ('humid', 'Humid'),
    ]
    
    date = models.DateField()
    location = models.CharField(max_length=100, default='Store Location')
    
    # Weather metrics
    temperature_avg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temperature_min = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temperature_max = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    humidity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rainfall = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Weather condition
    condition = models.CharField(max_length=20, choices=WEATHER_CONDITIONS, blank=True)
    
    # Weather impact on sales (calculated)
    sales_impact_score = models.DecimalField(max_digits=4, decimal_places=2, default=1.0,
                                           help_text="Sales multiplier based on weather")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['date', 'location']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.date} - {self.condition} ({self.temperature_avg}°C)"
    
    @classmethod
    def get_weather_impact_for_product(cls, product, date):
        """Get weather impact multiplier for a specific product and date"""
        try:
            weather = cls.objects.get(date=date)
            if product.weather_dependent:
                return weather.sales_impact_score
        except cls.DoesNotExist:
            pass
        return 1.0  # No weather impact
