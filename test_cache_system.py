#!/usr/bin/env python
"""
Cache System Test Script for Marche Smart Grocery Store

Run this script to test the caching implementation:
python manage.py shell < test_cache_system.py

Or run interactively:
python manage.py shell
exec(open('test_cache_system.py').read())
"""

import os
import sys
import django
from datetime import datetime

# Django setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'grocerystore'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')
os.chdir(os.path.join(os.path.dirname(__file__), 'grocerystore'))
django.setup()

from marche_smart.cache_utils import (  # type: ignore
    CacheManager, get_product_list_key, get_recommendations_key,
    invalidate_product_cache, get_cache_stats
)
from marche_smart.models import Product, Category, SmartProducts  # type: ignore

print("🧪 Testing Marche Smart Cache System")
print("=" * 50)

# Test 1: Basic cache operations
print("\n1. Testing basic cache operations...")
test_key = "test:cache:basic"
test_data = {"message": "Hello Cache!", "timestamp": str(datetime.now())}

# Set cache
success = CacheManager.set(test_key, test_data, 300)
print(f"   ✓ Cache set successful: {success}")

# Get cache
cached_result = CacheManager.get(test_key)
print(f"   ✓ Cache get successful: {cached_result is not None}")
print(f"   ✓ Data matches: {cached_result == test_data}")

# Test 2: Product cache keys
print("\n2. Testing cache key generation...")
product_key = get_product_list_key(category_id=1, search="apple", page=1)
print(f"   ✓ Product list key: {product_key}")

recommendation_key = get_recommendations_key("seasonal", limit=10)
print(f"   ✓ Recommendation key: {recommendation_key}")

# Test 3: Cache with actual data
print("\n3. Testing with real product data...")
try:
    # Cache some products
    products = Product.objects.all()[:5]
    cache_key = "test:products:sample"
    
    product_data = []
    for product in products:
        product_data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price)
        })
    
    CacheManager.set(cache_key, product_data, 300)
    
    # Retrieve from cache
    cached_products = CacheManager.get(cache_key)
    print(f"   ✓ Cached {len(product_data)} products")
    print(f"   ✓ Retrieved {len(cached_products) if cached_products else 0} products from cache")
    
except Exception as e:
    print(f"   ⚠ Product cache test failed: {e}")

# Test 4: Cache invalidation
print("\n4. Testing cache invalidation...")
try:
    invalidate_product_cache()
    print("   ✓ Product cache invalidation completed")
except Exception as e:
    print(f"   ⚠ Cache invalidation failed: {e}")

# Test 5: Cache statistics
print("\n5. Testing cache statistics...")
try:
    stats = get_cache_stats()
    print(f"   ✓ Cache backend: {stats.get('backend', 'unknown')}")
    
    if 'redis_info' in stats:
        redis_info = stats['redis_info']
        print(f"   ✓ Redis connected clients: {redis_info.get('connected_clients', 'N/A')}")
        print(f"   ✓ Redis memory usage: {redis_info.get('used_memory_human', 'N/A')}")
        print(f"   ✓ Cache hit ratio: {stats.get('hit_ratio', 'N/A')}%")
    else:
        print("   ⚠ Redis stats not available (using fallback cache)")
        
except Exception as e:
    print(f"   ⚠ Cache stats failed: {e}")

# Test 6: Model counts for verification
print("\n6. Database verification...")
try:
    product_count = Product.objects.count()
    category_count = Category.objects.count()
    smart_product_count = SmartProducts.objects.count()
    
    print(f"   ✓ Found {product_count} regular products")
    print(f"   ✓ Found {category_count} categories") 
    print(f"   ✓ Found {smart_product_count} smart products")
    
except Exception as e:
    print(f"   ⚠ Database query failed: {e}")

print("\n" + "=" * 50)
print("🎉 Cache system test completed!")
print("\nNext steps:")
print("1. Start Redis server: redis-server")
print("2. Test API endpoints with cache headers")
print("3. Monitor cache performance in production")
print("4. Use /api/v1/cache/stats/ for cache monitoring")