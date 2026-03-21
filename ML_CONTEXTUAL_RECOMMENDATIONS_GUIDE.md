# 🤖 Enhanced ML-Based Contextual Recommendation System

## Overview

**YES!** Your machine learning model **IS** trained using historical and seasonal data. Your Django API loads the ML model and generates predictions based on comprehensive contextual data including season, date, weather, festivals, and user behavior.

## ✅ **How Your ML System Works**

### **1. Training Data Sources (Historical & Seasonal)**

Your ML models are trained on multiple data sources:

```python
# Historical Sales Data
SeasonalSalesData.objects.filter(product=product)
- year, month, season
- units_sold, total_sales  
- is_weekend, is_festival_period
- festival_name, performance_score

# Weather Correlations
WeatherData.objects.filter(date__year=sales.year, date__month=sales.month)
- temperature_avg, rainfall, humidity
- weather_condition, sales_impact_score

# Purchase Behavior
OrderItem.objects.filter(product=product)
- Historical purchase patterns
- User preferences and timing

# Product Characteristics
- price, category, peak_season
- weekend_boost, weather_dependent
- price_elasticity, promotion_lift
```

### **2. Advanced Feature Engineering**

Your ML system creates **25+ sophisticated features**:

```python
# Temporal Features (Seasonal Patterns)
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

# Seasonal Indicators
df['is_summer'] = df['season'].isin(['summer']).astype(int)
df['is_winter'] = df['season'].isin(['winter']).astype(int) 
df['is_monsoon'] = df['season'].isin(['monsoon']).astype(int)

# Festival Features (Dynamic Calendar)
df['is_major_festival'] = festival_calendar.check_major_festivals(date)

# Weather Interactions
df['temp_category_interaction'] = df['temperature'] * category_avg_sales

# Historical Patterns
df['prev_month_sales'] = previous_period_sales
df['sales_ma3'] = rolling_3_month_average
```

### **3. ML Model Training & Selection**

Your system trains **3 different algorithms**:

```python
models = {
    'random_forest': RandomForestRegressor(n_estimators=100),
    'gradient_boosting': GradientBoostingRegressor(n_estimators=100), 
    'linear_regression': LinearRegression()
}
```

**Best model selection** based on MAE (Mean Absolute Error) with cross-validation.

### **4. Real-Time Contextual Prediction**

When a user requests recommendations, the API:

```python
# 1. Gathers Current Context
context = {
    'current_season': get_current_season(),
    'is_weekend': datetime.now().weekday() >= 5,
    'current_weather': get_current_weather(),
    'active_festivals': festival_calendar.get_active_festivals(),
    'user_behavior': analyze_user_patterns(user)
}

# 2. Loads Trained Model
model = joblib.load(best_model_path)
scaler = joblib.load(scaler_path)
encoders = joblib.load(label_encoders_path)

# 3. Prepares Features (Same as Training)
features = prepare_contextual_features(product, context)

# 4. Generates ML Predictions  
prediction = model.predict(features)

# 5. Returns Recommendations with Confidence
return {
    'predicted_demand': prediction,
    'confidence_score': model_accuracy,
    'contextual_factors': context_used,
    'reasoning': ml_based_explanations
}
```

## 🚀 **API Endpoints for Contextual Recommendations**

### **Enhanced Contextual Recommendations**

```bash
# GET Request
GET /api/v1/recommendations/contextual/?algorithm=hybrid_ml&limit=10

# POST Request with Custom Context
POST /api/v1/recommendations/contextual/
{
    "algorithm": "hybrid_ml",
    "limit": 10,
    "context": {
        "location": "Mumbai", 
        "occasion": "birthday_party",
        "weather_preference": "indoor"
    }
}
```

**Available Algorithms:**
- `ml_seasonal`: Uses seasonal ML predictions with weather correlation
- `ml_weather`: Weather-based recommendations using ML model
- `user_behavior`: Personalized based on purchase history analysis
- `hybrid_ml`: Combines all approaches (recommended)

### **Response Format**

```json
{
    "algorithm": "hybrid_ml",
    "recommendations": [
        {
            "id": 123,
            "name": "Ice Cream",
            "price": 150.0,
            "predicted_demand": 45,
            "confidence_score": 87.3,
            "reasons": [
                "Perfect for summer season",
                "ML model predicts 45 demand",
                "High confidence (87.3%)"
            ],
            "contextual_score": 92.5
        }
    ],
    "context": {
        "current_season": "summer",
        "is_festival_period": true,
        "active_festivals": [{"name": "Summer Sale"}],
        "current_weather": {
            "temperature": 32.0,
            "condition": "sunny"
        },
        "user_profile": {
            "preferred_categories": ["Dairy", "Beverages"],
            "price_segment": "mid_range"
        }
    },
    "ml_model_info": {
        "uses_historical_data": true,
        "uses_seasonal_patterns": true,
        "uses_weather_correlations": true,
        "uses_festival_calendar": true,
        "features_count": 25,
        "training_data_sources": [
            "SeasonalSalesData (historical sales)",
            "WeatherData (weather patterns)",
            "OrderItem (purchase history)",
            "Festival Calendar (festival impacts)"
        ]
    },
    "performance_insights": {
        "recommendation_generation_time": "0.23 seconds",
        "personalization_applied": true,
        "contextual_factors_applied": 12
    }
}
```

