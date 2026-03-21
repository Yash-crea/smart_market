# ML Forecasting System Implementation Guide

## Overview
This guide explains how your ML-powered seasonal recommendation and forecasting system should work for your grocery store.

## 1. Initial Setup & Training

### Step 1: Populate Historical Data
```bash
# Install Django and dependencies first
pip install django pandas scikit-learn
cd grocerystore

# Create and run migrations
python manage.py makemigrations
python manage.py migrate

# Setup initial ML forecasting data
python manage.py setup_ml_forecasting --create-models --populate-data --update-predictions
```

### Step 2: Configure Seasonal Products
```python
# Example: Setting up seasonal products
from marche_smart.models import Product, SmartProducts

# Mark summer products
summer_products = ['Ice Cream', 'Cold Drinks', 'Sunscreen', 'Cotton Clothes']
Product.objects.filter(name__in=summer_products).update(
    peak_season='summer',
    weather_dependent=True,
    seasonal_priority=8
)

# Mark festival products
diwali_products = ['Sweets', 'Decorative Lights', 'Rangoli Colors', 'Dry Fruits']
Product.objects.filter(name__in=diwali_products).update(
    festival_association='diwali',
    festival_sales_boost=2.5,  # 150% boost during Diwali
    seasonal_priority=9
)

# Mark weekend favorites
weekend_products = ['Snacks', 'Beverages', 'Ready-to-eat Meals']
Product.objects.filter(name__in=weekend_products).update(
    weekend_boost=True,
    weekend_sales_multiplier=1.4  # 40% more sales on weekends
)
```

## 2. Daily Operations Workflow

### Morning Operations (Automated)
```python
# File: daily_forecasting.py
from datetime import datetime, timedelta
from django.utils import timezone
from marche_smart.models import *
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

def daily_forecast_update():
    """Run this every morning to update predictions"""
    
    # 1. Collect yesterday's sales data
    yesterday = timezone.now().date() - timedelta(days=1)
    update_sales_data(yesterday)
    
    # 2. Update weather data (from API)
    update_weather_data()
    
    # 3. Check for upcoming festivals
    check_festival_periods()
    
    # 4. Generate new predictions
    update_ml_predictions()
    
    # 5. Update inventory recommendations
    update_inventory_alerts()

def update_sales_data(date):
    """Update actual sales data for model training"""
    # Get sales from Orders
    from marche_smart.models import OrderItem
    
    sales_data = OrderItem.objects.filter(
        order__created_at__date=date
    ).values('product_id', 'smart_product_id').annotate(
        total_sales=models.Sum('subtotal'),
        units_sold=models.Sum('quantity')
    )
    
    for sale in sales_data:
        # Update seasonal sales data
        SeasonalSalesData.objects.update_or_create(
            product_id=sale['product_id'],
            smart_product_id=sale['smart_product_id'],
            year=date.year,
            month=date.month,
            defaults={
                'total_sales': sale['total_sales'],
                'units_sold': sale['units_sold'],
                'average_daily_sales': sale['total_sales']
            }
        )
```

### Real-Time Recommendation Engine
```python
def get_seasonal_recommendations(user=None, context=None):
    """Get personalized seasonal recommendations"""
    current_date = datetime.now()
    current_season = get_current_season(current_date.month)
    is_weekend = current_date.weekday() >= 5
    upcoming_festivals = get_upcoming_festivals()
    
    recommendations = []
    
    # 1. Seasonal Products
    seasonal_products = Product.objects.filter(
        peak_season=current_season,
        stock_quantity__gt=10
    ).order_by('-seasonal_priority', '-predicted_demand_7d')[:5]
    
    recommendations.extend(seasonal_products)
    
    # 2. Weekend Favorites (if weekend)
    if is_weekend:
        weekend_favorites = Product.objects.filter(
            weekend_boost=True,
            stock_quantity__gt=5
        ).order_by('-weekend_sales_multiplier')[:3]
        
        recommendations.extend(weekend_favorites)
    
    # 3. Festival Recommendations
    for festival in upcoming_festivals:
        festival_products = Product.objects.filter(
            festival_association=festival['name'],
            stock_quantity__gt=0
        ).order_by('-festival_sales_boost')[:4]
        
        recommendations.extend(festival_products)
    
    # 4. Weather-based Recommendations
    today_weather = WeatherData.objects.filter(date=current_date.date()).first()
    if today_weather:
        if today_weather.condition in ['rainy', 'stormy']:
            # Recommend umbrellas, raincoats, hot beverages
            weather_products = Product.objects.filter(
                name__icontains__in=['umbrella', 'raincoat', 'tea', 'coffee'],
                weather_dependent=True
            )[:3]
            recommendations.extend(weather_products)
        
        elif today_weather.temperature_avg > 30:
            # Hot day - recommend cold drinks, ice cream
            hot_weather_products = Product.objects.filter(
                name__icontains__in=['cold', 'ice', 'cool'],
                weather_dependent=True
            )[:3]
            recommendations.extend(hot_weather_products)
    
    return list(set(recommendations))  # Remove duplicates

def get_current_season(month):
    """Determine current season from month"""
    season_map = {
        12: 'winter', 1: 'winter', 2: 'winter',
        3: 'spring', 4: 'spring', 5: 'spring', 
        6: 'summer', 7: 'summer', 8: 'summer',
        9: 'monsoon', 10: 'monsoon', 11: 'monsoon'
    }
    return season_map.get(month, 'all_year')

def get_upcoming_festivals():
    """Get festivals in next 30 days"""
    # This would integrate with a festival calendar
    current_month = datetime.now().month
    festivals = []
    
    if current_month == 10:  # October
        festivals.append({'name': 'diwali', 'date': '2026-10-24'})
    elif current_month == 3:  # March  
        festivals.append({'name': 'holi', 'date': '2026-03-14'})
    elif current_month == 12:  # December
        festivals.append({'name': 'christmas', 'date': '2026-12-25'})
    
    return festivals
```

