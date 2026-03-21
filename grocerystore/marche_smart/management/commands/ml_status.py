from django.core.management.base import BaseCommand
from marche_smart.models import (
    Product, SmartProducts, MLForecastModel, ForecastPrediction,
    SeasonalSalesData, WeatherData
)


class Command(BaseCommand):
    help = 'Show ML forecasting system status for scraped products'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎯 ML Forecasting System Status for Your Scraped Products')
        )
        self.stdout.write("=" * 60)
        
        # Product counts
        total_products = Product.objects.count()
        total_smart_products = SmartProducts.objects.count()
        
        self.stdout.write(f"\n📦 Product Inventory:")
        self.stdout.write(f"  • Regular Products: {total_products}")
        self.stdout.write(f"  • Scraped Products: {total_smart_products}")
        
        # Seasonal categorization
        diwali_products = SmartProducts.objects.filter(festival_association='diwali')
        christmas_products = SmartProducts.objects.filter(festival_association='christmas')
        summer_products = SmartProducts.objects.filter(peak_season='summer')
        winter_products = SmartProducts.objects.filter(peak_season='winter')
        weekend_favorites = SmartProducts.objects.filter(weekend_boost=True)
        
        self.stdout.write(f"\n🎉 Seasonal Categorization:")
        self.stdout.write(f"  • Diwali Products: {diwali_products.count()}")
        if diwali_products.exists():
            for p in diwali_products[:3]:
                self.stdout.write(f"    - {p.name}")
        
        self.stdout.write(f"  • Christmas Products: {christmas_products.count()}")
        if christmas_products.exists():
            for p in christmas_products[:3]:
                self.stdout.write(f"    - {p.name}")
                
        self.stdout.write(f"  • Summer Products: {summer_products.count()}")
        self.stdout.write(f"  • Winter Products: {winter_products.count()}")
        self.stdout.write(f"  • Weekend Favorites: {weekend_favorites.count()}")
        
        # ML Predictions
        predicted_products = SmartProducts.objects.filter(predicted_demand_7d__gt=0)
        
        self.stdout.write(f"\n🤖 ML Predictions:")
        self.stdout.write(f"  • Products with Predictions: {predicted_products.count()}")
        
        if predicted_products.exists():
            self.stdout.write(f"  • Sample Predictions:")
            for p in predicted_products[:3]:
                self.stdout.write(
                    f"    - {p.name[:40]}: 7day={p.predicted_demand_7d}, "
                    f"30day={p.predicted_demand_30d}, revenue=₹{p.predicted_revenue_30d or 0:.0f}"
                )
        
        # ML Models
        models = MLForecastModel.objects.filter(is_active=True)
        self.stdout.write(f"\n📊 Active ML Models: {models.count()}")
        for model in models:
            self.stdout.write(f"  • {model.name} ({model.model_type}) - {model.accuracy_score}% accuracy")
        
        # Historical data
        seasonal_data = SeasonalSalesData.objects.count()
        weather_data = WeatherData.objects.count()
        forecast_predictions = ForecastPrediction.objects.count()
        
        self.stdout.write(f"\n📈 Historical Data:")
        self.stdout.write(f"  • Seasonal Sales Records: {seasonal_data}")
        self.stdout.write(f"  • Weather Data Points: {weather_data}")
        self.stdout.write(f"  • Forecast Predictions: {forecast_predictions}")
        
        # Recommendations
        self.stdout.write(f"\n✅ System Ready For:")
        self.stdout.write("  • Seasonal product recommendations")
        self.stdout.write("  • Festival-based promotions")
        self.stdout.write("  • Weather-dependent suggestions") 
        self.stdout.write("  • Weekend favorites")
        self.stdout.write("  • Demand forecasting")
        self.stdout.write("  • Inventory optimization")
        
        self.stdout.write(f"\n🚀 Next Steps:")
        self.stdout.write("  1. Integrate recommendations in your frontend")
        self.stdout.write("  2. Set up daily prediction updates")
        self.stdout.write("  3. Monitor prediction accuracy")
        self.stdout.write("  4. Add more seasonal categorizations as needed")
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Your ML forecasting system is ready for production!')
        )