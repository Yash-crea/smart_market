"""
ML Engine for Demand Forecasting
Integrates pandas, scikit-learn with Django models for real-time predictions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
import joblib
import os
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

from django.conf import settings
from django.utils import timezone
from .models import (
    Product, SmartProducts, SeasonalSalesData, WeatherData, 
    MLForecastModel, ForecastPrediction, OrderItem
)
from .festival_calendar import FestivalCalendar, get_current_festival_recommendations, get_ml_festival_features


class DemandForecastEngine:
    """
    Main ML engine for demand forecasting using pandas and scikit-learn
    Integrates with Django models to provide real-time predictions for API
    """
    
    def __init__(self):
        self.models_path = Path(settings.BASE_DIR) / 'ml_models'
        self.models_path.mkdir(exist_ok=True)
        
        # Initialize ML models
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression()
        }
        
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def prepare_training_data(self) -> pd.DataFrame:
        """
        Prepare training dataset from Django models using pandas
        Returns: DataFrame ready for ML training
        """
        print("🔄 Preparing training data from Django models...")
        
        # Get all products with their sales data
        products_data = []
        
        # Process regular products
        regular_products = Product.objects.all()
        for product in regular_products:
            sales_data = SeasonalSalesData.objects.filter(product=product)
            order_items = OrderItem.objects.filter(product=product)
            
            for sales in sales_data:
                # Get weather data for the same period
                weather = WeatherData.objects.filter(
                    date__year=sales.year, 
                    date__month=sales.month
                ).first()
                
                products_data.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_type': 'regular',
                    'price': float(product.price),
                    'category': product.category.name if product.category else 'unknown',
                    'year': sales.year,
                    'month': sales.month,
                    'season': sales.season,
                    'units_sold': sales.units_sold,
                    'total_sales': float(sales.total_sales),
                    'is_weekend': sales.is_weekend,
                    'is_festival': sales.is_festival_period,
                    'festival_name': sales.festival_name or 'none',
                    'performance_score': float(sales.performance_score),
                    'peak_season': product.peak_season,
                    'weekend_boost': product.weekend_boost,
                    'weather_dependent': product.weather_dependent,
                    'price_elasticity': float(product.price_elasticity),
                    'avg_weekly_sales': float(product.avg_weekly_sales),
                    'promotion_lift': float(product.promotion_lift),
                    'is_promotional': product.is_promotional,
                    # Weather features
                    'temperature': float(weather.temperature_avg) if weather else 25.0,
                    'rainfall': float(weather.rainfall) if weather else 0.0,
                    'humidity': float(weather.humidity) if weather else 60.0,
                    'weather_condition': weather.condition if weather else 'sunny',
                    'weather_impact': float(weather.sales_impact_score) if weather else 1.0,
                })
        
        # Process smart products
        smart_products = SmartProducts.objects.all()
        for product in smart_products:
            sales_data = SeasonalSalesData.objects.filter(smart_product=product)
            
            for sales in sales_data:
                weather = WeatherData.objects.filter(
                    date__year=sales.year, 
                    date__month=sales.month
                ).first()
                
                products_data.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_type': 'smart',
                    'price': float(product.price),
                    'category': product.category or 'unknown',
                    'year': sales.year,
                    'month': sales.month,
                    'season': sales.season,
                    'units_sold': sales.units_sold,
                    'total_sales': float(sales.total_sales),
                    'is_weekend': sales.is_weekend,
                    'is_festival': sales.is_festival_period,
                    'festival_name': sales.festival_name or 'none',
                    'performance_score': float(sales.performance_score),
                    'peak_season': product.peak_season,
                    'weekend_boost': product.weekend_boost,
                    'weather_dependent': product.weather_dependent,
                    'price_elasticity': float(product.price_elasticity),
                    'avg_weekly_sales': float(product.avg_weekly_sales),
                    'promotion_lift': float(product.promotion_lift),
                    'is_promotional': product.is_promotional,
                    'temperature': float(weather.temperature_avg) if weather else 25.0,
                    'rainfall': float(weather.rainfall) if weather else 0.0,
                    'humidity': float(weather.humidity) if weather else 60.0,
                    'weather_condition': weather.condition if weather else 'sunny',
                    'weather_impact': float(weather.sales_impact_score) if weather else 1.0,
                })
        
        df = pd.DataFrame(products_data)
        print(f"✅ Prepared {len(df)} training samples")
        return df
    
    def feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Advanced feature engineering using pandas
        """
        print("🔧 Engineering features...")
        
        # Time-based features
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Seasonal indicators
        df['is_summer'] = df['season'].isin(['summer']).astype(int)
        df['is_winter'] = df['season'].isin(['winter']).astype(int)
        df['is_monsoon'] = df['season'].isin(['monsoon']).astype(int)
        
        # Festival indicators using dynamic festival calendar
        festival_calendar = FestivalCalendar()
        
        def get_festival_features(row):
            # Get current festival information for the month
            current_date = timezone.datetime(row['year'], row['month'], 15).date()  # Mid-month as representative date
            date_info = festival_calendar.get_current_date_info(current_date)
            
            # Check if this period has any festival influence
            is_major = 0
            active_festivals = date_info.get('active_festivals', [])
            boost_festivals = date_info.get('boost_active_festivals', [])
            
            if active_festivals or boost_festivals:
                major_festivals = ['diwali', 'deepavali', 'christmas', 'new_year', 'eid', 'ram_navami', 'ugadi']
                # Check if any of the festivals are major festivals
                all_festivals = [f.get('name', f.get('key', '')).lower() for f in (active_festivals + boost_festivals)]
                is_major = 1 if any(any(major in festival_name for major in major_festivals) 
                                  for festival_name in all_festivals) else 0
            
            return is_major
        
        df['is_major_festival'] = df.apply(get_festival_features, axis=1)
        
        # Price features
        df['price_per_category'] = df.groupby('category')['price'].transform('mean')
        df['price_ratio'] = df['price'] / df['price_per_category']
        
        # Weather interaction features
        df['temp_category_interaction'] = df['temperature'] * df['category'].map(
            df.groupby('category')['units_sold'].mean().to_dict()
        )
        
        # Lag features (previous period sales)
        df_sorted = df.sort_values(['product_id', 'year', 'month'])
        df['prev_month_sales'] = df_sorted.groupby('product_id')['units_sold'].shift(1)
        df['prev_month_sales'] = df['prev_month_sales'].fillna(df['avg_weekly_sales'])
        
        # Moving averages
        df['sales_ma3'] = df_sorted.groupby('product_id')['units_sold'].rolling(3, min_periods=1).mean().reset_index(0, drop=True)
        
        print("✅ Feature engineering completed")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features and target for model training
        """
        # Encode categorical variables
        categorical_features = ['category', 'peak_season', 'weather_condition', 'festival_name', 'product_type']
        
        for feature in categorical_features:
            if feature not in self.label_encoders:
                self.label_encoders[feature] = LabelEncoder()
                df[f'{feature}_encoded'] = self.label_encoders[feature].fit_transform(df[feature].astype(str))
            else:
                df[f'{feature}_encoded'] = self.label_encoders[feature].transform(df[feature].astype(str))
        
        # Select features for training
        feature_columns = [
            'price', 'month', 'month_sin', 'month_cos',
            'is_weekend', 'is_festival', 'is_summer', 'is_winter', 
            'is_monsoon', 'is_major_festival',
            'weekend_boost', 'weather_dependent', 'price_elasticity',
            'avg_weekly_sales', 'promotion_lift', 'is_promotional',
            'temperature', 'rainfall', 'humidity', 'weather_impact',
            'price_ratio', 'temp_category_interaction',
            'prev_month_sales', 'sales_ma3',
            'category_encoded', 'peak_season_encoded', 
            'weather_condition_encoded', 'festival_name_encoded',
            'product_type_encoded'
        ]
        
        # Fill NaN values
        df[feature_columns] = df[feature_columns].fillna(df[feature_columns].median())
        
        X = df[feature_columns]
        y = df['units_sold']
        
        return X, y
    
    def train_models(self) -> Dict[str, float]:
        """
        Train multiple ML models and return performance metrics
        """
        print("🤖 Training ML models...")
        
        # Prepare data
        df = self.prepare_training_data()
        if len(df) == 0:
            print("⚠️ No training data available. Please populate sales data first.")
            return {}
        
        # Feature engineering
        df = self.feature_engineering(df)
        X, y = self.prepare_features(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train and evaluate models
        results = {}
        best_model = None
        best_score = float('inf')
        
        for model_name, model in self.models.items():
            print(f"Training {model_name}...")
            
            # Train model
            if model_name == 'linear_regression':
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
            
            # Calculate metrics
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            # Cross-validation
            if model_name == 'linear_regression':
                cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='neg_mean_absolute_error')
            else:
                cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_absolute_error')
            
            cv_mae = -cv_scores.mean()
            
            results[model_name] = {
                'mae': mae,
                'rmse': rmse,
                'r2': r2,
                'cv_mae': cv_mae,
                'accuracy': max(0, 100 * (1 - mae / y_test.mean()))
            }
            
            # Track best model
            if mae < best_score:
                best_score = mae
                best_model = model_name
            
            print(f"  MAE: {mae:.2f}, RMSE: {rmse:.2f}, R²: {r2:.3f}, CV MAE: {cv_mae:.2f}")
            
            # Save model
            model_path = self.models_path / f'{model_name}_model.joblib'
            joblib.dump(model, model_path)
            print(f"  Model saved to {model_path}")
            
            # Save to Django MLForecastModel
            ml_model, created = MLForecastModel.objects.get_or_create(
                name=f'Demand Forecast {model_name.replace("_", " ").title()}',
                defaults={
                    'model_type': model_name,
                    'forecast_type': 'demand',
                    'model_file_path': str(model_path),
                    'is_active': True if model_name == best_model else False
                }
            )
            
            # Update metrics
            ml_model.accuracy_score = Decimal(str(results[model_name]['accuracy']))
            ml_model.mae = Decimal(str(mae))
            ml_model.rmse = Decimal(str(rmse))
            ml_model.mape = Decimal(str(cv_mae))
            ml_model.last_trained = timezone.now()
            ml_model.save()
        
        # Save preprocessing objects
        joblib.dump(self.scaler, self.models_path / 'scaler.joblib')
        joblib.dump(self.label_encoders, self.models_path / 'label_encoders.joblib')
        
        print(f"✅ Best model: {best_model} (MAE: {best_score:.2f})")
        return results
    
    def predict_demand(self, product_data: Dict, days_ahead: int = 7) -> Dict:
        """
        Predict demand for a specific product using trained models
        Returns predictions formatted for Django API
        """
        try:
            # Load best model
            best_model_record = MLForecastModel.objects.filter(
                is_active=True, 
                forecast_type='demand'
            ).first()
            
            if not best_model_record:
                return {'error': 'No trained model available'}
            
            # Load model and preprocessing objects
            model = joblib.load(best_model_record.model_file_path)
            scaler = joblib.load(self.models_path / 'scaler.joblib')
            label_encoders = joblib.load(self.models_path / 'label_encoders.joblib')
            
            # Prepare features
            features_df = pd.DataFrame([product_data])
            
            # Feature engineering (same as training)
            current_date = datetime.now()
            features_df['month'] = current_date.month
            features_df['month_sin'] = np.sin(2 * np.pi * features_df['month'] / 12)
            features_df['month_cos'] = np.cos(2 * np.pi * features_df['month'] / 12)
            
            # Add derived features
            features_df['is_summer'] = (features_df['month'].isin([6, 7, 8])).astype(int)
            features_df['is_winter'] = (features_df['month'].isin([12, 1, 2])).astype(int)
            features_df['is_monsoon'] = (features_df['month'].isin([9, 10, 11])).astype(int)
            
            # Add festival features from dynamic calendar
            major_festivals = ['diwali', 'deepavali', 'christmas', 'new_year', 'eid', 'ram_navami']
            festival_name_str = str(features_df['festival_name'].iloc[0]).lower()
            features_df['is_major_festival'] = 1 if any(fest in festival_name_str for fest in major_festivals) else 0
            
            # Add missing features that are created during training
            # Price features (simplified for single product prediction)
            features_df['price_ratio'] = 1.0  # Default ratio when we don't have category averages
            
            # Weather interaction features (simplified)
            features_df['temp_category_interaction'] = features_df['temperature'] * 10.0  # Default interaction
            
            # Lag features (use average weekly sales as proxy for previous sales)
            features_df['prev_month_sales'] = features_df.get('avg_weekly_sales', 10.0)
            
            # Moving averages (use current average as proxy)
            features_df['sales_ma3'] = features_df.get('avg_weekly_sales', 10.0)
            
            # Encode categorical variables
            categorical_features = ['category', 'peak_season', 'weather_condition', 'festival_name', 'product_type']
            for feature in categorical_features:
                if feature in label_encoders and feature in features_df:
                    try:
                        features_df[f'{feature}_encoded'] = label_encoders[feature].transform(features_df[feature].astype(str))
                    except ValueError:
                        # Handle unseen categories
                        features_df[f'{feature}_encoded'] = 0
            
            # Select and scale features in the EXACT order the model expects
            feature_columns = [
                'price', 'month', 'month_sin', 'month_cos',
                'is_weekend', 'is_festival', 'is_summer', 'is_winter', 
                'is_monsoon', 'is_major_festival',
                'weekend_boost', 'weather_dependent', 'price_elasticity',
                'avg_weekly_sales', 'promotion_lift', 'is_promotional',
                'temperature', 'rainfall', 'humidity', 'weather_impact',
                'price_ratio', 'temp_category_interaction',
                'prev_month_sales', 'sales_ma3',
                'category_encoded', 'peak_season_encoded', 
                'weather_condition_encoded', 'festival_name_encoded',
                'product_type_encoded'
            ]
            
            # Fill missing features with defaults
            for col in feature_columns:
                if col not in features_df:
                    features_df[col] = 0
            
            X = features_df[feature_columns].fillna(0)
            
            # Make prediction
            if 'linear' in best_model_record.model_type:
                X_scaled = scaler.transform(X)
                prediction = model.predict(X_scaled)[0]
            else:
                prediction = model.predict(X)[0]
            
            # Calculate confidence interval (simple approach)
            mae = float(best_model_record.mae)
            confidence_lower = max(0, prediction - 1.96 * mae)
            confidence_upper = prediction + 1.96 * mae
            
            # Calculate for different horizons
            prediction_7d = int(prediction * (days_ahead / 7))
            prediction_30d = int(prediction * (days_ahead / 30)) if days_ahead >= 30 else int(prediction * 4)
            
            return {
                'predicted_demand': int(prediction),
                'predicted_demand_7d': prediction_7d,
                'predicted_demand_30d': prediction_30d,
                'confidence_lower': int(confidence_lower),
                'confidence_upper': int(confidence_upper),
                'confidence_score': float(best_model_record.accuracy_score),
                'model_used': best_model_record.name,
                'prediction_date': timezone.now().isoformat(),
                'features_used': feature_columns
            }
            
        except Exception as e:
            return {'error': f'Prediction failed: {str(e)}'}
    
    def batch_predict_all_products(self) -> List[Dict]:
        """
        Generate predictions for all products using dynamic festival data
        """
        print("🔮 Generating batch predictions for all products...")
        predictions = []
        
        # Get current festival context
        festival_calendar = FestivalCalendar()
        current_date = timezone.now().date()
        current_festival_info = festival_calendar.get_current_date_info(current_date)
        
        # Determine current festival status
        active_festivals = current_festival_info.get('active_festivals', [])
        boost_festivals = current_festival_info.get('boost_active_festivals', [])
        is_festival_period = len(active_festivals) > 0 or len(boost_festivals) > 0
        festival_name = active_festivals[0]['name'] if active_festivals else (boost_festivals[0]['name'] if boost_festivals else 'none')
        
        print(f"🎉 Festival Context: {festival_name}, Festival Period: {is_festival_period}")
        
        # Regular products
        for product in Product.objects.all():
            # Get festival boost for this specific product
            product_data = {
                'name': product.name,
                'category': product.category.name if product.category else 'unknown'
            }
            festival_features = festival_calendar.get_festival_boost_for_product(product_data, current_date)
            
            product_data = {
                'price': float(product.price),
                'category': product.category.name if product.category else 'unknown',
                'peak_season': product.peak_season,
                'weekend_boost': product.weekend_boost,
                'weather_dependent': product.weather_dependent,
                'price_elasticity': float(product.price_elasticity),
                'avg_weekly_sales': float(product.avg_weekly_sales),
                'promotion_lift': float(product.promotion_lift),
                'is_promotional': product.is_promotional,
                'product_type': 'regular',
                'temperature': 25.0,  # Default values - should be replaced with real weather data
                'rainfall': 0.0,
                'humidity': 60.0,
                'weather_condition': 'sunny',
                'weather_impact': 1.0,
                'is_weekend': current_date.weekday() >= 5,  # Saturday/Sunday
                'is_festival': is_festival_period,
                'festival_name': festival_name,
                **festival_features  # Add dynamic festival features
            }
            
            result = self.predict_demand(product_data)
            if 'error' not in result:
                predictions.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_type': 'regular',
                    'festival_boost': festival_features.get('festival_boost', 1.0),
                    **result
                })
                
                # Update Django model
                product.predicted_demand_7d = result['predicted_demand_7d']
                product.predicted_demand_30d = result['predicted_demand_30d']
                product.forecast_accuracy = Decimal(str(result['confidence_score']))
                product.last_forecast_update = timezone.now()
                product.save()
        
        # Smart products
        for product in SmartProducts.objects.all():
            # Get festival boost for this specific product
            product_data = {
                'name': product.name,
                'category': product.category or 'unknown'
            }
            festival_features = festival_calendar.get_festival_boost_for_product(product_data, current_date)
            
            product_data = {
                'price': float(product.price),
                'category': product.category or 'unknown',
                'peak_season': product.peak_season,
                'weekend_boost': product.weekend_boost,
                'weather_dependent': product.weather_dependent,
                'price_elasticity': float(product.price_elasticity),
                'avg_weekly_sales': float(product.avg_weekly_sales),
                'promotion_lift': float(product.promotion_lift),
                'is_promotional': product.is_promotional,
                'product_type': 'smart',
                'temperature': 25.0,
                'rainfall': 0.0,
                'humidity': 60.0,
                'weather_condition': 'sunny',
                'weather_impact': 1.0,
                'is_weekend': current_date.weekday() >= 5,  # Saturday/Sunday
                'is_festival': is_festival_period,
                'festival_name': festival_name,
                **festival_features  # Add dynamic festival features
            }
            
            result = self.predict_demand(product_data)
            if 'error' not in result:
                predictions.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_type': 'smart',
                    'festival_boost': festival_features.get('festival_boost', 1.0),
                    **result
                })
                
                # Update Django model
                product.predicted_demand_7d = result['predicted_demand_7d']
                product.predicted_demand_30d = result['predicted_demand_30d']
                product.forecast_accuracy = Decimal(str(result['confidence_score']))
                product.last_forecast_update = timezone.now()
                product.save()
        
        print(f"✅ Generated {len(predictions)} predictions with dynamic festival context")
        return predictions


def create_ml_engine() -> DemandForecastEngine:
    """Factory function to create ML engine instance"""
    return DemandForecastEngine()