## 3. ML Model Training & Prediction

### Training Process
```python
# File: ml_training.py
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib

def train_demand_forecasting_model():
    """Train ML model for demand forecasting"""
    
    # 1. Prepare training data
    training_data = prepare_training_data()
    
    # 2. Feature engineering
    features, targets = create_features_and_targets(training_data)
    
    # 3. Split data
    X_train, X_test, y_train, y_test = train_test_split(
        features, targets, test_size=0.2, random_state=42
    )
    
    # 4. Train model
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # 5. Evaluate
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    rmse = mean_squared_error(y_test, predictions, squared=False)
    
    # 6. Save model
    model_path = 'ml_models/demand_forecast_model.joblib'
    joblib.dump(model, model_path)
    
    # 7. Update database record
    ml_model = MLForecastModel.objects.get(name='Demand Forecasting RandomForest')
    ml_model.accuracy_score = calculate_accuracy(y_test, predictions)
    ml_model.mae = mae
    ml_model.rmse = rmse
    ml_model.model_file_path = model_path
    ml_model.last_trained = timezone.now()
    ml_model.save()
    
    return model, mae, rmse

def prepare_training_data():
    """Prepare data for ML training"""
    # Get historical sales data
    sales_data = SeasonalSalesData.objects.all().values(
        'product__name', 'product__price', 'product__category__name',
        'units_sold', 'total_sales', 'month', 'is_weekend',
        'is_festival_period', 'season', 'year'
    )
    
    df = pd.DataFrame(sales_data)
    
    # Add weather data
    weather_data = WeatherData.objects.all().values(
        'date__month', 'condition', 'temperature_avg', 'rainfall',
        'sales_impact_score'
    )
    weather_df = pd.DataFrame(weather_data)
    
    # Merge datasets
    merged_data = df.merge(weather_df, left_on='month', right_on='date__month')
    
    return merged_data

def create_features_and_targets(data):
    """Create feature matrix and target vector"""
    # Features for ML model
    feature_columns = [
        'product__price', 'month', 'is_weekend', 'is_festival_period',
        'temperature_avg', 'rainfall', 'sales_impact_score'
    ]
    
    # Encode categorical variables
    data_encoded = pd.get_dummies(data, columns=['season', 'condition', 'product__category__name'])
    
    # Features
    feature_cols = [col for col in data_encoded.columns if col in feature_columns or col.startswith(('season_', 'condition_', 'product__category__name_'))]
    X = data_encoded[feature_cols].fillna(0)
    
    # Target
    y = data_encoded['units_sold']
    
    return X, y

def generate_predictions_for_all_products():
    """Generate predictions for all products"""
    model = joblib.load('ml_models/demand_forecast_model.joblib')
    
    products = Product.objects.all()
    
    for product in products:
        # Get features for this product
        features = product.get_demand_forecast_features()
        
        # Convert to format expected by model
        feature_vector = create_feature_vector(features)
        
        # Generate predictions
        pred_7d = model.predict([feature_vector])[0]
        pred_30d = model.predict([modify_feature_vector_for_30d(feature_vector)])[0]
        
        # Calculate revenue prediction
        pred_revenue_30d = pred_30d * product.price
        
        # Update product with predictions
        product.update_ml_predictions(
            demand_7d=int(pred_7d),
            demand_30d=int(pred_30d), 
            revenue_30d=pred_revenue_30d,
            accuracy=85.5  # From model evaluation
        )
```

## 4. Frontend Integration

