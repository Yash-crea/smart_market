from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Category, Product, SmartProducts, Cart, CartItem, Order, OrderItem, 
    Payment, Reviews, SeasonalSalesData, ProductRecommendationLog, 
    MLForecastModel, ForecastPrediction, WeatherData, Notification
)
from datetime import datetime, timedelta
from django.utils import timezone


# ============= USER & AUTH SERIALIZERS =============

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'date_joined', 'is_active']
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    orders_count = serializers.SerializerMethodField()
    cart_items = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'orders_count', 'cart_items']
        read_only_fields = ['id', 'username', 'date_joined']
    
    def get_orders_count(self, obj):
        return obj.orders.count()
    
    def get_cart_items(self, obj):
        try:
            return obj.cart.total_items
        except:
            return 0


# ============= PRODUCT SERIALIZERS =============

class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'products_count']
        
    def get_products_count(self, obj):
        return obj.products.count()


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_in_stock = serializers.SerializerMethodField()
    price_formatted = serializers.SerializerMethodField()
    needs_restock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'price_formatted', 'category', 
            'category_name', 'stock_quantity', 'is_in_stock', 'in_stock',
            'is_promotional', 'image_url', 'peak_season', 'festival_association',
            'weekend_boost', 'predicted_demand_7d', 'predicted_demand_30d',
            'forecast_accuracy', 'promotion_lift', 'created_at', 'updated_at',
            'needs_restock'
        ]
    
    def get_is_in_stock(self, obj):
        return obj.stock_quantity > 0 if obj.stock_quantity else False
    
    def get_price_formatted(self, obj):
        return f"₹{obj.price:.2f}"
        
    def get_needs_restock(self, obj):
        return obj.needs_restock()


class SmartProductSerializer(serializers.ModelSerializer):
    is_in_stock = serializers.SerializerMethodField()
    price_formatted = serializers.SerializerMethodField()
    needs_restock = serializers.SerializerMethodField()
    current_season_multiplier = serializers.SerializerMethodField()
    
    class Meta:
        model = SmartProducts
        fields = [
            'id', 'name', 'description', 'price', 'price_formatted', 'category',
            'stock_quantity', 'is_in_stock', 'is_promotional', 'image_url',
            'peak_season', 'festival_association', 'weekend_boost',
            'predicted_demand_7d', 'predicted_demand_30d', 'forecast_accuracy',
            'promotion_lift', 'created_at', 'updated_at', 'needs_restock',
            'current_season_multiplier'
        ]
    
    def get_is_in_stock(self, obj):
        return obj.stock_quantity > 0 if obj.stock_quantity else False
    
    def get_price_formatted(self, obj):
        return f"₹{obj.price:.2f}"
        
    def get_needs_restock(self, obj):
        return obj.needs_restock()
        
    def get_current_season_multiplier(self, obj):
        return obj.get_current_season_multiplier()


class ProductRecommendationSerializer(serializers.ModelSerializer):
    recommendation_reason = serializers.CharField(read_only=True)
    recommendation_type = serializers.CharField(read_only=True)
    recommendation_score = serializers.FloatField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'category_name',
            'stock_quantity', 'image_url', 'weekend_boost', 'peak_season',
            'predicted_demand_7d', 'recommendation_reason', 
            'recommendation_type', 'recommendation_score'
        ]


class SmartProductRecommendationSerializer(serializers.ModelSerializer):
    recommendation_reason = serializers.CharField(read_only=True)
    recommendation_type = serializers.CharField(read_only=True)
    recommendation_score = serializers.FloatField(read_only=True)
    
    class Meta:
        model = SmartProducts
        fields = [
            'id', 'name', 'description', 'price', 'category',
            'stock_quantity', 'image_url', 'weekend_boost', 'peak_season',
            'predicted_demand_7d', 'recommendation_reason', 
            'recommendation_type', 'recommendation_score'
        ]


# ============= CART & ORDER SERIALIZERS =============

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'smart_product', 'quantity', 'product_name', 'unit_price', 'subtotal', 'added_at']
        
    def get_product_name(self, obj):
        return obj.product_name
        
    def get_unit_price(self, obj):
        return float(obj.unit_price)
        
    def get_subtotal(self, obj):
        return float(obj.subtotal)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'user_username', 'items', 'total_amount', 'total_items', 'created_at', 'updated_at']
        
    def get_total_amount(self, obj):
        return float(obj.total_amount)
        
    def get_total_items(self, obj):
        return obj.total_items


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'unit_price', 'quantity', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user_username', 'order_number', 'status', 'customer_name',
            'customer_email', 'customer_phone', 'shipping_address', 'shipping_city',
            'subtotal', 'tax_amount', 'shipping_cost', 'total_amount',
            'created_at', 'updated_at', 'items'
        ]


