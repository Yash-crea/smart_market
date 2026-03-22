from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from . import api_views
from . import ssh_api_views  # Import SSH API views
from . import advanced_api_views  # Import Advanced ML API views

# Create router for ViewSets
router = DefaultRouter()

# Product management
router.register(r'categories', api_views.CategoryViewSet, basename='category')
router.register(r'products', api_views.ProductViewSet, basename='product')
router.register(r'smart-products', api_views.SmartProductViewSet, basename='smartproduct')

# Cart and orders
router.register(r'carts', api_views.CartViewSet, basename='cart')
router.register(r'orders', api_views.OrderViewSet, basename='order')

# Machine Learning endpoints
router.register(r'ml-models', api_views.MLForecastModelViewSet, basename='mlmodel')
router.register(r'predictions', api_views.ForecastPredictionViewSet, basename='prediction')
router.register(r'weather', api_views.WeatherDataViewSet, basename='weather')
router.register(r'seasonal-data', api_views.SeasonalSalesDataViewSet, basename='seasonaldata')

app_name = 'api'

urlpatterns = [
    # Include router URLs
    path('v1/', include(router.urls)),
    
    # ============= AUTHENTICATION ENDPOINTS =============
    path('v1/auth/login/', api_views.CustomAuthToken.as_view(), name='auth_login'),
    path('v1/auth/register/', api_views.register_user, name='auth_register'),
    path('v1/auth/token/', obtain_auth_token, name='auth_token'),
    
    # ============= RECOMMENDATION ENDPOINTS =============
    path('v1/recommendations/', api_views.get_recommendations, name='recommendations'),
    path('v1/recommendations/contextual/', api_views.get_contextual_recommendations, name='contextual_recommendations'),
    path('v1/recommendations/analytics/', api_views.recommendation_analytics, name='recommendation_analytics'),
    path('v1/interactions/log/', api_views.log_interaction, name='log_interaction'),
    
    # ============= ML MODEL MANAGEMENT =============  
    path('v1/ml/retrain/', api_views.retrain_ml_model_with_latest_data, name='ml_retrain'),
    
    # ============= CACHE MANAGEMENT ENDPOINTS =============
    path('v1/cache/stats/', api_views.cache_stats, name='cache_stats'),
    path('v1/cache/invalidate/', api_views.invalidate_cache, name='invalidate_cache'),
    path('v1/cache/warm/', api_views.warm_cache, name='warm_cache'),
    
    # ============= SSH MANAGEMENT ENDPOINTS =============
    path('v1/ssh/status/', ssh_api_views.ssh_server_status, name='ssh_server_status'),
    path('v1/ssh/health/', ssh_api_views.ssh_health_check, name='ssh_health_check'),
    path('v1/ssh/deploy/', ssh_api_views.ssh_deploy, name='ssh_deploy'),
    path('v1/ssh/execute/', ssh_api_views.ssh_execute, name='ssh_execute'),
    path('v1/ssh/config/', ssh_api_views.ssh_config, name='ssh_config'),
    path('v1/ssh/tunnel/', ssh_api_views.ssh_tunnel, name='ssh_tunnel'),
    
    # ============= POWER BI INTEGRATION ENDPOINTS =============
    # Customer Power BI remains available via authenticated API access.
    # Owner Power BI routes stay disabled in favor of Excel export.
    path('v1/powerbi/customer-dashboard/', advanced_api_views.powerbi_customer_dashboard, name='powerbi_customer_dashboard'),
    
    # ============= ADVANCED ML RECOMMENDATION & FORECASTING =============
    path('v1/forecast/30day/<int:product_id>/', advanced_api_views.get_30day_demand_forecast, name='advanced_forecast_30day'),
    path('v1/recommendations/personalized/', advanced_api_views.get_personalized_recommendations, name='advanced_recommendations_personalized'),
    path('v1/recommendations/export/', advanced_api_views.export_recommendations_json, name='advanced_recommendations_export'),
    path('v1/models/train/', advanced_api_views.train_forecasting_models, name='advanced_models_train'),
    path('v1/models/status/', advanced_api_views.get_model_status, name='advanced_models_status'),
]