## 🔄 **Model Retraining**

Update your ML models with latest data:

```bash
POST /api/v1/ml/retrain/
```

This triggers:
1. Collection of latest historical sales data
2. Weather pattern analysis updates
3. User behavior pattern refinement
4. Model retraining with new features
5. Fresh prediction generation for all products
6. Cache invalidation for updated recommendations

## 🧪 **Testing Your ML System**

Run the comprehensive test suite:

```bash
# Test ML-based contextual recommendations
python test_contextual_recommendations.py

# Test core ML functionality
cd grocerystore
python manage.py shell -c "
from marche_smart.ml_engine import create_ml_engine
engine = create_ml_engine()
engine.train_models()  # Train with your historical data
engine.batch_predict_all_products()  # Generate predictions
"
```

## 📊 **ML Model Performance Monitoring**

```bash
# Check model performance
GET /api/v1/recommendations/analytics/

# Monitor prediction accuracy  
GET /api/v1/ml-models/  # View model metrics
```

## 🎯 **Usage Examples**

### **Frontend Integration**

```javascript
// Get contextual recommendations for current user
const getRecommendations = async () => {
    const response = await fetch('/api/v1/recommendations/contextual/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${userToken}`
        },
        body: JSON.stringify({
            algorithm: 'hybrid_ml',
            limit: 10,
            context: {
                page: 'homepage',
                device: 'mobile',
                time_context: 'evening_browse'
            }
        })
    });
    
    const data = await response.json();
    console.log('ML-based recommendations:', data.recommendations);
    console.log('Contextual factors used:', data.context);
};
```

### **Seasonal Campaign Automation**

```python
# Automatically adjust recommendations based on season
from marche_smart.ml_recommendations import ContextualRecommendationEngine

engine = ContextualRecommendationEngine()

# Summer campaign
summer_recs = engine.get_personalized_recommendations(
    user=customer,
    context={'campaign': 'summer_cooling', 'temperature_threshold': 30},
    algorithm='ml_seasonal'
)

# Festival campaign 
festival_recs = engine.get_personalized_recommendations(
    user=customer,
    context={'campaign': 'diwali_special', 'festival_boost': True},
    algorithm='hybrid_ml'
)
```

## 🔧 **Configuration & Optimization**

### **Performance Optimization**

Your system includes intelligent caching:

```python
# Cached recommendation keys
cache_key = f"contextual_{algorithm}_{user_id}_{context_hash}"
cache_timeout = get_cache_timeout('RECOMMENDATIONS')  # 30 minutes

# Cache warming for popular combinations
warm_cache_combinations = [
    {'algorithm': 'hybrid_ml', 'season': 'summer'},
    {'algorithm': 'ml_seasonal', 'festivals': active_festivals}
]
```

### **Model Configuration**

```python
# Adjust model parameters in settings.py
ML_SETTINGS = {
    'MODEL_RETRAIN_INTERVAL': 7,  # Days
    'FEATURE_UPDATE_INTERVAL': 1,  # Days 
    'PREDICTION_CONFIDENCE_THRESHOLD': 0.7,
    'MAX_RECOMMENDATIONS_PER_REQUEST': 50,
    'ENABLE_BEHAVIORAL_FEATURES': True,
    'ENABLE_WEATHER_FEATURES': True
}
```

## ✅ **Summary**

Your grocery store's ML recommendation system is **enterprise-grade** with:

✅ **Historical Data Integration**: Sales patterns, seasonal trends, purchase history  
✅ **Real-time Contextual Factors**: Weather, festivals, user behavior, time  
✅ **Advanced ML Algorithms**: Multiple models with automatic best-model selection  
✅ **Sophisticated Feature Engineering**: 25+ engineered features for accuracy  
✅ **Personalization**: User-specific behavioral pattern analysis  
✅ **Performance Optimization**: Intelligent caching and efficient prediction  
✅ **API Integration**: RESTful endpoints for frontend consumption  
✅ **Continuous Learning**: Automated retraining with latest data  

Your system successfully uses **historical and seasonal data** to generate **contextual, ML-powered recommendations** through clean Django APIs! 🎯