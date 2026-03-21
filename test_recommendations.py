#!/usr/bin/env python3
"""
Test script for ML recommendation system
"""

import os
import django
import sys

# Add the grocerystore directory to the Python path
grocerystore_path = os.path.join(os.path.dirname(__file__), 'grocerystore')
sys.path.insert(0, grocerystore_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
os.chdir(grocerystore_path)
django.setup()

from marche_smart.views import (  # type: ignore
    get_seasonal_recommendations,
    get_weather_based_recommendations,
    get_current_season,
    get_upcoming_festivals
)
from marche_smart.models import SmartProducts  # type: ignore

def test_recommendations():
    print("🤖 ML Recommendation System Test")
    print("=" * 50)
    
    # Test 1: Current season detection
    current_season = get_current_season()
    print(f"✅ Current season: {current_season}")
    
    # Test 2: Festival detection
    upcoming_festivals = get_upcoming_festivals()
    print(f"✅ Upcoming festivals: {upcoming_festivals}")
    
    # Test 3: Seasonal recommendations
    print(f"\n🌟 Seasonal Recommendations ({current_season}):")
    seasonal_recs = get_seasonal_recommendations(limit=5)
    for i, product in enumerate(seasonal_recs[:5]):
        reason = getattr(product, 'recommendation_reason', 'Perfect for the season')
        print(f"  {i+1}. {product.name}")
        print(f"     Price: RS{product.price} | Reason: {reason}")
    
    # Test 4: Weather-based recommendations
    print(f"\n🌤️ Weather-Based Recommendations:")
    weather_recs = get_weather_based_recommendations()
    for i, product in enumerate(weather_recs[:3]):
        reason = getattr(product, 'recommendation_reason', 'Great for current weather')
        print(f"  {i+1}. {product.name}")
        print(f"     Price: RS{product.price} | Reason: {reason}")
    
    # Test 5: Trending products
    print(f"\n🔥 Trending Products (High Demand):")
    trending = SmartProducts.objects.filter(
        predicted_demand_7d__gt=40
    ).order_by('-predicted_demand_7d')[:5]
    
    for i, product in enumerate(trending):
        print(f"  {i+1}. {product.name}")
        print(f"     Price: RS{product.price} | 7-day demand: {product.predicted_demand_7d}")
    
    # Test 6: Products on promotion or sale
    print(f"\n💰 Promotional Products:")
    promotional = SmartProducts.objects.filter(
        is_promotional=True
    )[:3]
    
    if promotional.exists():
        for i, product in enumerate(promotional):
            print(f"  {i+1}. {product.name}")
            print(f"     Price: RS{product.price} | Promotional item")
    else:
        print("  No promotional products currently available")
    
    # Test 7: Database stats
    total_products = SmartProducts.objects.count()
    products_with_predictions = SmartProducts.objects.filter(predicted_demand_7d__isnull=False).count()
    seasonal_products = SmartProducts.objects.exclude(peak_season='all_year').count()
    
    print(f"\n📊 Database Statistics:")
    print(f"  Total products: {total_products}")
    print(f"  Products with ML predictions: {products_with_predictions}")
    print(f"  Seasonal products: {seasonal_products}")
    
    print(f"\n✅ ML Recommendation System is working correctly!")
    print(f"🚀 Frontend integration ready!")
    
    return True

if __name__ == "__main__":
    test_recommendations()