# ============= MACHINE LEARNING SERIALIZERS =============

class MLForecastModelSerializer(serializers.ModelSerializer):
    predictions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MLForecastModel
        fields = [
            'id', 'name', 'model_type', 'forecast_type', 'parameters',
            'features_used', 'accuracy_score', 'mae', 'rmse', 'mape',
            'is_active', 'last_trained', 'next_retrain_date',
            'model_file_path', 'created_at', 'updated_at', 'predictions_count'
        ]
        
    def get_predictions_count(self, obj):
        return obj.predictions.count()


class ForecastPredictionSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source='model.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True, allow_null=True)
    smart_product_name = serializers.CharField(source='smart_product.name', read_only=True, allow_null=True)
    
    class Meta:
        model = ForecastPrediction
        fields = [
            'id', 'model_name', 'product_name', 'smart_product_name',
            'prediction_date', 'target_date', 'horizon', 'predicted_value',
            'confidence_interval_lower', 'confidence_interval_upper',
            'confidence_score', 'actual_value', 'prediction_error',
            'is_accurate', 'context_data', 'created_at'
        ]


class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = [
            'id', 'date', 'location', 'temperature_avg', 'temperature_min',
            'temperature_max', 'humidity', 'rainfall', 'wind_speed',
            'condition', 'sales_impact_score', 'created_at'
        ]


class SeasonalSalesDataSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True, allow_null=True)
    smart_product_name = serializers.CharField(source='smart_product.name', read_only=True, allow_null=True)
    
    class Meta:
        model = SeasonalSalesData
        fields = [
            'id', 'product_name', 'smart_product_name', 'year', 'month',
            'season', 'week_of_year', 'is_weekend', 'is_festival_period',
            'festival_name', 'total_sales', 'units_sold', 'average_daily_sales',
            'performance_score', 'created_at', 'updated_at'
        ]


class ProductRecommendationLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True, allow_null=True)
    smart_product_name = serializers.CharField(source='smart_product.name', read_only=True, allow_null=True)
    
    class Meta:
        model = ProductRecommendationLog
        fields = [
            'id', 'user_username', 'product_name', 'smart_product_name',
            'recommendation_type', 'context_data', 'was_viewed',
            'was_added_to_cart', 'was_purchased', 'recommended_at', 'last_interaction'
        ]


# ============= NOTIFICATION SERIALIZERS =============

class NotificationSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='recipient_user.username', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user_username', 'notification_type', 'title', 'message',
            'related_order', 'is_read', 'created_at'
        ]


# ============= ANALYTICS SERIALIZERS =============

class RecommendationAnalyticsSerializer(serializers.Serializer):
    total_recommendations = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_cart_adds = serializers.IntegerField()
    total_purchases = serializers.IntegerField()
    view_rate = serializers.FloatField()
    cart_conversion_rate = serializers.FloatField()
    purchase_conversion_rate = serializers.FloatField()


class SalesAnalyticsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_selling_products = serializers.ListField()
    seasonal_trends = serializers.DictField()


class MLPredictionInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_type = serializers.ChoiceField(choices=[('regular', 'Regular Product'), ('smart', 'Smart Product')])
    horizon = serializers.ChoiceField(choices=[('1d', '1 Day'), ('7d', '7 Days'), ('30d', '30 Days'), ('90d', '90 Days')])
    include_weather = serializers.BooleanField(default=False)
    include_seasonal = serializers.BooleanField(default=True)


class BulkRecommendationSerializer(serializers.Serializer):
    algorithm_type = serializers.ChoiceField(choices=[
        ('seasonal', 'Seasonal'),
        ('weather', 'Weather-based'),
        ('trending', 'Trending'),
        ('discount', 'Discount'),
        ('hybrid', 'Hybrid')
    ], default='hybrid')
    limit = serializers.IntegerField(min_value=1, max_value=50, default=10)
    user_id = serializers.IntegerField(required=False)
    include_context = serializers.BooleanField(default=True)


class InteractionLogSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_type = serializers.ChoiceField(choices=[('regular', 'Regular Product'), ('smart', 'Smart Product')])
    interaction_type = serializers.ChoiceField(choices=[('view', 'View'), ('add_to_cart', 'Add to Cart'), ('purchase', 'Purchase')])
    recommendation_type = serializers.CharField(required=False)