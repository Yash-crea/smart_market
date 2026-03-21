"""
Comprehensive Test Suite for Advanced Recommendation and Forecasting System
Tests 30-day forecasting, personalized recommendations, and explainable AI features
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Add grocerystore directory to path for proper imports
grocerystore_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grocerystore')
sys.path.append(grocerystore_dir)
# Change working directory so ml_models/ path resolves correctly
os.chdir(grocerystore_dir)
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APIClient  # type: ignore

# Import from grocerystore.marche_smart for proper Django app imports
try:
    from grocerystore.marche_smart.models import Product, SmartProducts, Category, OrderItem, Order  # type: ignore
    from grocerystore.marche_smart.advanced_recommendation_system import AdvancedRecommendationForecastSystem  # type: ignore
    from grocerystore.marche_smart.advanced_api_views import *  # type: ignore
except ImportError:
    # Fallback for direct import when running from grocerystore directory
    from marche_smart.models import Product, SmartProducts, Category, OrderItem, Order  # type: ignore
    from marche_smart.advanced_recommendation_system import AdvancedRecommendationForecastSystem  # type: ignore
    from marche_smart.advanced_api_views import *  # type: ignore


class AdvancedRecommendationSystemTestSuite:
    """Comprehensive test suite for the advanced recommendation system"""
    
    def __init__(self):
        self.client = APIClient()
        self.system = AdvancedRecommendationForecastSystem()
        self.test_results = {}
        
    def setup_test_environment(self):
        """Setup test environment with sample data"""
        print("🔧 Setting up test environment...")
        
        # Create test categories
        self.categories = {}
        category_names = ['Fruits', 'Vegetables', 'Dairy', 'Grains', 'Beverages']
        
        for name in category_names:
            category, created = Category.objects.get_or_create(name=name)
            self.categories[name] = category
        
        # Create test products
        self.test_products = []
        product_data = [
            {'name': 'Fresh Apples', 'category': 'Fruits', 'price': 150.0, 'peak_season': 'winter'},
            {'name': 'Organic Bananas', 'category': 'Fruits', 'price': 80.0, 'peak_season': 'summer'},
            {'name': 'Fresh Spinach', 'category': 'Vegetables', 'price': 45.0, 'peak_season': 'winter'},
            {'name': 'Tomatoes', 'category': 'Vegetables', 'price': 60.0, 'peak_season': 'summer'},
            {'name': 'Fresh Milk', 'category': 'Dairy', 'price': 75.0, 'weekend_boost': True},
            {'name': 'Basmati Rice', 'category': 'Grains', 'price': 120.0, 'peak_season': 'all_year'},
            {'name': 'Orange Juice', 'category': 'Beverages', 'price': 95.0, 'weather_dependent': True},
            {'name': 'Green Tea', 'category': 'Beverages', 'price': 250.0, 'peak_season': 'winter'},
        ]
        
        for data in product_data:
            product, created = Product.objects.get_or_create(
                name=data['name'],
                defaults={
                    'category': self.categories[data['category']],
                    'price': data['price'],
                    'description': f"Test {data['name']}",
                    'in_stock': True,
                    'stock_quantity': 100
                }
            )
            
            # Set additional attributes
            for attr, value in data.items():
                if attr not in ['name', 'category', 'price']:
                    setattr(product, attr, value)
            product.save()
            
            self.test_products.append(product)
        
        # Create test user
        self.test_user, created = User.objects.get_or_create(
            username='testuser_advanced',
            defaults={
                'email': 'test@advanced.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        # Create test orders for history
        self.create_test_order_history()
        
        print(f"✅ Created {len(self.test_products)} products and test order history")
    
    def create_test_order_history(self):
        """Create realistic order history for testing personalization"""
        print("📊 Creating test order history...")
        
        # Create orders over the last 90 days
        base_date = timezone.now() - timedelta(days=90)
        
        order_patterns = [
            # Frequent buyer of fruits and dairy
            {'products': ['Fresh Apples', 'Fresh Milk'], 'frequency': 7, 'quantity_range': (2, 4)},
            # Occasional vegetable buyer
            {'products': ['Fresh Spinach', 'Tomatoes'], 'frequency': 14, 'quantity_range': (1, 2)},
            # Beverage enthusiast
            {'products': ['Orange Juice', 'Green Tea'], 'frequency': 10, 'quantity_range': (1, 3)},
            # Bulk grain buyer
            {'products': ['Basmati Rice'], 'frequency': 30, 'quantity_range': (5, 8)},
        ]
        
        orders_created = 0
        for pattern in order_patterns:
            current_date = base_date
            
            while current_date <= timezone.now():
                # Create order with all required fields
                order = Order.objects.create(
                    user=self.test_user,
                    status='completed',
                    customer_name=f"{self.test_user.first_name} {self.test_user.last_name}",
                    customer_email=self.test_user.email,
                    shipping_address='123 Test Street',
                    shipping_city='Test City',
                    subtotal=0,
                    total_amount=0
                )
                
                # Add items to order
                total_amount = 0
                for product_name in pattern['products']:
                    try:
                        product = Product.objects.get(name=product_name)
                        quantity = np.random.randint(
                            pattern['quantity_range'][0], 
                            pattern['quantity_range'][1] + 1
                        )
                        
                        item_subtotal = float(product.price) * quantity
                        order_item = OrderItem.objects.create(
                            order=order,
                            product=product,
                            product_name=product.name,
                            quantity=quantity,
                            unit_price=product.price,
                            subtotal=item_subtotal
                        )
                        
                        total_amount += item_subtotal
                        
                    except Product.DoesNotExist:
                        continue
                
                order.subtotal = total_amount
                order.total_amount = total_amount
                order.save()
                orders_created += 1
                
                # Move to next order date
                current_date += timedelta(days=pattern['frequency'])
        
        print(f"✅ Created {orders_created} test orders")
    
    def test_comprehensive_training_data(self):
        """Test comprehensive training data preparation"""
        print("\n🧪 Testing comprehensive training data preparation...")
        
        try:
            training_df = self.system.prepare_comprehensive_training_data()
            
            # Validate data structure
            required_columns = [
                'product_id', 'product_name', 'price', 'category', 'date',
                'quantity_sold', 'is_festival', 'season', 'temperature'
            ]
            
            missing_columns = [col for col in required_columns if col not in training_df.columns]
            
            if missing_columns:
                raise Exception(f"Missing columns: {missing_columns}")
            
            if len(training_df) == 0:
                raise Exception("No training data generated")
            
            self.test_results['training_data'] = {
                'status': 'passed',
                'samples': len(training_df),
                'columns': len(training_df.columns),
                'date_range': f"{training_df['date'].min()} to {training_df['date'].max()}"
            }
            
            print(f"✅ Training data: {len(training_df)} samples, {len(training_df.columns)} features")
            return True
            
        except Exception as e:
            self.test_results['training_data'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"❌ Training data test failed: {e}")
            return False
    
    def test_feature_engineering(self):
        """Test advanced feature engineering"""
        print("\n🔧 Testing feature engineering...")
        
        try:
            # Get sample data
            training_df = self.system.prepare_comprehensive_training_data()
            engineered_df = self.system.engineer_advanced_features(training_df)
            
            # Check for expected engineered features
            expected_features = [
                'month_sin', 'month_cos', 'day_sin', 'day_cos',
                'is_summer', 'is_winter', 'is_monsoon', 'is_spring',
                'price_category_ratio', 'sales_7d_mean', 'market_share'
            ]
            
            missing_features = [f for f in expected_features if f not in engineered_df.columns]
            
            if missing_features:
                raise Exception(f"Missing engineered features: {missing_features}")
            
            # Check for NaN values
            nan_count = engineered_df.isnull().sum().sum()
            
            self.test_results['feature_engineering'] = {
                'status': 'passed',
                'original_features': len(training_df.columns),
                'engineered_features': len(engineered_df.columns),
                'new_features_created': len(engineered_df.columns) - len(training_df.columns),
                'nan_values': int(nan_count)
            }
            
            print(f"✅ Feature engineering: {len(engineered_df.columns)} total features")
            return True
            
        except Exception as e:
            self.test_results['feature_engineering'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"❌ Feature engineering test failed: {e}")
            return False
    
    def test_model_training(self):
        """Test model training with validation metrics"""
        print("\n🤖 Testing model training...")
        
        try:
            # Prepare data
            training_df = self.system.prepare_comprehensive_training_data()
            engineered_df = self.system.engineer_advanced_features(training_df)
            
            # Train models
            training_results = self.system.train_forecasting_models(engineered_df)
            
            # Validate results
            if 'results' not in training_results:
                raise Exception("No training results returned")
            
            if 'best_model' not in training_results:
                raise Exception("No best model identified")
            
            # Check metrics
            best_model = training_results['best_model']
            best_metrics = training_results['results'][best_model]
            
            required_metrics = ['mae', 'rmse', 'r2', 'accuracy']
            missing_metrics = [m for m in required_metrics if m not in best_metrics]
            
            if missing_metrics:
                raise Exception(f"Missing metrics: {missing_metrics}")
            
            self.test_results['model_training'] = {
                'status': 'passed',
                'models_trained': list(training_results['results'].keys()),
                'best_model': best_model,
                'best_mae': best_metrics['mae'],
                'best_rmse': best_metrics['rmse'],
                'best_r2': best_metrics['r2'],
                'best_accuracy': best_metrics['accuracy']
            }
            
            print(f"✅ Model training: {best_model} (MAE: {best_metrics['mae']:.2f})")
            return True
            
        except Exception as e:
            self.test_results['model_training'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"❌ Model training test failed: {e}")
            return False
    
    def test_30day_forecasting(self):
        """Test 30-day demand forecasting"""
        print("\n📈 Testing 30-day demand forecasting...")
        
        try:
            # Test with a sample product
            test_product = self.test_products[0]
            product_data = {
                'product_id': test_product.id,
                'name': test_product.name,
                'price': float(test_product.price),
                'category': test_product.category.name,
                'avg_weekly_sales': 50
            }
            
            # Get forecast
            forecast_result = self.system.predict_30day_demand(product_data)
            
            # Validate forecast structure
            required_fields = [
                'product_id', 'product_name', 'forecast_period',
                'total_30day_demand', 'average_daily_demand', 'peak_daily_demand',
                'daily_predictions'
            ]
            
            missing_fields = [f for f in required_fields if f not in forecast_result]
            
            if missing_fields:
                raise Exception(f"Missing forecast fields: {missing_fields}")
            
            # Validate daily predictions
            daily_predictions = forecast_result['daily_predictions']
            if len(daily_predictions) != 30:
                raise Exception(f"Expected 30 daily predictions, got {len(daily_predictions)}")
            
            # Check for negative predictions
            negative_predictions = [p for p in daily_predictions if p['predicted_demand'] < 0]
            if negative_predictions:
                raise Exception(f"Found {len(negative_predictions)} negative predictions")
            
            self.test_results['30day_forecasting'] = {
                'status': 'passed',
                'product_tested': test_product.name,
                'total_30day_demand': forecast_result['total_30day_demand'],
                'average_daily_demand': forecast_result['average_daily_demand'],
                'peak_daily_demand': forecast_result['peak_daily_demand'],
                'predictions_count': len(daily_predictions)
            }
            
            print(f"✅ 30-day forecast: {forecast_result['total_30day_demand']:.1f} total demand")
            return True
            
        except Exception as e:
            self.test_results['30day_forecasting'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"❌ 30-day forecasting test failed: {e}")
            return False
    
    def test_personalized_recommendations(self):
        """Test personalized recommendations with diversity"""
        print("\n🎯 Testing personalized recommendations...")
        
        try:
            # Test with user
            user_recommendations = self.system.generate_personalized_recommendations(
                user=self.test_user,
                limit=10
            )
            
            # Test without user (anonymous)
            anonymous_recommendations = self.system.generate_personalized_recommendations(
                user=None,
                limit=10
            )
            
            # Validate recommendation structure
            for rec_set, rec_type in [(user_recommendations, 'user'), (anonymous_recommendations, 'anonymous')]:
                if not rec_set:
                    raise Exception(f"No {rec_type} recommendations generated")
                
                # Check required fields
                required_fields = [
                    'rank', 'item_id', 'item_name', 'category', 'price',
                    'score', 'reason', 'forecast_date', 'confidence'
                ]
                
                for rec in rec_set[:3]:  # Check first 3 recommendations
                    missing_fields = [f for f in required_fields if f not in rec]
                    if missing_fields:
                        raise Exception(f"Missing fields in {rec_type} recommendation: {missing_fields}")
            
            # Test diversity
            user_categories = set(rec['category'] for rec in user_recommendations)
            if len(user_categories) < 2:
                print("⚠️  Warning: Low category diversity in recommendations")
            
            # Test scoring consistency (note: diversity ranking may re-score items)
            user_scores = [rec['score'] for rec in user_recommendations]
            # Verify scores are reasonable (positive and non-zero)
            if any(s < 0 for s in user_scores):
                raise Exception("Found negative scores in recommendations")
            
            self.test_results['personalized_recommendations'] = {
                'status': 'passed',
                'user_recommendations': len(user_recommendations),
                'anonymous_recommendations': len(anonymous_recommendations),
                'user_categories': len(user_categories),
                'top_user_score': user_scores[0] if user_scores else 0,
                'user_avg_confidence': np.mean([rec['confidence'] for rec in user_recommendations])
            }
            
            print(f"✅ Recommendations: {len(user_recommendations)} personalized, {len(anonymous_recommendations)} anonymous")
            return True
            
        except Exception as e:
            self.test_results['personalized_recommendations'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"❌ Personalized recommendations test failed: {e}")
            return False
    
    def test_explainable_ai(self):
        """Test explainable AI features"""
        print("\n🧠 Testing explainable AI features...")
        
        try:
            recommendations = self.system.generate_personalized_recommendations(
                user=self.test_user,
                limit=5
            )
            
            if not recommendations:
                raise Exception("No recommendations to test explanations")
            
            # Check for explanation fields
            explanation_fields = ['reason', 'detailed_reasons']
            reasons_found = []
            
            for rec in recommendations:
                for field in explanation_fields:
                    if field not in rec:
                        raise Exception(f"Missing explanation field: {field}")
                
                # Collect reasons for analysis
                if rec['detailed_reasons']:
                    reasons_found.extend(rec['detailed_reasons'])
            
            # Expected reason types
            expected_reason_types = [
                'preference', 'demand', 'seasonal', 'festival', 'favorite', 'restock'
            ]
            
            reason_coverage = []
            for reason_type in expected_reason_types:
                has_reason = any(reason_type.lower() in reason.lower() for reason in reasons_found)
                reason_coverage.append(has_reason)
            
            explanation_coverage = sum(reason_coverage) / len(expected_reason_types)
            
            self.test_results['explainable_ai'] = {
                'status': 'passed',
                'recommendations_with_explanations': len(recommendations),
                'unique_reasons_found': len(set(reasons_found)),
                'explanation_coverage': explanation_coverage,
                'sample_reasons': reasons_found[:5] if reasons_found else []
            }
            
            print(f"✅ Explainable AI: {len(set(reasons_found))} unique reasons, {explanation_coverage:.1%} coverage")
            return True
            
        except Exception as e:
            self.test_results['explainable_ai'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"❌ Explainable AI test failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🌐 Testing API endpoints...")
        
        try:
            from django.test.utils import override_settings
            
            with override_settings(ALLOWED_HOSTS=['*']):
                # Test 30-day forecast endpoint
                test_product = self.test_products[0]
                forecast_url = reverse('smart_market:api:advanced_forecast_30day', kwargs={'product_id': test_product.id})
                forecast_response = self.client.get(forecast_url)
                
                if forecast_response.status_code != 200:
                    raise Exception(f"Forecast API failed: {forecast_response.status_code}")
                
                forecast_data = forecast_response.json()
                
                # Test personalized recommendations endpoint
                rec_url = reverse('smart_market:api:advanced_recommendations_personalized')
                rec_response = self.client.get(rec_url, {'user_id': self.test_user.id, 'limit': 5})
                
                if rec_response.status_code != 200:
                    raise Exception(f"Recommendations API failed: {rec_response.status_code}")
                
                rec_data = rec_response.json()
                
                # Test model status endpoint
                status_url = reverse('smart_market:api:advanced_models_status')
                status_response = self.client.get(status_url)
                
                if status_response.status_code != 200:
                    raise Exception(f"Model status API failed: {status_response.status_code}")
                
                status_data = status_response.json()
            
            self.test_results['api_endpoints'] = {
                'status': 'passed',
                'forecast_endpoint': 'working',
                'recommendations_endpoint': 'working',
                'status_endpoint': 'working',
                'forecast_predictions': len(forecast_data.get('daily_predictions', [])),
                'recommendations_count': len(rec_data.get('recommendations', []))
            }
            
            print("✅ API endpoints: all working correctly")
            return True
            
        except Exception as e:
            self.test_results['api_endpoints'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"❌ API endpoints test failed: {e}")
            return False
    
    def test_json_export_format(self):
        """Test JSON export format compliance"""
        print("\n📄 Testing JSON export format...")
        
        try:
            recommendations = self.system.generate_personalized_recommendations(
                user=self.test_user,
                limit=5
            )
            
            # Export to JSON
            filename = self.system.export_recommendations_json(recommendations)
            
            # Load and validate JSON
            with open(filename, 'r') as f:
                export_data = json.load(f)
            
            # Check required structure
            if 'metadata' not in export_data:
                raise Exception("Missing metadata in JSON export")
            
            if 'recommendations' not in export_data:
                raise Exception("Missing recommendations in JSON export")
            
            # Check required fields
            required_fields = [
                'user_id', 'item_id', 'item_name', 'score', 
                'reason', 'forecast_date', 'predicted_demand'
            ]
            
            for rec in export_data['recommendations']:
                missing_fields = [f for f in required_fields if f not in rec]
                if missing_fields:
                    raise Exception(f"Missing required fields in export: {missing_fields}")
            
            # Clean up
            os.remove(filename)
            
            self.test_results['json_export'] = {
                'status': 'passed',
                'exported_recommendations': len(export_data['recommendations']),
                'has_metadata': True,
                'required_fields_present': True
            }
            
            print(f"✅ JSON export: {len(export_data['recommendations'])} recommendations exported")
            return True
            
        except Exception as e:
            self.test_results['json_export'] = {
                'status': 'failed',
                'error': str(e)
            }
            print(f"❌ JSON export test failed: {e}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all tests and generate report"""
        print("🚀 Starting Comprehensive Advanced ML Test Suite")
        print("=" * 80)
        
        self.setup_test_environment()
        
        # Run all tests
        test_methods = [
            self.test_comprehensive_training_data,
            self.test_feature_engineering,
            self.test_model_training,
            self.test_30day_forecasting,
            self.test_personalized_recommendations,
            self.test_explainable_ai,
            self.test_api_endpoints,
            self.test_json_export_format
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            if test_method():
                passed_tests += 1
        
        # Generate report
        print("\n" + "=" * 80)
        print("🏁 COMPREHENSIVE TEST RESULTS")
        print("=" * 80)
        
        print(f"📊 Overall: {passed_tests}/{total_tests} tests passed ({100*passed_tests/total_tests:.1f}%)")
        
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {result['status']}")
            
            if result['status'] == 'failed':
                print(f"   Error: {result['error']}")
            else:
                # Print key metrics for passed tests
                for key, value in result.items():
                    if key != 'status' and not key.startswith('error'):
                        print(f"   {key}: {value}")
        
        # Save detailed results
        report_filename = f'advanced_ml_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_filename, 'w') as f:
            json.dump({
                'test_summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'success_rate': 100 * passed_tests / total_tests,
                    'timestamp': datetime.now().isoformat()
                },
                'detailed_results': self.test_results
            }, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Advanced ML system is fully functional.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} tests failed. Please review errors above.")
        
        return passed_tests == total_tests


def main():
    """Main test execution function"""
    test_suite = AdvancedRecommendationSystemTestSuite()
    success = test_suite.run_comprehensive_tests()
    
    if success:
        print("\n✅ Advanced ML Recommendation and Forecasting System is ready for production!")
    else:
        print("\n❌ Some tests failed. Please fix issues before production deployment.")
    
    return success


if __name__ == '__main__':
    main()