### View for Seasonal Recommendations
```python
# views.py
from django.shortcuts import render
from django.http import JsonResponse
from .ml_system import get_seasonal_recommendations

def shop_view(request):
    """Enhanced shop view with ML recommendations"""
    
    # Get regular products
    all_products = Product.objects.filter(in_stock=True)
    
    # Get personalized recommendations
    recommendations = get_seasonal_recommendations(user=request.user)
    
    # Get trending products (high recent sales)
    trending = Product.objects.filter(
        predicted_demand_7d__gt=50
    ).order_by('-predicted_demand_7d')[:6]
    
    context = {
        'all_products': all_products,
        'seasonal_recommendations': recommendations,
        'trending_products': trending,
        'current_season': get_current_season(datetime.now().month),
        'upcoming_festivals': get_upcoming_festivals()
    }
    
    return render(request, 'shop.html', context)

def api_recommendations(request):
    """API endpoint for getting recommendations"""
    recommendations = get_seasonal_recommendations(user=request.user)
    
    data = [{
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'predicted_demand': product.predicted_demand_7d,
        'recommendation_reason': get_recommendation_reason(product)
    } for product in recommendations]
    
    return JsonResponse({'recommendations': data})

def get_recommendation_reason(product):
    """Generate reason for recommendation"""
    current_month = datetime.now().month
    is_weekend = datetime.now().weekday() >= 5
    
    if product.peak_season == get_current_season(current_month):
        return f"Popular in {product.peak_season} season"
    elif product.weekend_boost and is_weekend:
        return "Weekend favorite"
    elif product.festival_association != 'none':
        return f"Perfect for {product.festival_association}"
    elif product.predicted_demand_7d > 100:
        return "High demand predicted"
    else:
        return "Recommended for you"
```

### Enhanced Template
```html
<!-- shop.html -->
<div class="recommendations-section">
    <h2>🌟 Recommended for You</h2>
    <div class="season-indicator">
        Current Season: <span class="season">{{ current_season|title }}</span>
    </div>
    
    {% if upcoming_festivals %}
        <div class="festival-alert">
            🎉 Upcoming: {% for festival in upcoming_festivals %}{{ festival.name|title }}{% endfor %}
        </div>
    {% endif %}
    
    <div class="product-grid">
        {% for product in seasonal_recommendations %}
            <div class="product-card seasonal">
                <div class="recommendation-badge">
                    {% if product.peak_season == current_season %}
                        <span class="badge seasonal">{{ current_season|title }} Pick</span>
                    {% elif product.festival_association != 'none' %}
                        <span class="badge festival">Festival Special</span>
                    {% elif product.weekend_boost %}
                        <span class="badge weekend">Weekend Favorite</span>
                    {% endif %}
                </div>
                
                <img src="{{ product.image_url }}" alt="{{ product.name }}">
                <h3>{{ product.name }}</h3>
                <p class="price">₹{{ product.price }}</p>
                <p class="prediction">Expected demand: {{ product.predicted_demand_7d }} units</p>
                
                {% if product.forecast_accuracy > 80 %}
                    <div class="accuracy-badge">{{ product.forecast_accuracy }}% accurate</div>
                {% endif %}
                
                <button class="add-to-cart" data-product-id="{{ product.id }}">
                    Add to Cart
                </button>
            </div>
        {% endfor %}
    </div>
</div>
```

## 5. Automated Tasks (Cron Jobs)

### Daily Tasks
```bash
# Add to crontab
# Update predictions every morning at 6 AM
0 6 * * * cd /path/to/grocery/store && python manage.py update_daily_predictions

# Update weather data every 6 hours  
0 */6 * * * cd /path/to/grocery/store && python manage.py fetch_weather_data

# Generate inventory alerts every day at 8 AM
0 8 * * * cd /path/to/grocery/store && python manage.py check_inventory_levels
```

### Management Commands
```python
# management/commands/update_daily_predictions.py
from django.core.management.base import BaseCommand
from marche_smart.ml_system import generate_predictions_for_all_products

class Command(BaseCommand):
    help = 'Update ML predictions for all products'
    
    def handle(self, *args, **options):
        generate_predictions_for_all_products()
        self.stdout.write('Predictions updated successfully')
```

## 6. Admin Dashboard

### Analytics Views  
```python
def admin_analytics(request):
    """Admin dashboard with ML insights"""
    
    # Model performance
    models = MLForecastModel.objects.filter(is_active=True)
    
    # Top performing seasonal products
    seasonal_performers = Product.objects.filter(
        seasonal_priority__gte=7
    ).order_by('-predicted_revenue_30d')[:10]
    
    # Inventory alerts
    low_stock = Product.objects.filter(
        stock_quantity__lte=models.F('reorder_point')
    )
    
    # Prediction accuracy
    recent_predictions = ForecastPrediction.objects.filter(
        target_date__lt=timezone.now(),
        actual_value__isnull=False
    )[:50]
    
    context = {
        'models': models,
        'seasonal_performers': seasonal_performers,
        'low_stock_products': low_stock,
        'prediction_accuracy': calculate_overall_accuracy(recent_predictions)
    }
    
    return render(request, 'admin_analytics.html', context)
```

This system will automatically:
- 📈 **Predict demand** based on seasons, weather, and festivals
- 🎯 **Show relevant products** to customers at the right time  
- 📦 **Optimize inventory** with automated reorder alerts
- 🎉 **Boost festival sales** with targeted recommendations
- 🌤️ **React to weather** changes (umbrellas on rainy days)
- 📊 **Learn continuously** from new sales data

The beauty is it runs automatically and gets smarter over time!