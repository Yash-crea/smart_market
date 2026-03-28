from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta
import json
import pandas as pd

from .models import (
    Category, Product, SmartProducts, Cart, CartItem, Order, OrderItem,
    Payment, Reviews, SeasonalSalesData, ProductRecommendationLog,
    MLForecastModel, ForecastPrediction, WeatherData, Notification
)
from .serializers import (
    UserSerializer, UserProfileSerializer, CategorySerializer, ProductSerializer,
    SmartProductSerializer, ProductRecommendationSerializer, SmartProductRecommendationSerializer,
    CartSerializer, CartItemSerializer, OrderSerializer, OrderItemSerializer,
    MLForecastModelSerializer, ForecastPredictionSerializer, WeatherDataSerializer,
    SeasonalSalesDataSerializer, ProductRecommendationLogSerializer,
    NotificationSerializer, RecommendationAnalyticsSerializer, SalesAnalyticsSerializer,
    MLPredictionInputSerializer, BulkRecommendationSerializer, InteractionLogSerializer
)
from .ml_engine import create_ml_engine
from .festival_calendar import FestivalCalendar, get_current_festival_recommendations, get_ml_festival_features
from .cache_utils import (
    CacheManager, get_product_list_key, get_smart_product_list_key, 
    get_recommendations_key, get_category_products_key, get_analytics_key,
    invalidate_product_cache, invalidate_recommendations_cache, get_cache_timeout
)


# ============= AUTHENTICATION VIEWS =============

class CustomAuthToken(ObtainAuthToken):
    """Enhanced authentication with user details"""
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username,
            'is_staff': user.is_staff
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """User registration endpoint"""
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============= PRODUCT VIEWSETS =============

class CategoryViewSet(viewsets.ModelViewSet):
    """Category CRUD operations"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        """Allow read for anyone, require staff for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get all products in this category with caching"""
        category = self.get_object()
        
        # Try to get from cache first
        cache_key = get_category_products_key(category.id)
        cached_data = CacheManager.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)
        
        # If not in cache, fetch from database
        products = category.products.filter(in_stock=True)
        regular_serializer = ProductSerializer(products, many=True)
        
        # Also get smart products in this category
        smart_products = SmartProducts.objects.filter(
            category=category.name, 
            stock_quantity__gt=0
        )
        smart_serializer = SmartProductSerializer(smart_products, many=True)
        
        response_data = {
            'regular_products': regular_serializer.data,
            'smart_products': smart_serializer.data,
            'total_count': len(regular_serializer.data) + len(smart_serializer.data),
            'cached': False,
            'category_name': category.name
        }
        
        # Cache the response data
        CacheManager.set(cache_key, response_data, get_cache_timeout('PRODUCTS'))
        
        return Response(response_data)


class ProductViewSet(viewsets.ModelViewSet):
    """Product CRUD operations with ML features and caching"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        """Allow read for anyone, require staff for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    def list(self, request, *args, **kwargs):
        """List products with caching support"""
        # Extract query parameters for cache key generation
        category = request.query_params.get('category', None)
        min_price = request.query_params.get('min_price', None)
        max_price = request.query_params.get('max_price', None)
        in_stock_only = request.query_params.get('in_stock', 'false') == 'true'
        search = request.query_params.get('search', None)
        page = int(request.query_params.get('page', 1))
        
        # Generate cache key  
        cache_key = get_product_list_key(
            category_id=category,
            search=search,
            in_stock_only=in_stock_only,
            page=page
        )
        
        # Try to get from cache
        cached_data = CacheManager.get(cache_key)
        if cached_data is not None:
            cached_data['cached'] = True
            return Response(cached_data)
        
        # Get filtered queryset
        queryset = self.get_queryset()
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            
            # Cache the paginated response
            response_data = paginated_response.data
            response_data['cached'] = False
            response_data['cache_key'] = cache_key
            CacheManager.set(cache_key, response_data, get_cache_timeout('PRODUCTS'))
            
            return paginated_response
        
        # Non-paginated response
        serializer = self.get_serializer(queryset, many=True)
        response_data = {
            'results': serializer.data,
            'count': len(serializer.data),
            'cached': False,
            'cache_key': cache_key
        }
        
        # Cache the response
        CacheManager.set(cache_key, response_data, get_cache_timeout('PRODUCTS'))
        
        return Response(response_data)
    
    def get_queryset(self):
        queryset = Product.objects.all()
        
        # Filtering
        category = self.request.query_params.get('category', None)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        in_stock = self.request.query_params.get('in_stock', None)
        search = self.request.query_params.get('search', None)
        
        if category:
            queryset = queryset.filter(category__name__icontains=category)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if in_stock == 'true':
            queryset = queryset.filter(stock_quantity__gt=0)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
            
        return queryset
    
    def perform_create(self, serializer):
        """Create product and invalidate cache"""
        instance = serializer.save()
        invalidate_product_cache(
            product_id=instance.id,
            category_id=instance.category.id if instance.category else None
        )
    
    def perform_update(self, serializer):
        """Update product and invalidate cache"""
        instance = serializer.save()
        invalidate_product_cache(
            product_id=instance.id,
            category_id=instance.category.id if instance.category else None
        )
    
    def perform_destroy(self, instance):
        """Delete product and invalidate cache"""
        product_id = instance.id
        category_id = instance.category.id if instance.category else None
        instance.delete()
        invalidate_product_cache(
            product_id=product_id,
            category_id=category_id
        )
    
    @action(detail=True, methods=['post'])
    def update_prediction(self, request, pk=None):
        """Update ML predictions for a product"""
        product = self.get_object()
        demand_7d = request.data.get('predicted_demand_7d', 0)
        demand_30d = request.data.get('predicted_demand_30d', 0)
        revenue_30d = request.data.get('predicted_revenue_30d', 0)
        accuracy = request.data.get('forecast_accuracy', 0)
        
        product.update_ml_predictions(demand_7d, demand_30d, revenue_30d, accuracy)
        
        return Response({
            'message': 'Predictions updated successfully',
            'predictions': {
                'demand_7d': product.predicted_demand_7d,
                'demand_30d': product.predicted_demand_30d,
                'revenue_30d': float(product.predicted_revenue_30d),
                'accuracy': float(product.forecast_accuracy)
            }
        })
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock"""
        low_stock_products = Product.objects.filter(
            stock_quantity__lte=F('reorder_point')
        ).exclude(stock_quantity__isnull=True)
        
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response({
            'products': serializer.data,
            'count': len(serializer.data)
        })
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending products based on ML predictions"""
        trending_products = Product.objects.filter(
            predicted_demand_7d__gt=50
        ).order_by('-predicted_demand_7d')[:20]
        
        serializer = self.get_serializer(trending_products, many=True)
        return Response({
            'products': serializer.data,
            'generated_at': timezone.now()
        })


