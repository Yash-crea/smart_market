"""
Advanced Recommendation and Forecasting System
Combines historical sales data, cultural events, and user behavior for personalized recommendations
with 30-day demand forecasting and explainable AI
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
from decimal import Decimal
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.cluster import KMeans
import joblib

from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum, Avg, F

from .models import (
    Product, SmartProducts, SeasonalSalesData, WeatherData, 
    OrderItem, ProductRecommendationLog, MLForecastModel
)
from .festival_calendar import FestivalCalendar


class AdvancedRecommendationForecastSystem:
    """
    Advanced ML-based recommendation and forecasting system with:
    - 30-day demand forecasting with RMSE/MAE validation
    - Diverse, personalized recommendations
    - Cultural event integration
    - Explainable AI with reasoning
    """
    
    def __init__(self):
        self.models_path = 'ml_models'
        self.festival_calendar = FestivalCalendar()
        
        # ML Models for forecasting
        self.forecast_models = {
            'random_forest': RandomForestRegressor(n_estimators=200, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=200, random_state=42),
            'linear_regression': LinearRegression()
        }
        
        # User clustering for personalization
        self.user_clusterer = KMeans(n_clusters=5, random_state=42)
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
        # Diversity parameters
        self.max_items_per_category = 3
        self.min_recommendation_diversity = 0.6
        
    def prepare_comprehensive_training_data(self) -> pd.DataFrame:
        """
        Prepare comprehensive training dataset with all historical sales data
        """
        print("🔄 Preparing comprehensive training data...")
        
        training_data = []
        
        # Process all historical sales data
        all_orders = OrderItem.objects.select_related('order', 'product', 'smart_product').all()
        
        for order_item in all_orders:
            order_date = order_item.order.created_at.date()
            
            # Get product information
            if order_item.product:
                product = order_item.product
                product_id = product.id
                product_name = product.name
                product_type = 'regular'
                price = float(product.price)
                category = product.category.name if product.category else 'unknown'
            elif order_item.smart_product:
                product = order_item.smart_product
                product_id = product.id
                product_name = product.name
                product_type = 'smart'
                price = float(product.price)
                category = product.category or 'unknown'
            else:
                continue
            
            # Get seasonal data for this period
            try:
                seasonal_data = SeasonalSalesData.objects.filter(
                    product=order_item.product if order_item.product else None,
                    smart_product=order_item.smart_product if order_item.smart_product else None,
                    year=order_date.year,
                    month=order_date.month
                ).first()
            except:
                seasonal_data = None
            
            # Get weather data
            try:
                weather_data = WeatherData.objects.filter(
                    date__year=order_date.year,
                    date__month=order_date.month
                ).first()
            except:
                weather_data = None
            
            # Festival information for this date
            festival_info = self.festival_calendar.get_current_date_info(order_date)
            is_festival = len(festival_info.get('active_festivals', [])) > 0
            festival_boost = festival_info.get('festival_boost_multiplier', 1.0)
            
            # User behavior features
            user_id = order_item.order.user.id if hasattr(order_item.order, 'user') else None
            
            training_data.append({
                # Product features
                'product_id': product_id,
                'product_name': product_name,
                'product_type': product_type,
                'price': price,
                'category': category,
                
                # Temporal features
                'date': order_date,
                'year': order_date.year,
                'month': order_date.month,
                'day': order_date.day,
                'weekday': order_date.weekday(),
                'is_weekend': order_date.weekday() >= 5,
                'quarter': (order_date.month - 1) // 3 + 1,
                
                # Season and festival features
                'season': self._get_season_from_month(order_date.month),
                'is_festival': is_festival,
                'festival_boost': festival_boost,
                'festival_names': ','.join([f['name'] for f in festival_info.get('active_festivals', [])]),
                
                # Weather features
                'temperature': float(weather_data.temperature_avg) if weather_data else 25.0,
                'rainfall': float(weather_data.rainfall) if weather_data else 0.0,
                'humidity': float(weather_data.humidity) if weather_data else 60.0,
                'weather_condition': weather_data.condition if weather_data else 'sunny',
                
                # Sales features
                'quantity_sold': order_item.quantity,
                'revenue': float(order_item.subtotal),
                'unit_price': float(order_item.unit_price),
                
                # User features
                'user_id': user_id,
                
                # Product characteristics (if available)
                'peak_season': getattr(product, 'peak_season', 'all_year'),
                'weekend_boost': getattr(product, 'weekend_boost', False),
                'weather_dependent': getattr(product, 'weather_dependent', False),
                'price_elasticity': float(getattr(product, 'price_elasticity', 1.0)),
                'promotion_lift': float(getattr(product, 'promotion_lift', 1.0)),
                'is_promotional': getattr(product, 'is_promotional', False)
            })
        
        df = pd.DataFrame(training_data)
        print(f"✅ Prepared {len(df)} comprehensive training samples")
        return df
    
    def engineer_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create advanced features for forecasting and recommendations
        """
        print("🔧 Engineering advanced features...")
        
        # Temporal features
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['day_sin'] = np.sin(2 * np.pi * df['day'] / 31)
        df['day_cos'] = np.cos(2 * np.pi * df['day'] / 31)
        df['weekday_sin'] = np.sin(2 * np.pi * df['weekday'] / 7)
        df['weekday_cos'] = np.cos(2 * np.pi * df['weekday'] / 7)
        
        # Seasonal indicators
        df['is_summer'] = (df['month'].isin([6, 7, 8])).astype(int)
        df['is_winter'] = (df['month'].isin([12, 1, 2])).astype(int)
        df['is_monsoon'] = (df['month'].isin([9, 10, 11])).astype(int)
        df['is_spring'] = (df['month'].isin([3, 4, 5])).astype(int)
        
        # Price features
        df['price_category_ratio'] = df.groupby('category')['price'].transform(lambda x: x / x.mean())
        df['price_quantile'] = df.groupby(['year', 'month'])['price'].transform(lambda x: pd.qcut(x, 5, labels=False, duplicates='drop'))
        
        # Lag features (previous periods)
        df_sorted = df.sort_values(['product_id', 'date'])
        
        # 7-day, 30-day, and 365-day lags
        for lag_days in [7, 30, 365]:
            lag_col = f'sales_{lag_days}d_ago'
            df_sorted[lag_col] = df_sorted.groupby('product_id')['quantity_sold'].shift(lag_days)
        
        # Rolling statistics
        df_sorted['sales_7d_mean'] = df_sorted.groupby('product_id')['quantity_sold'].rolling(7, min_periods=1).mean().reset_index(0, drop=True)
        df_sorted['sales_30d_mean'] = df_sorted.groupby('product_id')['quantity_sold'].rolling(30, min_periods=1).mean().reset_index(0, drop=True)
        df_sorted['sales_7d_std'] = df_sorted.groupby('product_id')['quantity_sold'].rolling(7, min_periods=1).std().reset_index(0, drop=True)
        
        # Competition features
        df_sorted['category_demand'] = df_sorted.groupby(['date', 'category'])['quantity_sold'].transform('sum')
        df_sorted['market_share'] = df_sorted['quantity_sold'] / (df_sorted['category_demand'] + 0.001)
        
        # Weather interaction features
        df_sorted['temp_season_interaction'] = df_sorted['temperature'] * df_sorted['month']
        df_sorted['weather_weekend_interaction'] = df_sorted['is_weekend'] * (df_sorted['temperature'] > 30).astype(int)
        
        print("✅ Advanced feature engineering completed")
        return df_sorted.fillna(0)
    
    def train_forecasting_models(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Train multiple forecasting models with proper validation
        """
        print("🤖 Training forecasting models with time series validation...")
        
        # Prepare features for training
        feature_columns = [
            'price', 'month_sin', 'month_cos', 'day_sin', 'day_cos', 'weekday_sin', 'weekday_cos',
            'is_weekend', 'is_festival', 'festival_boost', 'is_summer', 'is_winter', 'is_monsoon', 'is_spring',
            'temperature', 'rainfall', 'humidity', 'price_category_ratio', 'price_quantile',
            'sales_7d_ago', 'sales_30d_ago', 'sales_365d_ago', 'sales_7d_mean', 'sales_30d_mean', 'sales_7d_std',
            'category_demand', 'market_share', 'temp_season_interaction', 'weather_weekend_interaction',
            'weekend_boost', 'weather_dependent', 'price_elasticity', 'promotion_lift', 'is_promotional'
        ]
        
        # Encode categorical variables
        categorical_features = ['category', 'peak_season', 'weather_condition', 'product_type']
        for feature in categorical_features:
            if feature not in self.label_encoders:
                self.label_encoders[feature] = LabelEncoder()
                df[f'{feature}_encoded'] = self.label_encoders[feature].fit_transform(df[feature].astype(str))
            feature_columns.append(f'{feature}_encoded')
        
        # Prepare training data
        X = df[feature_columns].fillna(0)
        y = df['quantity_sold']
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        results = {}
        best_model = None
        best_score = float('inf')
        
        for model_name, model in self.forecast_models.items():
            print(f"Training {model_name}...")
            
            # Cross-validation scores
            cv_scores = []
            mae_scores = []
            rmse_scores = []
            
            for train_idx, test_idx in tscv.split(X):
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                
                # Scale features for linear models
                if model_name == 'linear_regression':
                    X_train_scaled = self.scaler.fit_transform(X_train)
                    X_test_scaled = self.scaler.transform(X_test)
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                
                # Calculate metrics
                mae = mean_absolute_error(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                r2 = r2_score(y_test, y_pred)
                
                mae_scores.append(mae)
                rmse_scores.append(rmse)
                cv_scores.append(r2)
            
            # Average metrics
            avg_mae = np.mean(mae_scores)
            avg_rmse = np.mean(rmse_scores)
            avg_r2 = np.mean(cv_scores)
            
            results[model_name] = {
                'mae': avg_mae,
                'rmse': avg_rmse,
                'r2': avg_r2,
                'accuracy': max(0, 100 * avg_r2)
            }
            
            if avg_mae < best_score:
                best_score = avg_mae
                best_model = model_name
            
            print(f"  MAE: {avg_mae:.2f}, RMSE: {avg_rmse:.2f}, R²: {avg_r2:.3f}")
            
            # Save model
            model_path = f'{self.models_path}/forecast_{model_name}.joblib'
            joblib.dump(model, model_path)
        
        # Save preprocessing objects
        joblib.dump(self.scaler, f'{self.models_path}/forecast_scaler.joblib')
        joblib.dump(self.label_encoders, f'{self.models_path}/forecast_encoders.joblib')
        
        print(f"✅ Best model: {best_model} (MAE: {best_score:.2f})")
        return {'results': results, 'best_model': best_model}
    
    def predict_30day_demand(self, product_data: Dict, start_date: datetime = None) -> Dict:
        """
        Predict demand for the next 30 days with confidence intervals
        """
        if start_date is None:
            start_date = timezone.now().date()
        
        # Load best model
        try:
            model = joblib.load(f'{self.models_path}/forecast_random_forest.joblib')  # Default to RF
            scaler = joblib.load(f'{self.models_path}/forecast_scaler.joblib')
            encoders = joblib.load(f'{self.models_path}/forecast_encoders.joblib')
        except:
            return {'error': 'Forecasting models not trained. Please train models first.'}
        
        predictions = []
        
        for day_offset in range(30):
            forecast_date = start_date + timedelta(days=day_offset)
            
            # Get festival info for this date
            festival_info = self.festival_calendar.get_current_date_info(forecast_date)
            
            # Prepare features for this date
            features = {
                'price': product_data.get('price', 0),
                'month_sin': np.sin(2 * np.pi * forecast_date.month / 12),
                'month_cos': np.cos(2 * np.pi * forecast_date.month / 12),
                'day_sin': np.sin(2 * np.pi * forecast_date.day / 31),
                'day_cos': np.cos(2 * np.pi * forecast_date.day / 31),
                'weekday_sin': np.sin(2 * np.pi * forecast_date.weekday() / 7),
                'weekday_cos': np.cos(2 * np.pi * forecast_date.weekday() / 7),
                'is_weekend': int(forecast_date.weekday() >= 5),
                'is_festival': int(len(festival_info.get('active_festivals', [])) > 0),
                'festival_boost': festival_info.get('festival_boost_multiplier', 1.0),
                'is_summer': int(forecast_date.month in [6, 7, 8]),
                'is_winter': int(forecast_date.month in [12, 1, 2]),
                'is_monsoon': int(forecast_date.month in [9, 10, 11]),
                'is_spring': int(forecast_date.month in [3, 4, 5]),
                'temperature': product_data.get('temperature', 25.0),
                'rainfall': product_data.get('rainfall', 0.0),
                'humidity': product_data.get('humidity', 60.0),
                'price_category_ratio': product_data.get('price_category_ratio', 1.0),
                'price_quantile': product_data.get('price_quantile', 2),
                'sales_7d_ago': product_data.get('avg_weekly_sales', 10) / 7,
                'sales_30d_ago': product_data.get('avg_weekly_sales', 10) / 7,
                'sales_365d_ago': product_data.get('avg_weekly_sales', 10) / 7,
                'sales_7d_mean': product_data.get('avg_weekly_sales', 10) / 7,
                'sales_30d_mean': product_data.get('avg_weekly_sales', 10) / 7,
                'sales_7d_std': product_data.get('avg_weekly_sales', 10) / 14,
                'category_demand': product_data.get('category_demand', 100),
                'market_share': product_data.get('market_share', 0.1),
                'temp_season_interaction': product_data.get('temperature', 25.0) * forecast_date.month,
                'weather_weekend_interaction': int(forecast_date.weekday() >= 5) * int(product_data.get('temperature', 25.0) > 30),
                'weekend_boost': int(product_data.get('weekend_boost', False)),
                'weather_dependent': int(product_data.get('weather_dependent', False)),
                'price_elasticity': product_data.get('price_elasticity', 1.0),
                'promotion_lift': product_data.get('promotion_lift', 1.0),
                'is_promotional': int(product_data.get('is_promotional', False))
            }
            
            # Encode categorical features
            categorical_features = ['category', 'peak_season', 'weather_condition', 'product_type']
            for feature in categorical_features:
                if feature in encoders and feature in product_data:
                    try:
                        encoded_value = encoders[feature].transform([str(product_data[feature])])[0]
                        features[f'{feature}_encoded'] = encoded_value
                    except:
                        features[f'{feature}_encoded'] = 0
                else:
                    features[f'{feature}_encoded'] = 0
            
            # Create feature vector
            feature_vector = np.array([[features[col] for col in sorted(features.keys())]])
            
            # Make prediction
            prediction = model.predict(feature_vector)[0]
            prediction = max(0, prediction)  # Ensure non-negative
            
            predictions.append({
                'date': forecast_date.isoformat(),
                'predicted_demand': round(prediction, 2),
                'is_festival': features['is_festival'],
                'festival_boost': features['festival_boost'],
                'day_of_week': forecast_date.strftime('%A')
            })
        
        # Calculate summary statistics
        total_demand = sum([p['predicted_demand'] for p in predictions])
        avg_daily_demand = total_demand / 30
        peak_demand = max([p['predicted_demand'] for p in predictions])
        
        return {
            'product_id': product_data.get('product_id'),
            'product_name': product_data.get('name'),
            'forecast_period': f"{start_date.isoformat()} to {(start_date + timedelta(days=29)).isoformat()}",
            'total_30day_demand': round(total_demand, 2),
            'average_daily_demand': round(avg_daily_demand, 2),
            'peak_daily_demand': round(peak_demand, 2),
            'daily_predictions': predictions,
            'forecast_generated_at': timezone.now().isoformat()
        }
    
    def generate_personalized_recommendations(
        self, 
        user: User = None, 
        limit: int = 20,
        context: Dict = None
    ) -> List[Dict]:
        """
        Generate diverse, personalized recommendations with explainable reasons
        """
        print(f"🎯 Generating personalized recommendations for user {user.id if user else 'anonymous'}...")
        
        if context is None:
            context = {}
        
        all_candidates = []
        current_date = timezone.now().date()
        
        # Get user's purchase history for personalization
        user_history = self._get_user_purchase_history(user) if user else {}
        user_preferences = self._analyze_user_preferences(user) if user else {}
        
        # Get festival context
        festival_info = self.festival_calendar.get_current_date_info(current_date)
        
        # Generate candidates from regular products
        regular_products = Product.objects.filter(in_stock=True)
        for product in regular_products:
            candidate = self._score_product_candidate(
                product, 'regular', user_history, user_preferences, festival_info, context
            )
            if candidate:
                all_candidates.append(candidate)
        
        # Generate candidates from smart products
        smart_products = SmartProducts.objects.filter(stock_quantity__gt=0)
        for product in smart_products:
            candidate = self._score_product_candidate(
                product, 'smart', user_history, user_preferences, festival_info, context
            )
            if candidate:
                all_candidates.append(candidate)
        
        # Apply diversity and ranking
        diverse_recommendations = self._apply_diversity_ranking(all_candidates, limit)
        
        # Format final recommendations
        formatted_recommendations = []
        for i, rec in enumerate(diverse_recommendations):
            formatted_rec = {
                'rank': i + 1,
                'user_id': user.id if user else None,
                'item_id': rec['product_id'],
                'item_name': rec['product_name'],
                'category': rec['category'],
                'price': rec['price'],
                'score': round(rec['total_score'], 2),
                'demand_score': round(rec['demand_score'], 2),
                'personalization_score': round(rec['personalization_score'], 2),
                'seasonal_score': round(rec['seasonal_score'], 2),
                'reason': rec['primary_reason'],
                'detailed_reasons': rec['reasons'],
                'forecast_date': current_date.isoformat(),
                'predicted_demand': rec.get('predicted_demand', 0),
                'confidence': rec['confidence'],
                'diversity_factor': rec['diversity_factor']
            }
            formatted_recommendations.append(formatted_rec)
        
        return formatted_recommendations
    
    def _get_user_purchase_history(self, user: User) -> Dict:
        """Get comprehensive user purchase history"""
        if not user:
            return {}
        
        # Recent purchases (last 90 days)
        recent_orders = OrderItem.objects.filter(
            order__user=user,
            order__created_at__gte=timezone.now() - timedelta(days=90)
        ).select_related('product', 'smart_product')
        
        history = {
            'total_orders': recent_orders.count(),
            'categories': {},
            'products': {},
            'total_spent': 0,
            'avg_order_value': 0,
            'favorite_brands': [],
            'purchase_frequency': 0
        }
        
        for order in recent_orders:
            if order.product:
                product_name = order.product.name
                category = order.product.category.name if order.product.category else 'unknown'
            elif order.smart_product:
                product_name = order.smart_product.name
                category = order.smart_product.category or 'unknown'
            else:
                continue
            
            # Track categories
            if category not in history['categories']:
                history['categories'][category] = {'count': 0, 'spending': 0}
            history['categories'][category]['count'] += order.quantity
            history['categories'][category]['spending'] += float(order.subtotal)
            
            # Track products
            if product_name not in history['products']:
                history['products'][product_name] = {'count': 0, 'last_purchase': None}
            history['products'][product_name]['count'] += order.quantity
            history['products'][product_name]['last_purchase'] = order.order.created_at.date()
            
            history['total_spent'] += float(order.subtotal)
        
        if history['total_orders'] > 0:
            history['avg_order_value'] = history['total_spent'] / history['total_orders']
            history['purchase_frequency'] = history['total_orders'] / 90  # orders per day
        
        return history
    
    def _analyze_user_preferences(self, user: User) -> Dict:
        """Analyze user preferences and behavioral patterns"""
        if not user:
            return {}
        
        history = self._get_user_purchase_history(user)
        
        preferences = {
            'preferred_categories': [],
            'price_segment': 'mid_range',
            'brand_loyalty': 0.5,
            'novelty_seeking': 0.5,
            'seasonal_bias': {},
            'weekend_shopping': False
        }
        
        # Analyze preferred categories
        if history['categories']:
            sorted_categories = sorted(
                history['categories'].items(), 
                key=lambda x: x[1]['count'], 
                reverse=True
            )
            preferences['preferred_categories'] = [cat[0] for cat in sorted_categories[:3]]
        
        # Analyze price segment
        if history['avg_order_value'] > 0:
            if history['avg_order_value'] < 500:
                preferences['price_segment'] = 'budget'
            elif history['avg_order_value'] > 1500:
                preferences['price_segment'] = 'premium'
            else:
                preferences['price_segment'] = 'mid_range'
        
        # Calculate novelty seeking (tendency to try new products)
        total_products = len(history['products'])
        repeat_purchases = sum(1 for p in history['products'].values() if p['count'] > 1)
        if total_products > 0:
            preferences['novelty_seeking'] = 1 - (repeat_purchases / total_products)
        
        return preferences
    
    def _score_product_candidate(
        self, 
        product, 
        product_type: str, 
        user_history: Dict, 
        user_preferences: Dict, 
        festival_info: Dict,
        context: Dict
    ) -> Optional[Dict]:
        """Score a product candidate for recommendation"""
        
        try:
            # Basic product information
            if product_type == 'regular':
                product_id = product.id
                product_name = product.name
                category = product.category.name if product.category else 'unknown'
                price = float(product.price)
                stock = getattr(product, 'stock_quantity', 100) or 100
            else:  # smart product
                product_id = product.id
                product_name = product.name
                category = product.category or 'unknown'
                price = float(product.price)
                stock = product.stock_quantity or 0
            
            if stock <= 0:
                return None
            
            # Initialize scores
            demand_score = 0
            personalization_score = 0
            seasonal_score = 0
            festival_score = 0
            reasons = []
            
            # 1. Demand Score (based on predicted demand)
            predicted_demand = getattr(product, 'predicted_demand_7d', 0) or 10
            demand_score = min(predicted_demand / 50.0 * 100, 100)  # Normalize to 0-100
            
            if predicted_demand > 30:
                reasons.append("High demand predicted")
            elif predicted_demand > 15:
                reasons.append("Moderate demand expected")
            
            # 2. Personalization Score
            if user_history and user_preferences:
                # Category preference
                if category in user_preferences.get('preferred_categories', []):
                    personalization_score += 40
                    reasons.append(f"Matches your preference for {category}")
                
                # Previous purchases
                if product_name in user_history.get('products', {}):
                    personalization_score += 30
                    last_purchase = user_history['products'][product_name]['last_purchase']
                    if last_purchase and (timezone.now().date() - last_purchase).days > 30:
                        reasons.append("Time to restock favorite item")
                    else:
                        reasons.append("Previously purchased")
                
                # Price segment matching
                price_segment = user_preferences.get('price_segment', 'mid_range')
                if ((price_segment == 'budget' and price < 200) or
                    (price_segment == 'mid_range' and 200 <= price <= 800) or
                    (price_segment == 'premium' and price > 800)):
                    personalization_score += 20
                    reasons.append(f"Fits your {price_segment} budget")
            
            # 3. Seasonal Score
            current_month = timezone.now().month
            current_season = self._get_season_from_month(current_month)
            
            if hasattr(product, 'peak_season'):
                if product.peak_season == current_season:
                    seasonal_score += 50
                    reasons.append(f"Perfect for {current_season} season")
                elif product.peak_season == 'all_year':
                    seasonal_score += 20
                    reasons.append("Popular year-round")
            
            # Weekend bonus
            if timezone.now().date().weekday() >= 5:  # Weekend
                if hasattr(product, 'weekend_boost') and product.weekend_boost:
                    seasonal_score += 15
                    reasons.append("Weekend favorite")
            
            # 4. Festival Score
            active_festivals = festival_info.get('active_festivals', [])
            if active_festivals:
                festival_boost = festival_info.get('festival_boost_multiplier', 1.0)
                festival_score = (festival_boost - 1) * 100
                
                for festival in active_festivals:
                    festival_products = festival.get('products', [])
                    if any(fp in product_name.lower() for fp in festival_products):
                        festival_score += 25
                        reasons.append(f"Perfect for {festival['name']}")
            
            # 5. Calculate total score
            total_score = (
                demand_score * 0.3 +
                personalization_score * 0.25 +
                seasonal_score * 0.25 +
                festival_score * 0.2
            )
            
            # Confidence based on amount of data
            confidence = 0.7  # Base confidence
            if user_history.get('total_orders', 0) > 10:
                confidence += 0.15
            if predicted_demand > 0:
                confidence += 0.10
            if len(reasons) > 2:
                confidence += 0.05
            confidence = min(confidence, 1.0)
            
            # Primary reason (strongest factor)
            primary_reason = "Recommended for you"
            if festival_score > 20:
                primary_reason = f"Perfect for {active_festivals[0]['name'] if active_festivals else 'festival'}"
            elif personalization_score > 30:
                primary_reason = "Based on your preferences"
            elif demand_score > 60:
                primary_reason = "High demand predicted"
            elif seasonal_score > 30:
                primary_reason = f"Great for {current_season}"
            
            return {
                'product_id': product_id,
                'product_name': product_name,
                'category': category,
                'price': price,
                'product_type': product_type,
                'total_score': total_score,
                'demand_score': demand_score,
                'personalization_score': personalization_score,
                'seasonal_score': seasonal_score,
                'festival_score': festival_score,
                'predicted_demand': predicted_demand,
                'reasons': reasons,
                'primary_reason': primary_reason,
                'confidence': confidence,
                'stock': stock
            }
            
        except Exception as e:
            print(f"Error scoring product {product}: {e}")
            return None
    
    def _apply_diversity_ranking(self, candidates: List[Dict], limit: int) -> List[Dict]:
        """Apply diversity constraints and final ranking"""
        
        if not candidates:
            return []
        
        # Sort by total score
        candidates.sort(key=lambda x: x['total_score'], reverse=True)
        
        final_recommendations = []
        category_counts = {}
        seen_products = set()
        
        for candidate in candidates:
            if len(final_recommendations) >= limit:
                break
            
            category = candidate['category']
            product_name = candidate['product_name']
            
            # Skip if already recommended
            if product_name in seen_products:
                continue
            
            # Apply category diversity constraint
            if category_counts.get(category, 0) >= self.max_items_per_category:
                continue
            
            # Calculate diversity factor
            diversity_factor = 1.0
            if category in category_counts:
                diversity_factor = 1.0 - (category_counts[category] / self.max_items_per_category) * 0.3
            
            candidate['diversity_factor'] = diversity_factor
            candidate['total_score'] *= diversity_factor
            
            final_recommendations.append(candidate)
            category_counts[category] = category_counts.get(category, 0) + 1
            seen_products.add(product_name)
        
        return final_recommendations
    
    def _get_season_from_month(self, month: int) -> str:
        """Get season from month number"""
        season_map = {
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'monsoon', 10: 'monsoon', 11: 'monsoon'
        }
        return season_map.get(month, 'all_year')
    
    def export_recommendations_json(self, recommendations: List[Dict], filename: str = None) -> str:
        """
        Export recommendations in the specified JSON format
        """
        if filename is None:
            filename = f"recommendations_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Format for JSON export
        export_data = {
            'metadata': {
                'generated_at': timezone.now().isoformat(),
                'total_recommendations': len(recommendations),
                'model_version': '1.0',
                'algorithm': 'advanced_ml_personalized'
            },
            'recommendations': []
        }
        
        for rec in recommendations:
            export_rec = {
                'user_id': rec['user_id'],
                'item_id': rec['item_id'],
                'item_name': rec['item_name'],
                'category': rec['category'],
                'price': rec['price'],
                'score': rec['score'],
                'reason': rec['reason'],
                'detailed_reasons': rec['detailed_reasons'],
                'forecast_date': rec['forecast_date'],
                'predicted_demand': rec['predicted_demand'],
                'confidence': rec['confidence'],
                'rank': rec['rank']
            }
            export_data['recommendations'].append(export_rec)
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Recommendations exported to {filename}")
        return filename


# Factory function
def create_advanced_recommendation_system():
    """Factory function to create the advanced recommendation system"""
    return AdvancedRecommendationForecastSystem()