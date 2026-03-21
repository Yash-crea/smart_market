"""
Management command to train the advanced recommendation and forecasting system
Usage: python manage.py train_advanced_models [--force] [--models model1,model2]
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from marche_smart.advanced_recommendation_system import AdvancedRecommendationForecastSystem
from marche_smart.models import MLForecastModel, Product, SmartProducts, OrderItem


class Command(BaseCommand):
    help = 'Train advanced recommendation and forecasting models with comprehensive validation'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force retrain models even if recently trained'
        )
        
        parser.add_argument(
            '--models',
            type=str,
            default='random_forest,gradient_boosting,linear_regression',
            help='Comma-separated list of models to train (default: all)'
        )
        
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Run comprehensive validation after training'
        )
        
        parser.add_argument(
            '--export-results',
            action='store_true',
            help='Export training results to JSON file'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting Advanced ML Training System'))
        self.stdout.write('=' * 80)
        
        try:
            # Initialize the system
            forecast_system = AdvancedRecommendationForecastSystem()
            
            # Parse model list
            model_list = [model.strip() for model in options['models'].split(',')]
            valid_models = ['random_forest', 'gradient_boosting', 'linear_regression']
            model_list = [m for m in model_list if m in valid_models]
            
            if not model_list:
                raise CommandError('No valid models specified. Valid options: random_forest, gradient_boosting, linear_regression')
            
            # Check if training is needed
            if not options['force']:
                recent_training = MLForecastModel.objects.filter(
                    model_type='advanced_forecast',
                    trained_at__gte=timezone.now() - timedelta(days=7)
                ).exists()
                
                if recent_training:
                    self.stdout.write(
                        self.style.WARNING('⚠️  Models were trained recently. Use --force to retrain.')
                    )
                    return
            
            # Check data availability
            total_orders = OrderItem.objects.count()
            total_products = Product.objects.count() + SmartProducts.objects.count()
            
            self.stdout.write(f'📊 Data Summary:')
            self.stdout.write(f'   • Total orders: {total_orders:,}')
            self.stdout.write(f'   • Total products: {total_products:,}')
            
            if total_orders < 100:
                raise CommandError(f'❌ Insufficient training data. Need at least 100 orders, found {total_orders}')
            
            # Step 1: Prepare training data
            self.stdout.write('\n🔄 Step 1: Preparing comprehensive training data...')
            training_df = forecast_system.prepare_comprehensive_training_data()
            
            self.stdout.write(f'   ✅ Prepared {len(training_df):,} training samples')
            self.stdout.write(f'   📅 Date range: {training_df["date"].min()} to {training_df["date"].max()}')
            
            # Step 2: Feature engineering
            self.stdout.write('\n🔧 Step 2: Engineering advanced features...')
            engineered_df = forecast_system.engineer_advanced_features(training_df)
            
            feature_cols = [col for col in engineered_df.columns if col not in ['date', 'quantity_sold']]
            self.stdout.write(f'   ✅ Created {len(feature_cols)} features')
            self.stdout.write(f'   📊 Final dataset: {engineered_df.shape[0]:,} samples × {engineered_df.shape[1]} features')
            
            # Step 3: Train models
            self.stdout.write(f'\n🤖 Step 3: Training {len(model_list)} models...')
            self.stdout.write(f'   Models: {", ".join(model_list)}')
            
            # Filter models to train
            original_models = forecast_system.forecast_models.copy()
            forecast_system.forecast_models = {k: v for k, v in original_models.items() if k in model_list}
            
            training_results = forecast_system.train_forecasting_models(engineered_df)
            
            # Step 4: Save results and validate
            self.stdout.write('\n💾 Step 4: Saving results and validating...')
            
            best_model = training_results['best_model']
            best_metrics = training_results['results'][best_model]
            
            for model_name, metrics in training_results['results'].items():
                try:
                    model_record, created = MLForecastModel.objects.update_or_create(
                        model_name=model_name,
                        model_type='advanced_forecast',
                        defaults={
                            'accuracy': metrics.get('accuracy', 0),
                            'rmse': metrics.get('rmse', 0),
                            'mae': metrics.get('mae', 0),
                            'r_squared': metrics.get('r2', 0),
                            'training_samples': len(training_df),
                            'feature_count': len(feature_cols),
                            'trained_at': timezone.now()
                        }
                    )
                    
                    status = "Created" if created else "Updated"
                    self.stdout.write(f'   ✅ {status} record for {model_name}')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Could not save {model_name}: {e}')
                    )
            
            # Display results
            self.stdout.write('\n📈 Training Results:')
            self.stdout.write('-' * 60)
            
            for model_name, metrics in training_results['results'].items():
                is_best = "🏆 " if model_name == best_model else "   "
                self.stdout.write(
                    f'{is_best}{model_name:20} | '
                    f'MAE: {metrics["mae"]:6.2f} | '
                    f'RMSE: {metrics["rmse"]:6.2f} | '
                    f'R²: {metrics["r2"]:5.3f} | '
                    f'Acc: {metrics["accuracy"]:5.1f}%'
                )
            
            self.stdout.write('-' * 60)
            self.stdout.write(f'🏆 Best Model: {best_model} (MAE: {best_metrics["mae"]:.2f})')
            
            # Step 5: Comprehensive validation
            if options['validate']:
                self.stdout.write('\n🧪 Step 5: Running comprehensive validation...')
                self._run_validation(forecast_system, engineered_df, training_results)
            
            # Step 6: Export results
            if options['export_results']:
                self.stdout.write('\n📤 Step 6: Exporting results...')
                self._export_results(training_results, len(training_df), len(feature_cols))
            
            # Success summary
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('✅ Advanced ML Training Completed Successfully!'))
            self.stdout.write(f'   • Trained {len(model_list)} models on {len(training_df):,} samples')
            self.stdout.write(f'   • Best model: {best_model} (MAE: {best_metrics["mae"]:.2f})')
            self.stdout.write(f'   • Training accuracy: {best_metrics["accuracy"]:.1f}%')
            self.stdout.write(f'   • Models saved to: ml_models/')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Training failed: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
            raise CommandError(f'Training failed: {str(e)}')
    
    def _run_validation(self, forecast_system, df, training_results):
        """Run comprehensive validation tests"""
        try:
            # Test recommendation generation
            self.stdout.write('   🎯 Testing recommendation generation...')
            recommendations = forecast_system.generate_personalized_recommendations(limit=10)
            self.stdout.write(f'   ✅ Generated {len(recommendations)} recommendations')
            
            # Test forecast generation
            self.stdout.write('   📊 Testing forecast generation...')
            sample_products = df[['product_id', 'product_name', 'price', 'category']].drop_duplicates().head(3)
            
            for _, product in sample_products.iterrows():
                product_data = {
                    'product_id': product['product_id'],
                    'name': product['product_name'],
                    'price': product['price'],
                    'category': product['category']
                }
                
                try:
                    forecast = forecast_system.predict_30day_demand(product_data)
                    if 'total_30day_demand' in forecast:
                        self.stdout.write(f'   ✅ {product["product_name"][:30]:30} | 30d forecast: {forecast["total_30day_demand"]:6.1f}')
                    else:
                        self.stdout.write(f'   ⚠️  {product["product_name"][:30]:30} | Forecast failed')
                except Exception as e:
                    self.stdout.write(f'   ❌ {product["product_name"][:30]:30} | Error: {str(e)[:30]}')
            
            self.stdout.write('   ✅ Validation completed')
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  Validation failed: {str(e)}'))
    
    def _export_results(self, training_results, sample_count, feature_count):
        """Export training results to JSON file"""
        try:
            import json
            
            export_data = {
                'training_summary': {
                    'timestamp': timezone.now().isoformat(),
                    'training_samples': sample_count,
                    'feature_count': feature_count,
                    'models_trained': list(training_results['results'].keys()),
                    'best_model': training_results['best_model']
                },
                'model_performance': training_results['results'],
                'validation_metrics': {
                    'best_model_mae': training_results['results'][training_results['best_model']]['mae'],
                    'best_model_rmse': training_results['results'][training_results['best_model']]['rmse'],
                    'best_model_r2': training_results['results'][training_results['best_model']]['r2']
                }
            }
            
            filename = f'advanced_ml_training_results_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.stdout.write(f'   ✅ Results exported to {filename}')
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  Export failed: {str(e)}'))