class SmartProductViewSet(viewsets.ModelViewSet):
    """Smart Products with enhanced ML features and caching"""
    queryset = SmartProducts.objects.all()
    serializer_class = SmartProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        """Allow read for anyone, require staff for write operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    def list(self, request, *args, **kwargs):
        """List smart products with caching support"""
        # Extract query parameters for cache key generation
        category = request.query_params.get('category', None)
        season = request.query_params.get('season', None)
        festival = request.query_params.get('festival', None)
        in_stock_only = request.query_params.get('in_stock', 'false') == 'true'
        page = int(request.query_params.get('page', 1))
        
        # Generate cache key
        cache_key = get_smart_product_list_key(
            category=category,
            season=season,
            festival=festival,
            in_stock_only=in_stock_only,
            page=page
        )
        
        # Try to get from cache
        cached_data = CacheManager.get(cache_key)
        if cached_data is not None:
            cached_data['cached'] = True
            return Response(cached_data)
        
        # Get filtered queryset
        queryset = self.get_queryset()
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            
            # Cache the paginated response
            response_data = paginated_response.data
            response_data['cached'] = False
            response_data['cache_key'] = cache_key
            CacheManager.set(cache_key, response_data, get_cache_timeout('PRODUCTS'))
            
            return paginated_response
        
        # Non-paginated response
        serializer = self.get_serializer(queryset, many=True)
        response_data = {
            'results': serializer.data,
            'count': len(serializer.data),
            'cached': False,
            'cache_key': cache_key
        }
        
        # Cache the response
        CacheManager.set(cache_key, response_data, get_cache_timeout('PRODUCTS'))
        
        return Response(response_data)
    
    def get_queryset(self):
        queryset = SmartProducts.objects.all()
        
        # Filtering
        category = self.request.query_params.get('category', None)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        in_stock = self.request.query_params.get('in_stock', None)
        search = self.request.query_params.get('search', None)
        season = self.request.query_params.get('season', None)
        festival = self.request.query_params.get('festival', None)
        
        if category:
            queryset = queryset.filter(category__icontains=category)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if in_stock == 'true':
            queryset = queryset.filter(stock_quantity__gt=0)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        if season:
            queryset = queryset.filter(peak_season=season)
        if festival:
            queryset = queryset.filter(festival_association=festival)
            
        return queryset
    
    def perform_create(self, serializer):
        """Create smart product and invalidate cache"""
        instance = serializer.save()
        invalidate_product_cache(product_id=instance.id)
        invalidate_recommendations_cache()  # Smart products affect recommendations
    
    def perform_update(self, serializer):
        """Update smart product and invalidate cache"""
        instance = serializer.save()
        invalidate_product_cache(product_id=instance.id)
        invalidate_recommendations_cache()  # Smart products affect recommendations
    
    def perform_destroy(self, instance):
        """Delete smart product and invalidate cache"""
        product_id = instance.id
        instance.delete()
        invalidate_product_cache(product_id=product_id)
        invalidate_recommendations_cache()  # Smart products affect recommendations
    
    @action(detail=False, methods=['get'])
    def seasonal(self, request):
        """Get seasonal products for current season with caching"""
        current_season = self._get_current_season()
        
        # Try cache first
        cache_key = get_smart_product_list_key(
            season=current_season,
            in_stock_only=True
        )
        cached_data = CacheManager.get(cache_key)
        
        if cached_data is not None:
            cached_data['cached'] = True
            return Response(cached_data)
        
        seasonal_products = SmartProducts.objects.filter(
            peak_season=current_season,
            stock_quantity__gt=0
        ).order_by('-seasonal_priority')[:20]
        
        serializer = self.get_serializer(seasonal_products, many=True)
        response_data = {
            'products': serializer.data,
            'current_season': current_season,
            'count': len(serializer.data),
            'cached': False
        }
        
        # Cache the response
        CacheManager.set(cache_key, response_data, get_cache_timeout('PRODUCTS'))
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def festival(self, request):
        """Get festival products for upcoming festivals with caching"""
        upcoming_festivals = self._get_upcoming_festivals()
        
        # Try cache first
        cache_key = get_smart_product_list_key(
            festival=','.join(upcoming_festivals),
            in_stock_only=True
        )
        cached_data = CacheManager.get(cache_key)
        
        if cached_data is not None:
            cached_data['cached'] = True
            return Response(cached_data)
        
        festival_products = SmartProducts.objects.filter(
            festival_association__in=upcoming_festivals,
            stock_quantity__gt=0
        ).order_by('-festival_sales_boost')[:20]
        
        serializer = self.get_serializer(festival_products, many=True)
        response_data = {
            'products': serializer.data,
            'upcoming_festivals': upcoming_festivals,
            'count': len(serializer.data),
            'cached': False
        }
        
        # Cache the response
        CacheManager.set(cache_key, response_data, get_cache_timeout('PRODUCTS'))
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def promotional(self, request):
        """Get products currently on promotion with caching"""
        # Try cache first
        cache_key = 'smart_products:promotional:in_stock'
        cached_data = CacheManager.get(cache_key)
        
        if cached_data is not None:
            cached_data['cached'] = True
            return Response(cached_data)
        
        promotional_products = SmartProducts.objects.filter(
            is_promotional=True,
            stock_quantity__gt=0
        ).order_by('-promotion_lift')[:20]
        
        serializer = self.get_serializer(promotional_products, many=True)
        response_data = {
            'products': serializer.data,
            'count': len(serializer.data),
            'cached': False
        }
        
        # Cache the response (shorter timeout for promotions)
        CacheManager.set(cache_key, response_data, 180)  # 3 minutes for promotions
        
        return Response(response_data)
    
    def _get_current_season(self):
        current_month = datetime.now().month
        season_map = {
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'monsoon', 10: 'monsoon', 11: 'monsoon'
        }
        return season_map.get(current_month, 'all_year')
    
    def _get_upcoming_festivals(self):
        """Get upcoming festivals using dynamic festival calendar"""
        festival_calendar = FestivalCalendar()
        current_date = timezone.now().date()
        date_info = festival_calendar.get_current_date_info(current_date)
        
        upcoming_festivals = []
        
        # Current month festivals
        if date_info['festivals_this_month']:
            upcoming_festivals.extend(date_info['festivals_this_month'])
        
        # Next festival within 30 days
        if date_info['next_festival'] and date_info['days_to_next_festival'] <= 30:
            if date_info['next_festival'] not in upcoming_festivals:
                upcoming_festivals.append(date_info['next_festival'])
        
        return upcoming_festivals or ['general']  # fallback to general if no festivals


# ============= CART & ORDER VIEWSETS =============

class CartViewSet(viewsets.ModelViewSet):
    """Shopping cart management"""
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart"""
        product_id = request.data.get('product_id')
        product_type = request.data.get('product_type', 'smart')  # 'smart' or 'regular'
        quantity = int(request.data.get('quantity', 1))
        
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        if product_type == 'regular':
            try:
                product = Product.objects.get(id=product_id)
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    defaults={'quantity': quantity}
                )
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=404)
        else:
            try:
                smart_product = SmartProducts.objects.get(id=product_id)
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    smart_product=smart_product,
                    defaults={'quantity': quantity}
                )
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()
            except SmartProducts.DoesNotExist:
                return Response({'error': 'Product not found'}, status=404)
        
        serializer = CartSerializer(cart)
        return Response({
            'message': 'Item added to cart successfully',
            'cart': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Remove item from cart"""
        item_id = request.data.get('item_id')
        
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            
            serializer = CartSerializer(cart)
            return Response({
                'message': 'Item removed successfully',
                'cart': serializer.data
            })
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({'error': 'Item not found'}, status=404)
    
    @action(detail=False, methods=['post'])
    def update_quantity(self, request):
        """Update item quantity in cart"""
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))
        
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.quantity = quantity
            cart_item.save()
            
            serializer = CartSerializer(cart)
            return Response({
                'message': 'Quantity updated successfully',
                'cart': serializer.data
            })
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return Response({'error': 'Item not found'}, status=404)
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear entire cart"""
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
            
            serializer = CartSerializer(cart)
            return Response({
                'message': 'Cart cleared successfully',
                'cart': serializer.data
            })
        except Cart.DoesNotExist:
            return Response({'message': 'Cart is already empty'})


class OrderViewSet(viewsets.ModelViewSet):
    """Order management with analytics"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_from_cart(self, request):
        """Create order from current cart"""
        try:
            cart = Cart.objects.get(user=request.user)
            if not cart.items.exists():
                return Response({'error': 'Cart is empty'}, status=400)
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                customer_name=request.data.get('customer_name', request.user.get_full_name()),
                customer_email=request.data.get('customer_email', request.user.email),
                customer_phone=request.data.get('customer_phone', ''),
                shipping_address=request.data.get('shipping_address', ''),
                shipping_city=request.data.get('shipping_city', ''),
                shipping_postal_code=request.data.get('shipping_postal_code', ''),
                subtotal=cart.total_amount,
                tax_amount=cart.total_amount * 0.18,  # 18% tax
                shipping_cost=0,  # Free shipping
                total_amount=cart.total_amount * 1.18
            )
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    smart_product=cart_item.smart_product,
                    product_name=cart_item.product_name,
                    unit_price=cart_item.unit_price,
                    quantity=cart_item.quantity,
                    subtotal=cart_item.subtotal
                )
            
            # Clear cart
            cart.items.all().delete()
            
            serializer = OrderSerializer(order)
            return Response({
                'message': 'Order created successfully',
                'order': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=404)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get order analytics - staff sees all, customers see only their own"""
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        if request.user.is_staff:
            orders = Order.objects.filter(created_at__gte=start_date)
        else:
            orders = Order.objects.filter(created_at__gte=start_date, user=request.user)
        
        analytics = {
            'total_orders': orders.count(),
            'total_revenue': orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'average_order_value': orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0,
            'orders_by_status': orders.values('status').annotate(count=Count('id'))
        }
        
        serializer = SalesAnalyticsSerializer(analytics)
        return Response(serializer.data)


# ============= MACHINE LEARNING VIEWSETS =============

class MLForecastModelViewSet(viewsets.ModelViewSet):
    """ML Model management"""
    queryset = MLForecastModel.objects.all()
    serializer_class = MLForecastModelSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def train(self, request, pk=None):
        """Trigger model training"""
        model = self.get_object()
        
        # This would integrate with your ML training pipeline
        model.last_trained = timezone.now()
        model.next_retrain_date = timezone.now() + timedelta(days=7)
        model.save()
        
        return Response({
            'message': f'Training started for model {model.name}',
            'model_id': model.id,
            'last_trained': model.last_trained
        })
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get model performance metrics"""
        model = self.get_object()
        
        # Get recent predictions and accuracy
        recent_predictions = model.predictions.filter(
            prediction_date__gte=timezone.now() - timedelta(days=30)
        )
        
        accuracy_stats = recent_predictions.aggregate(
            avg_error=Avg('prediction_error'),
            accurate_count=Count('id', filter=Q(is_accurate=True)),
            total_count=Count('id')
        )
        
        return Response({
            'model': MLForecastModelSerializer(model).data,
            'recent_accuracy': accuracy_stats['accurate_count'] / max(accuracy_stats['total_count'], 1) * 100,
            'average_error': accuracy_stats['avg_error'] or 0,
            'predictions_count': accuracy_stats['total_count']
        })


class ForecastPredictionViewSet(viewsets.ModelViewSet):
    """Forecast predictions management"""
    queryset = ForecastPrediction.objects.all()
    serializer_class = ForecastPredictionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ForecastPrediction.objects.all()
        
        # Filtering
        model_id = self.request.query_params.get('model_id', None)
        product_id = self.request.query_params.get('product_id', None)
        horizon = self.request.query_params.get('horizon', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if model_id:
            queryset = queryset.filter(model_id=model_id)
        if product_id:
            queryset = queryset.filter(
                Q(product_id=product_id) | Q(smart_product_id=product_id)
            )
        if horizon:
            queryset = queryset.filter(horizon=horizon)
        if start_date:
            queryset = queryset.filter(prediction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(prediction_date__lte=end_date)
            
        return queryset.order_by('-prediction_date')
    
    @action(detail=False, methods=['post'])
    def generate_prediction(self, request):
        """Generate new prediction for a product"""
        serializer = MLPredictionInputSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            product_type = serializer.validated_data['product_type']
            horizon = serializer.validated_data['horizon']
            
            # This would integrate with your ML prediction pipeline
            # For now, return mock prediction
            prediction_value = 100 + (hash(str(product_id)) % 100)  # Mock prediction
            
            return Response({
                'product_id': product_id,
                'product_type': product_type,
                'horizon': horizon,
                'predicted_value': prediction_value,
                'confidence_score': 85,
                'generated_at': timezone.now()
            })
        
        return Response(serializer.errors, status=400)


class WeatherDataViewSet(viewsets.ModelViewSet):
    """Weather data for weather-based recommendations"""
    queryset = WeatherData.objects.all()
    serializer_class = WeatherDataSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current weather data"""
        try:
            latest_weather = WeatherData.objects.latest('date')
            serializer = WeatherDataSerializer(latest_weather)
            return Response(serializer.data)
        except WeatherData.DoesNotExist:
            return Response({'message': 'No weather data available'}, status=404)
    
    @action(detail=False, methods=['get'])
    def forecast(self, request):
        """Get weather forecast for next 7 days"""
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=days)
        
        weather_data = WeatherData.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')
        
        serializer = WeatherDataSerializer(weather_data, many=True)
        return Response({
            'forecast': serializer.data,
            'days': days
        })


class SeasonalSalesDataViewSet(viewsets.ModelViewSet):
    """Seasonal sales analytics"""
    queryset = SeasonalSalesData.objects.all()
    serializer_class = SeasonalSalesDataSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = SeasonalSalesData.objects.all()
        
        # Filtering
        year = self.request.query_params.get('year', None)
        month = self.request.query_params.get('month', None)
        season = self.request.query_params.get('season', None)
        festival = self.request.query_params.get('festival', None)
        
        if year:
            queryset = queryset.filter(year=year)
        if month:
            queryset = queryset.filter(month=month)
        if season:
            queryset = queryset.filter(season=season)
        if festival:
            queryset = queryset.filter(festival_name=festival)
            
        return queryset.order_by('-year', '-month')
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get seasonal sales trends"""
        year = int(request.query_params.get('year', datetime.now().year))
        
        trends = SeasonalSalesData.objects.filter(year=year).values(
            'season', 'month'
        ).annotate(
            total_sales=Sum('total_sales'),
            total_units=Sum('units_sold'),
            avg_performance=Avg('performance_score')
        ).order_by('month')
        
        return Response({
            'year': year,
            'trends': list(trends)
        })


# ============= RECOMMENDATION & ANALYTICS APIs =============

@api_view(['GET'])
@permission_classes([AllowAny])
def get_recommendations(request):
    """Enhanced recommendation API with multiple algorithms and caching"""
    serializer = BulkRecommendationSerializer(data=request.query_params)
    if serializer.is_valid():
        algorithm_type = serializer.validated_data['algorithm_type']
        limit = serializer.validated_data['limit']
        include_context = serializer.validated_data['include_context']
        
        # Generate cache key based on parameters
        user_id = request.user.id if request.user.is_authenticated else None
        cache_key = get_recommendations_key(
            algorithm_type=algorithm_type,
            limit=limit,
            user_id=user_id,
            include_context=include_context
        )
        
        # Try to get from cache first
        cached_data = CacheManager.get(cache_key)
        if cached_data is not None:
            cached_data['cached'] = True
            cached_data['cache_hit_time'] = timezone.now()
            return Response(cached_data)
        
        # Generate fresh recommendations
        recommendations = []
        context = {}
        
        if algorithm_type == 'seasonal':
            recommendations = _get_seasonal_recommendations(limit)
        elif algorithm_type == 'weather':
            recommendations = _get_weather_recommendations(limit)
        elif algorithm_type == 'trending':
            recommendations = _get_trending_recommendations(limit)
        elif algorithm_type == 'discount':
            recommendations = _get_discount_recommendations(limit)
        else:  # hybrid
            recommendations = _get_hybrid_recommendations(limit)
        
        if include_context:
            context = {
                'current_season': _get_current_season(),
                'upcoming_festivals': _get_upcoming_festivals(),
                'is_weekend': datetime.now().weekday() >= 5,
                'weather_condition': _get_current_weather()
            }
        
        response_data = {
            'algorithm_type': algorithm_type,
            'recommendations': recommendations,
            'context': context,
            'generated_at': timezone.now(),
            'total_count': len(recommendations),
            'cached': False,
            'cache_key': cache_key
        }
        
        # Cache the response
        CacheManager.set(cache_key, response_data, get_cache_timeout('RECOMMENDATIONS'))
        
        return Response(response_data)
    
    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_interaction(request):
    """Log user interaction with products for ML learning"""
    serializer = InteractionLogSerializer(data=request.data)
    if serializer.is_valid():
        product_id = serializer.validated_data['product_id']
        product_type = serializer.validated_data['product_type']
        interaction_type = serializer.validated_data['interaction_type']
        recommendation_type = serializer.validated_data.get('recommendation_type', 'unknown')
        
        # Find the product
        if product_type == 'smart':
            try:
                smart_product = SmartProducts.objects.get(id=product_id)
                log_entry, created = ProductRecommendationLog.objects.get_or_create(
                    user=request.user,
                    smart_product=smart_product,
                    defaults={
                        'recommendation_type': recommendation_type,
                        'context_data': {'logged_at': str(timezone.now())}
                    }
                )
            except SmartProducts.DoesNotExist:
                return Response({'error': 'Product not found'}, status=404)
        else:
            try:
                product = Product.objects.get(id=product_id)
                log_entry, created = ProductRecommendationLog.objects.get_or_create(
                    user=request.user,
                    product=product,
                    defaults={
                        'recommendation_type': recommendation_type,
                        'context_data': {'logged_at': str(timezone.now())}
                    }
                )
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=404)
        
        # Update interaction flags
        if interaction_type == 'view':
            log_entry.was_viewed = True
        elif interaction_type == 'add_to_cart':
            log_entry.was_added_to_cart = True
        elif interaction_type == 'purchase':
            log_entry.was_purchased = True
        
        log_entry.save()
        
        return Response({
            'message': 'Interaction logged successfully',
            'log_id': log_entry.id
        })
    
    return Response(serializer.errors, status=400)


# ============= ENHANCED ML-BASED CONTEXTUAL RECOMMENDATIONS =============

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  
def get_contextual_recommendations(request):
    """
    🤖 Enhanced ML-based contextual recommendations using historical & seasonal data
    
    This endpoint leverages your sophisticated ML model that's trained on:
    - Historical sales patterns and seasonal trends
    - Weather data correlations and festival impacts  
    - User behavior patterns and purchase history
    - Real-time contextual factors (time, season, festivals)
    
    Example Usage:
    GET /api/contextual-recommendations/?algorithm=hybrid_ml&limit=10
    POST /api/contextual-recommendations/ 
    {
        "algorithm": "hybrid_ml",
        "limit": 10,
        "context": {
            "location": "Mumbai",
            "occasion": "birthday_party"
        }
    }
    """
    from .ml_recommendations import ContextualRecommendationEngine
    
    # Parse request parameters
    algorithm = request.query_params.get('algorithm', 'hybrid_ml') if request.method == 'GET' else request.data.get('algorithm', 'hybrid_ml')
    limit = int(request.query_params.get('limit', 10)) if request.method == 'GET' else int(request.data.get('limit', 10))
    
    # Additional context from request body (for POST requests)
    additional_context = request.data.get('context', {}) if request.method == 'POST' else {}
    
    # Validate algorithm type
    valid_algorithms = ['ml_seasonal', 'ml_weather', 'user_behavior', 'hybrid_ml']
    if algorithm not in valid_algorithms:
        return Response({
            'error': f'Invalid algorithm. Must be one of: {valid_algorithms}'
        }, status=400)
    
    # Generate cache key for this specific request
    user_id = request.user.id if request.user.is_authenticated else None
    cache_key = get_recommendations_key(
        algorithm_type=f'contextual_{algorithm}',
        limit=limit,
        user_id=user_id,
        include_context=True
    )
    
    # Try cache first
    cached_data = CacheManager.get(cache_key)
    if cached_data is not None:
        cached_data['cached'] = True
        cached_data['cache_hit_time'] = timezone.now()
        return Response(cached_data)
    
    try:
        # Initialize contextual recommendation engine
        rec_engine = ContextualRecommendationEngine()
        
        # Get user object if authenticated
        user = request.user if request.user.is_authenticated else None
        
        # Generate contextual recommendations using ML model
        result = rec_engine.get_personalized_recommendations(
            user=user,
            context=additional_context,
            algorithm=algorithm,
            limit=limit
        )
        
        # Enhance response with meta-information about ML model 
        result['ml_model_info'] = {
            'uses_historical_data': True,
            'uses_seasonal_patterns': True,
            'uses_weather_correlations': True,
            'uses_festival_calendar': True,
            'uses_user_behavior': user is not None,
            'features_count': 25,  # Number of features in your ML model
            'training_data_sources': [
                'SeasonalSalesData (historical sales)',
                'WeatherData (weather patterns)',
                'OrderItem (purchase history)', 
                'Festival Calendar (festival impacts)',
                'User behavior patterns'
            ]
        }
        
        # Add performance metrics
        result['performance_insights'] = {
            'recommendation_generation_time': f'{(timezone.now() - result["generated_at"]).total_seconds():.2f} seconds',
            'algorithm_used': algorithm,
            'personalization_applied': user is not None,
            'contextual_factors_applied': len(result['context'])
        }
        
        # Cache the result
        result['cached'] = False
        result['cache_key'] = cache_key
        CacheManager.set(cache_key, result, get_cache_timeout('RECOMMENDATIONS'))
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'error': f'Failed to generate contextual recommendations: {str(e)}',
            'algorithm': algorithm,
            'user_authenticated': user is not None,
            'timestamp': timezone.now()
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retrain_ml_model_with_latest_data(request):
    """
    🔄 Retrain ML model with latest historical and seasonal data
    
    This endpoint triggers retraining of your ML models with the most recent:
    - Sales transaction data
    - Seasonal sales patterns
    - Weather correlations
    - Festival impact data
    - User interaction logs
    """
    try:
        # Create ML engine instance
        ml_engine = create_ml_engine()
        
        # Retrain models with latest data
        print("🤖 Retraining ML models with latest contextual data...")
        training_results = ml_engine.train_models()
        
        if training_results:
            # Generate fresh predictions for all products
            print("🔮 Generating fresh predictions with updated models...")
            predictions = ml_engine.batch_predict_all_products()
            
            # Clear recommendation caches to force fresh ML-based recommendations
            invalidate_recommendations_cache()
            
            return Response({
                'success': True,
                'message': 'ML model retrained successfully with latest data',
                'training_results': training_results,
                'predictions_updated': len(predictions),
                'models_trained': list(training_results.keys()),
                'best_model_accuracy': max([result['accuracy'] for result in training_results.values()]),
                'data_sources_used': [
                    'Historical sales (SeasonalSalesData)',
                    'Weather patterns (WeatherData)', 
                    'Purchase behavior (OrderItem)',
                    'Festival calendar data',
                    'Product characteristics'
                ],
                'retrained_at': timezone.now(),
                'next_auto_retrain': timezone.now() + timedelta(days=7)
            })
        else:
            return Response({
                'success': False,
                'message': 'No training data available. Please ensure sales data is populated.',
                'suggestion': 'Add sales transactions and seasonal data before retraining'
            }, status=400)
            
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Failed to retrain ML model'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommendation_analytics(request):
    """Get recommendation performance analytics"""
    days = int(request.query_params.get('days', 30))
    user_id = request.query_params.get('user_id', None)
    
    start_date = timezone.now() - timedelta(days=days)
    
    queryset = ProductRecommendationLog.objects.filter(recommended_at__gte=start_date)
    if user_id and request.user.is_staff:
        queryset = queryset.filter(user_id=user_id)
    elif not request.user.is_staff:
        queryset = queryset.filter(user=request.user)
    
    analytics = queryset.aggregate(
        total_recommendations=Count('id'),
        total_views=Count('id', filter=Q(was_viewed=True)),
        total_cart_adds=Count('id', filter=Q(was_added_to_cart=True)),
        total_purchases=Count('id', filter=Q(was_purchased=True))
    )
    
    # Calculate rates
    total = analytics['total_recommendations'] or 1
    analytics['view_rate'] = (analytics['total_views'] / total) * 100
    analytics['cart_conversion_rate'] = (analytics['total_cart_adds'] / total) * 100
    analytics['purchase_conversion_rate'] = (analytics['total_purchases'] / total) * 100
    
    serializer = RecommendationAnalyticsSerializer(analytics)
    return Response(serializer.data)


# ============= HELPER FUNCTIONS =============

def _get_seasonal_recommendations(limit):
    current_season = _get_current_season()
    products = SmartProducts.objects.filter(
        peak_season=current_season,
        stock_quantity__gt=0
    ).order_by('-seasonal_priority')[:limit]
    
    recommendations = []
    for product in products:
        recommendations.append({
            'id': product.id,
            'type': 'smart_product',
            'name': product.name,
            'price': float(product.price),
            'score': float(product.seasonal_priority),
            'reason': f"Perfect for {current_season} season"
        })
    
    return recommendations


def _get_weather_recommendations(limit):
    # Mock weather-based recommendations
    weather_products = SmartProducts.objects.filter(
        weather_dependent=True,
        stock_quantity__gt=0
    )[:limit]
    
    recommendations = []
    for product in weather_products:
        recommendations.append({
            'id': product.id,
            'type': 'smart_product',
            'name': product.name,
            'price': float(product.price),
            'score': 80.0,
            'reason': "Great for current weather"
        })
    
    return recommendations


def _get_trending_recommendations(limit):
    products = SmartProducts.objects.filter(
        predicted_demand_7d__gt=40,
        stock_quantity__gt=0
    ).order_by('-predicted_demand_7d')[:limit]
    
    recommendations = []
    for product in products:
        recommendations.append({
            'id': product.id,
            'type': 'smart_product',
            'name': product.name,
            'price': float(product.price),
            'score': float(product.predicted_demand_7d),
            'reason': "Trending this week"
        })
    
    return recommendations


def _get_discount_recommendations(limit):
    products = SmartProducts.objects.filter(
        is_promotional=True,
        stock_quantity__gt=0
    ).order_by('-promotion_lift')[:limit]
    
    recommendations = []
    for product in products:
        discount = (float(product.promotion_lift) - 1.0) * 100
        recommendations.append({
            'id': product.id,
            'type': 'smart_product',
            'name': product.name,
            'price': float(product.price),
            'score': float(product.promotion_lift * 100),
            'reason': f"On sale - {discount:.0f}% off"
        })
    
    return recommendations


def _get_hybrid_recommendations(limit):
    # Combine multiple recommendation types
    seasonal = _get_seasonal_recommendations(limit // 3)
    trending = _get_trending_recommendations(limit // 3)
    discount = _get_discount_recommendations(limit // 3)
    
    all_recs = seasonal + trending + discount
    return sorted(all_recs, key=lambda x: x['score'], reverse=True)[:limit]


def _get_current_season():
    current_month = datetime.now().month
    season_map = {
        12: 'winter', 1: 'winter', 2: 'winter',
        3: 'spring', 4: 'spring', 5: 'spring',
        6: 'summer', 7: 'summer', 8: 'summer',
        9: 'monsoon', 10: 'monsoon', 11: 'monsoon'
    }
    return season_map.get(current_month, 'all_year')


def _get_upcoming_festivals():
    current_month = datetime.now().month
    festivals = []
    
    if current_month == 10:
        festivals.append('diwali')
    elif current_month == 3:
        festivals.append('holi')
    elif current_month == 12:
        festivals.append('christmas')
    
    return festivals


def _get_current_weather():
    try:
        latest_weather = WeatherData.objects.latest('date')
        return latest_weather.condition
    except WeatherData.DoesNotExist:
        return 'unknown'


# ============= CACHE MANAGEMENT APIs =============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cache_stats(request):
    """Get cache statistics and performance metrics"""
    if not request.user.is_staff:
        return Response({'error': 'Staff access required'}, status=403)
    
    from .cache_utils import get_cache_stats
    stats = get_cache_stats()
    
    return Response({
        'cache_stats': stats,
        'generated_at': timezone.now(),
        'cache_status': 'healthy' if 'error' not in stats else 'error'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invalidate_cache(request):
    """Manually invalidate specific cache patterns"""
    if not request.user.is_staff:
        return Response({'error': 'Staff access required'}, status=403)
    
    cache_type = request.data.get('cache_type', 'all')
    
    if cache_type == 'products':
        invalidate_product_cache()
        message = 'Product caches invalidated'
    elif cache_type == 'recommendations':
        invalidate_recommendations_cache()
        message = 'Recommendation caches invalidated'
    elif cache_type == 'all':
        invalidate_product_cache()
        invalidate_recommendations_cache()
        message = 'All caches invalidated'
    else:
        return Response({'error': 'Invalid cache_type'}, status=400)
    
    return Response({
        'message': message,
        'cache_type': cache_type,
        'invalidated_at': timezone.now()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])  
def warm_cache(request):
    """Warm up cache with popular data"""
    if not request.user.is_staff:
        return Response({'error': 'Staff access required'}, status=403)
    
    from .cache_utils import warm_popular_products_cache
    
    try:
        warm_popular_products_cache()
        return Response({
            'message': 'Cache warming completed',
            'warmed_at': timezone.now()
        })
    except Exception as e:
        return Response({
            'error': f'Cache warming failed: {str(e)}',
            'failed_at': timezone.now()
        }, status=500)


# ============= POWER BI INTEGRATION ENDPOINTS =============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def powerbi_demand_forecast_data(request):
    """
    Power BI optimized endpoint for demand forecasting dashboard with dynamic festival context
    Returns structured data for visualization in Power BI
    """
    # Get time range from query params
    days_ahead = int(request.GET.get('days_ahead', 30))
    include_confidence = request.GET.get('include_confidence', 'true').lower() == 'true'
    
    # Get current festival context
    festival_calendar = FestivalCalendar()
    current_date = timezone.now().date()
    festival_info = festival_calendar.get_current_date_info(current_date)
    
    # Prepare data for Power BI
    forecast_data = []
    
    # Regular products
    products = Product.objects.filter(
        predicted_demand_7d__gt=0
    ).select_related('category')
    
    for product in products:
        # Get festival boost for this specific product
        product_data = {'name': product.name, 'category': product.category.name if product.category else 'unknown'}
        festival_features = festival_calendar.get_festival_boost_for_product(product_data)
        
        base_data = {
            'product_id': product.id,
            'product_name': product.name,
            'product_type': 'regular',
            'category': product.category.name if product.category else 'Unknown',
            'current_price': float(product.price),
            'current_stock': product.stock_quantity or 0,
            'predicted_demand_7d': product.predicted_demand_7d,
            'predicted_demand_30d': product.predicted_demand_30d,
            'forecast_accuracy': float(product.forecast_accuracy),
            'last_forecast_update': product.last_forecast_update,
            'trend': product.demand_trend,
            'seasonal_category': product.peak_season,
            'is_weather_dependent': product.weather_dependent,
            'reorder_point': product.reorder_point,
            'needs_restock': product.needs_restock(),
            # Festival context from dynamic calendar
            'festival_boost': festival_features.get('festival_boost', 1.0),
            'festival_intensity': festival_features.get('festival_intensity', 0),
            'current_festivals': festival_info['festivals_this_month'],
            'days_to_next_festival': festival_info['days_to_next_festival'],
            'next_festival': festival_info['next_festival'],
            'is_festival_period': len(festival_info['festivals_this_month']) > 0 or festival_info['days_to_next_festival'] <= 7
        }
        
        if include_confidence:
            # Calculate confidence intervals (simplified approach)
            accuracy = float(product.forecast_accuracy) / 100
            margin_7d = int(product.predicted_demand_7d * (1 - accuracy))
            margin_30d = int(product.predicted_demand_30d * (1 - accuracy))
            
            base_data.update({
                'confidence_lower_7d': max(0, product.predicted_demand_7d - margin_7d),
                'confidence_upper_7d': product.predicted_demand_7d + margin_7d,
                'confidence_lower_30d': max(0, product.predicted_demand_30d - margin_30d),
                'confidence_upper_30d': product.predicted_demand_30d + margin_30d,
            })
        
        forecast_data.append(base_data)
    
    # Smart products
    smart_products = SmartProducts.objects.filter(
        predicted_demand_7d__gt=0
    )
    
    for product in smart_products:
        # Get festival boost for this specific product
        product_data = {'name': product.name, 'category': product.category or 'unknown'}
        festival_features = festival_calendar.get_festival_boost_for_product(product_data)
        
        base_data = {
            'product_id': product.id,
            'product_name': product.name,
            'product_type': 'smart',
            'category': product.category or 'Unknown',
            'current_price': float(product.price),
            'current_stock': product.stock_quantity or 0,
            'predicted_demand_7d': product.predicted_demand_7d,
            'predicted_demand_30d': product.predicted_demand_30d,
            'forecast_accuracy': float(product.forecast_accuracy),
            'last_forecast_update': product.last_forecast_update,
            'trend': product.demand_trend,
            'seasonal_category': product.peak_season,
            'is_weather_dependent': product.weather_dependent,
            'reorder_point': product.reorder_point,
            'needs_restock': product.needs_restock(),
            # Festival context from dynamic calendar
            'festival_boost': festival_features.get('festival_boost', 1.0),
            'festival_intensity': festival_features.get('festival_intensity', 0),
            'current_festivals': festival_info['festivals_this_month'],
            'days_to_next_festival': festival_info['days_to_next_festival'],
            'next_festival': festival_info['next_festival'],
            'is_festival_period': len(festival_info['festivals_this_month']) > 0 or festival_info['days_to_next_festival'] <= 7
        }
        
        if include_confidence:
            accuracy = float(product.forecast_accuracy) / 100
            margin_7d = int(product.predicted_demand_7d * (1 - accuracy))
            margin_30d = int(product.predicted_demand_30d * (1 - accuracy))
            
            base_data.update({
                'confidence_lower_7d': max(0, product.predicted_demand_7d - margin_7d),
                'confidence_upper_7d': product.predicted_demand_7d + margin_7d,
                'confidence_lower_30d': max(0, product.predicted_demand_30d - margin_30d),
                'confidence_upper_30d': product.predicted_demand_30d + margin_30d,
            })
        
        forecast_data.append(base_data)
    
    return Response({
        'timestamp': timezone.now(),
        'data_points': len(forecast_data),
        'forecast_horizon_days': days_ahead,
        'includes_confidence_intervals': include_confidence,
        'festival_calendar_context': {
            'current_date': current_date,
            'active_festivals': [f['name'] for f in festival_info.get('active_festivals', [])],
            'boost_festivals': [f['name'] for f in festival_info.get('boost_active_festivals', [])],
            'next_major_festival': festival_info.get('next_major_festival', {}).get('name', 'None'),
            'season': festival_info.get('season', 'unknown')
        },
        'forecasts': forecast_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def powerbi_sales_analytics_data(request):
    """
    Power BI optimized sales analytics endpoint
    Returns sales data formatted for Power BI dashboards
    """
    # Get date range from query params
    days = int(request.GET.get('days', 30))
    group_by = request.GET.get('group_by', 'day')  # day, week, month
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Get orders data
    orders = Order.objects.filter(
        created_at__gte=start_date
    ).select_related()
    
    # Aggregate by time period
    if group_by == 'day':
        sales_data = orders.extra(
            select={'period': "DATE(created_at)"}
        ).values('period').annotate(
            total_revenue=Sum('total_amount'),
            order_count=Count('id'),
            avg_order_value=Avg('total_amount')
        ).order_by('period')
    elif group_by == 'week':
        sales_data = orders.extra(
            select={'period': "DATE_FORMAT(created_at, '%%Y-%%u')"}
        ).values('period').annotate(
            total_revenue=Sum('total_amount'),
            order_count=Count('id'),
            avg_order_value=Avg('total_amount')
        ).order_by('period')
    else:  # month
        sales_data = orders.extra(
            select={'period': "DATE_FORMAT(created_at, '%%Y-%%m')"}
        ).values('period').annotate(
            total_revenue=Sum('total_amount'),
            order_count=Count('id'),
            avg_order_value=Avg('total_amount')
        ).order_by('period')
    
    # Category breakdown
    category_sales = OrderItem.objects.filter(
        order__created_at__gte=start_date
    ).values(
        'product__category__name'
    ).annotate(
        revenue=Sum(F('quantity') * F('unit_price')),
        units_sold=Sum('quantity')
    ).order_by('-revenue')
    
    # Product performance
    top_products = OrderItem.objects.filter(
        order__created_at__gte=start_date
    ).values(
        'product__name', 'product__id'
    ).annotate(
        revenue=Sum(F('quantity') * F('unit_price')),
        units_sold=Sum('quantity')
    ).order_by('-revenue')[:20]
    
    return Response({
        'timestamp': timezone.now(),
        'date_range': {
            'start_date': start_date,
            'end_date': timezone.now(),
            'days': days
        },
        'grouping': group_by,
        'time_series': list(sales_data),
        'category_breakdown': list(category_sales),
        'top_products': list(top_products),
        'summary': {
            'total_revenue': orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'total_orders': orders.count(),
            'avg_order_value': orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def powerbi_inventory_alerts_data(request):
    """
    Power BI inventory alerts and stock optimization data
    """
    # Stock alerts
    low_stock_products = []
    
    # Regular products
    products = Product.objects.filter(
        stock_quantity__lte=F('reorder_point')
    ).select_related('category')
    
    for product in products:
        low_stock_products.append({
            'product_id': product.id,
            'product_name': product.name,
            'product_type': 'regular',
            'category': product.category.name if product.category else 'Unknown',
            'current_stock': product.stock_quantity or 0,
            'reorder_point': product.reorder_point,
            'predicted_demand_7d': product.predicted_demand_7d,
            'days_until_stockout': max(0, (product.stock_quantity or 0) / max(1, product.predicted_demand_7d / 7)),
            'suggested_reorder_qty': max(product.reorder_point, product.predicted_demand_30d),
            'priority': 'high' if (product.stock_quantity or 0) == 0 else 'medium'
        })
    
    # Smart products
    smart_products = SmartProducts.objects.filter(
        stock_quantity__lte=F('reorder_point')
    )
    
    for product in smart_products:
        low_stock_products.append({
            'product_id': product.id,
            'product_name': product.name,
            'product_type': 'smart',
            'category': product.category or 'Unknown',
            'current_stock': product.stock_quantity or 0,
            'reorder_point': product.reorder_point,
            'predicted_demand_7d': product.predicted_demand_7d,
            'days_until_stockout': max(0, (product.stock_quantity or 0) / max(1, product.predicted_demand_7d / 7)),
            'suggested_reorder_qty': max(product.reorder_point, product.predicted_demand_30d),
            'priority': 'high' if (product.stock_quantity or 0) == 0 else 'medium'
        })
    
    # Sort by priority and days until stockout
    low_stock_products.sort(key=lambda x: (x['priority'], x['days_until_stockout']))
    
    return Response({
        'timestamp': timezone.now(),
        'total_alerts': len(low_stock_products),
        'high_priority_count': len([p for p in low_stock_products if p['priority'] == 'high']),
        'inventory_alerts': low_stock_products
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def powerbi_generate_ml_predictions(request):
    """
    Trigger ML prediction generation for Power BI real-time updates
    """
    try:
        ml_engine = create_ml_engine()
        
        # Generate predictions for all products
        predictions = ml_engine.batch_predict_all_products()
        
        return Response({
            'success': True,
            'timestamp': timezone.now(),
            'predictions_generated': len(predictions),
            'message': 'ML predictions updated successfully',
            'next_scheduled_run': timezone.now() + timedelta(hours=6)
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate ML predictions'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def powerbi_ml_model_performance(request):
    """
    Power BI dashboard data for ML model performance monitoring
    """
    # Get active models
    active_models = MLForecastModel.objects.filter(is_active=True)
    
    model_metrics = []
    for model in active_models:
        # Get recent predictions
        recent_predictions = ForecastPrediction.objects.filter(
            model=model,
            prediction_date__gte=timezone.now() - timedelta(days=30)
        )
        
        # Calculate accuracy metrics
        accurate_predictions = recent_predictions.filter(is_accurate=True).count()
        total_predictions = recent_predictions.count()
        
        model_metrics.append({
            'model_id': model.id,
            'model_name': model.name,
            'model_type': model.model_type,
            'forecast_type': model.forecast_type,
            'accuracy_score': float(model.accuracy_score),
            'mae': float(model.mae),
            'rmse': float(model.rmse),
            'last_trained': model.last_trained,
            'predictions_last_30_days': total_predictions,
            'accurate_predictions_count': accurate_predictions,
            'recent_accuracy_rate': (accurate_predictions / max(1, total_predictions)) * 100,
            'is_active': model.is_active
        })
    
    return Response({
        'timestamp': timezone.now(),
        'active_models': len(active_models),
        'model_performance': model_metrics
    })