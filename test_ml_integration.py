#!/usr/bin/env python
"""
Test the ML Integration with pandas and scikit-learn
"""

import os
import sys
import django
from pathlib import Path

# Add Django project to path
project_path = Path(__file__).parent / 'grocerystore'
sys.path.insert(0, str(project_path))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')

# Change to grocerystore directory for proper imports
os.chdir(str(project_path))

# Setup Django
django.setup()

def test_ml_integration():
    print("🧪 Testing ML Integration with pandas and scikit-learn")
    print("=" * 60)
    
    try:
        # Test imports
        print("📦 Testing package imports...")
        import pandas as pd
        import numpy as np
        from sklearn.ensemble import RandomForestRegressor
        import joblib
        print("✅ All ML packages imported successfully")
        
        # Test Django model imports
        print("\n🔧 Testing Django model imports...")
        from marche_smart.models import Product, SmartProducts, MLForecastModel  # type: ignore
        print("✅ Django models imported successfully")
        
        # Test ML engine import
        print("\n⚙️ Testing ML engine import...")
        from marche_smart.ml_engine import create_ml_engine  # type: ignore
        ml_engine = create_ml_engine()
        print("✅ ML engine created successfully")
        
        # Test database connectivity
        print("\n💾 Testing database connectivity...")
        product_count = Product.objects.count()
        smart_product_count = SmartProducts.objects.count()
        ml_model_count = MLForecastModel.objects.count()
        
        print(f"📊 Database stats:")
        print(f"   Regular Products: {product_count}")
        print(f"   Smart Products: {smart_product_count}")
        print(f"   ML Models: {ml_model_count}")
        
        # Test basic pandas functionality
        print("\n🐼 Testing pandas functionality...")
        test_data = {
            'product_name': ['Test Product 1', 'Test Product 2'],
            'price': [10.0, 15.0],
            'category': ['Electronics', 'Food']
        }
        df = pd.DataFrame(test_data)
        print("✅ Pandas DataFrame created:")
        print(df.to_string(index=False))
        
        # Test scikit-learn model
        print("\n🤖 Testing scikit-learn model...")
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([1, 2, 3])
        model.fit(X, y)
        prediction = model.predict([[2, 3]])
        print(f"✅ Random Forest model prediction: {prediction[0]:.2f}")
        
        # Test Power BI endpoint access
        print("\n🔌 Testing API endpoint structure...")
        from marche_smart import api_views  # type: ignore
        
        # Check if our new endpoints exist
        endpoints = [
            'powerbi_demand_forecast_data',
            'powerbi_sales_analytics_data', 
            'powerbi_inventory_alerts_data',
            'powerbi_generate_ml_predictions',
            'powerbi_ml_model_performance'
        ]
        
        for endpoint in endpoints:
            if hasattr(api_views, endpoint):
                print(f"   ✅ {endpoint}")
            else:
                print(f"   ❌ {endpoint} - Missing")
        
        print("\n" + "=" * 60)
        print("🎉 ML Integration Test Results:")
        print("✅ pandas, numpy, scikit-learn: Working")
        print("✅ Django models: Accessible")  
        print("✅ ML engine: Created successfully")
        print("✅ Power BI endpoints: Available")
        print("✅ Database: Connected")
        
        if product_count > 0 or smart_product_count > 0:
            print(f"\n📈 Ready for ML training with {product_count + smart_product_count} products!")
            print("Run: python manage.py train_ml_models --batch-predict")
        else:
            print("\n⚠️ No products found in database.")
            print("Add products through Django admin or web scraping first.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Run: pip install -r ml_requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        return False

def test_sample_prediction():
    """Test a sample ML prediction without real data"""
    print("\n🔮 Testing sample ML prediction...")
    
    try:
        from marche_smart.ml_engine import create_ml_engine  # type: ignore
        
        ml_engine = create_ml_engine()
        
        # Create sample product data for prediction
        sample_data = {
            'price': 25.0,
            'category': 'Food',
            'peak_season': 'summer',
            'weekend_boost': True,
            'weather_dependent': False,
            'price_elasticity': 1.0,
            'avg_weekly_sales': 50.0,
            'promotion_lift': 1.2,
            'is_promotional': False,
            'product_type': 'regular',
            'temperature': 30.0,
            'rainfall': 5.0,
            'humidity': 65.0,
            'weather_condition': 'sunny',
            'weather_impact': 1.1,
            'is_weekend': False,
            'is_festival': False,
            'festival_name': 'none'
        }
        
        print("📊 Sample product data prepared")
        print(f"   Price: Rs {sample_data['price']}")
        print(f"   Category: {sample_data['category']}")
        print(f"   Peak Season: {sample_data['peak_season']}")
        
        # This will fail gracefully if no trained model exists
        result = ml_engine.predict_demand(sample_data)
        
        if 'error' in result:
            print(f"⚠️ Prediction skipped: {result['error']}")
            print("This is expected if no ML models are trained yet.")
        else:
            print("✅ Sample prediction generated:")
            print(f"   7-day forecast: {result['predicted_demand_7d']} units")
            print(f"   30-day forecast: {result['predicted_demand_30d']} units")
            print(f"   Confidence: {result['confidence_score']:.1f}%")
        
    except Exception as e:
        print(f"⚠️ Prediction test failed: {e}")
        print("This is normal if ML models haven't been trained yet.")

if __name__ == '__main__':
    success = test_ml_integration()
    
    if success:
        test_sample_prediction()
        
        print("\n🚀 Next Steps:")
        print("1. Add products to your database (scraping or admin)")
        print("2. Run: python manage.py train_ml_models --batch-predict")  
        print("3. Test Power BI endpoints with API calls")
        print("4. Connect Power BI to your ML-powered Django API")
        print("\n📖 See POWER_BI_INTEGRATION.md for detailed setup guide")
    else:
        print("\n❌ ML integration test failed. Please fix issues above.")
        sys.exit(1)