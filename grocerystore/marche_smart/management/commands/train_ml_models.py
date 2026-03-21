"""
Management command to train ML models using pandas and scikit-learn
"""

from django.core.management.base import BaseCommand
from marche_smart.ml_engine import create_ml_engine


class Command(BaseCommand):
    help = 'Train ML models for demand forecasting using scikit-learn'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-type',
            type=str,
            choices=['random_forest', 'gradient_boosting', 'linear_regression', 'all'],
            default='all',
            help='Specific model type to train (default: all)'
        )
        parser.add_argument(
            '--batch-predict',
            action='store_true',
            help='Generate predictions for all products after training'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🤖 Starting ML Model Training with scikit-learn')
        )
        
        # Create ML engine
        ml_engine = create_ml_engine()
        
        # Train models
        self.stdout.write('📊 Training models with pandas data preparation...')
        results = ml_engine.train_models()
        
        if not results:
            self.stdout.write(
                self.style.ERROR(
                    '❌ Training failed - no data available.\n'
                    'Please ensure you have:\n'
                    '1. Products in your database\n'
                    '2. Historical sales data (SeasonalSalesData)\n'
                    '3. Weather data (optional but recommended)'
                )
            )
            return
        
        # Display results
        self.stdout.write('\n📈 Training Results:')
        self.stdout.write('=' * 60)
        
        best_model = None
        best_accuracy = 0
        
        for model_name, metrics in results.items():
            accuracy = metrics['accuracy']
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_model = model_name
            
            self.stdout.write(
                f"🔹 {model_name.replace('_', ' ').title()}:\n"
                f"   Accuracy: {accuracy:.1f}%\n"
                f"   MAE: {metrics['mae']:.2f}\n"
                f"   RMSE: {metrics['rmse']:.2f}\n"
                f"   R²: {metrics['r2']:.3f}\n"
                f"   Cross-validation MAE: {metrics['cv_mae']:.2f}\n"
            )
        
        self.stdout.write('=' * 60)
        self.stdout.write(
            self.style.SUCCESS(f'🏆 Best Model: {best_model} ({best_accuracy:.1f}% accuracy)')
        )
        
        # Batch prediction if requested
        if options['batch_predict']:
            self.stdout.write('\n🔮 Generating predictions for all products...')
            predictions = ml_engine.batch_predict_all_products()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Generated {len(predictions)} predictions\n'
                    'All product forecasts updated in database!\n'
                    'Predictions available via Django API for Power BI integration.'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🎉 ML Training Complete!\n'
                'Your models are ready to serve predictions via Django REST API.\n'
                'Use the API endpoints to feed data to Power BI dashboards.\n\n'
                '📡 API Integration:\n'
                '• GET /api/v1/ml-models/ - View trained models\n'
                '• GET /api/v1/products/ - Products with ML predictions\n'
                '• GET /api/v1/recommendations/ - ML-powered recommendations\n'
                '• GET /api/v1/forecast-predictions/ - Detailed forecasts\n\n'
                '🔄 To retrain models, run this command periodically or set up a cron job.'
            )
        )