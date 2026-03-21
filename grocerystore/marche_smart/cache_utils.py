"""
Cache utility functions for Marche Smart grocery store
Provides consistent caching strategies for products, recommendations, and analytics
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Union
from django.core.cache import cache
from django.conf import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Cache key prefixes
CACHE_PREFIXES = {
    'PRODUCT_LIST': 'products:list',
    'SMART_PRODUCT_LIST': 'smart_products:list', 
    'CATEGORY_LIST': 'categories:list',
    'CATEGORY_PRODUCTS': 'categories:products',
    'RECOMMENDATIONS': 'recommendations',
    'PRODUCT_DETAIL': 'products:detail',
    'USER_CART': 'users:cart',
    'ANALYTICS': 'analytics',
    'WEATHER': 'weather',
    'SEASONAL': 'seasonal',
    'TRENDING': 'trending',
}

def get_cache_timeout(cache_type: str) -> int:
    """Get cache timeout for specific cache type"""
    timeouts = getattr(settings, 'CACHE_TIMEOUTS', {})
    default_timeout = 300  # 5 minutes default
    return timeouts.get(cache_type, default_timeout)

def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate consistent cache key from arguments
    Args can include prefix, user_id, filters, etc.
    """
    key_parts = []
    
    # Add positional arguments
    for arg in args:
        if arg is not None:
            key_parts.append(str(arg))
    
    # Add keyword arguments (sorted for consistency)
    for key, value in sorted(kwargs.items()):
        if value is not None:
            if isinstance(value, (dict, list)):
                # Hash complex objects for consistent keys
                value_str = hashlib.md5(json.dumps(value, sort_keys=True).encode()).hexdigest()[:8]
                key_parts.append(f"{key}:{value_str}")
            else:
                key_parts.append(f"{key}:{value}")
    
    return ':'.join(key_parts)

def get_product_list_key(category_id: Optional[int] = None, 
                        search: Optional[str] = None,
                        in_stock_only: bool = False,
                        page: int = 1) -> str:
    """Generate cache key for product listing"""
    return generate_cache_key(
        CACHE_PREFIXES['PRODUCT_LIST'],
        category_id=category_id,
        search=search,
        in_stock_only=in_stock_only,
        page=page
    )

def get_smart_product_list_key(category: Optional[str] = None,
                              season: Optional[str] = None,
                              festival: Optional[str] = None,
                              in_stock_only: bool = False,
                              page: int = 1) -> str:
    """Generate cache key for smart product listing"""
    return generate_cache_key(
        CACHE_PREFIXES['SMART_PRODUCT_LIST'],
        category=category,
        season=season,
        festival=festival,
        in_stock_only=in_stock_only,
        page=page
    )

def get_recommendations_key(algorithm_type: str = 'hybrid',
                           limit: int = 10,
                           user_id: Optional[int] = None,
                           include_context: bool = False) -> str:
    """Generate cache key for recommendations"""
    return generate_cache_key(
        CACHE_PREFIXES['RECOMMENDATIONS'],
        algorithm_type,
        limit=limit,
        user_id=user_id,
        include_context=include_context
    )

def get_category_products_key(category_id: int) -> str:
    """Generate cache key for products in a category"""
    return generate_cache_key(
        CACHE_PREFIXES['CATEGORY_PRODUCTS'],
        category_id
    )

def get_user_cart_key(user_id: int) -> str:
    """Generate cache key for user's cart"""
    return generate_cache_key(
        CACHE_PREFIXES['USER_CART'],
        user_id
    )

def get_analytics_key(analytics_type: str, **filters) -> str:
    """Generate cache key for analytics data"""
    return generate_cache_key(
        CACHE_PREFIXES['ANALYTICS'],
        analytics_type,
        **filters
    )

class CacheManager:
    """
    Centralized cache management with fallback and invalidation
    """
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get value from cache with fallback handling"""
        try:
            return cache.get(key, default)
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return default
    
    @staticmethod
    def set(key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache with error handling"""
        if timeout is None:
            timeout = get_cache_timeout('DEFAULT')
        
        try:
            cache.set(key, value, timeout)
            logger.debug(f"Cached data with key: {key} for {timeout} seconds")
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache"""
        try:
            cache.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False
    
    @staticmethod
    def clear_pattern(pattern: str) -> int:
        """Clear cache keys matching pattern (requires django-redis)"""
        try:
            if hasattr(cache, 'delete_pattern'):
                deleted_count = cache.delete_pattern(f"*{pattern}*")
                logger.info(f"Cleared {deleted_count} cache keys matching pattern: {pattern}")
                return deleted_count
            return 0
        except Exception as e:
            logger.warning(f"Cache pattern clear failed for pattern {pattern}: {e}")
            return 0

def invalidate_product_cache(product_id: Optional[int] = None, category_id: Optional[int] = None):
    """
    Invalidate product-related cache entries
    Call this when products are created/updated/deleted
    """
    patterns_to_clear = [
        CACHE_PREFIXES['PRODUCT_LIST'],
        CACHE_PREFIXES['SMART_PRODUCT_LIST'],
        CACHE_PREFIXES['RECOMMENDATIONS'],
    ]
    
    if category_id:
        patterns_to_clear.append(f"{CACHE_PREFIXES['CATEGORY_PRODUCTS']}:{category_id}")
    
    for pattern in patterns_to_clear:
        CacheManager.clear_pattern(pattern)
    
    logger.info(f"Invalidated product cache for product_id={product_id}, category_id={category_id}")

def invalidate_recommendations_cache():
    """Invalidate all recommendation cache entries"""
    CacheManager.clear_pattern(CACHE_PREFIXES['RECOMMENDATIONS'])
    logger.info("Invalidated all recommendation caches")

def invalidate_user_cache(user_id: int):
    """Invalidate user-specific cache entries"""
    patterns_to_clear = [
        f"{CACHE_PREFIXES['USER_CART']}:{user_id}",
        f"*user_id:{user_id}*",
    ]
    
    for pattern in patterns_to_clear:
        CacheManager.clear_pattern(pattern)
    
    logger.info(f"Invalidated cache for user_id={user_id}")

def cache_function_result(cache_key: str, timeout: Optional[int] = None):
    """
    Decorator to cache function results
    Usage:
        @cache_function_result('my-cache-key', timeout=300)
        def expensive_function():
            return expensive_computation()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get from cache first
            cached_result = CacheManager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for function {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            CacheManager.set(cache_key, result, timeout)
            logger.debug(f"Cached result for function {func.__name__}")
            return result
        
        return wrapper
    return decorator

# Cache warming functions
def warm_popular_products_cache():
    """Pre-populate cache with popular products"""
    from .models import Product, SmartProducts
    
    logger.info("Starting cache warming for popular products")
    
    # Cache top products by category
    from .models import Category
    for category in Category.objects.all():
        key = get_category_products_key(category.id)
        if not CacheManager.get(key):
            products = Product.objects.filter(category=category, in_stock=True)[:20]
            product_data = list(products.values())
            CacheManager.set(key, product_data, get_cache_timeout('PRODUCTS'))
    
    # Cache seasonal recommendations
    seasonal_key = get_recommendations_key('seasonal')
    if not CacheManager.get(seasonal_key):
        # This would call your actual recommendation function
        pass
    
    logger.info("Cache warming completed")

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics and health information"""
    try:
        # Basic cache info
        stats = {
            'backend': str(cache.__class__),
            'cache_prefixes': CACHE_PREFIXES,
            'timeouts': getattr(settings, 'CACHE_TIMEOUTS', {}),
        }
        
        # Try to get Redis specific stats if available
        if hasattr(cache, '_cache') and hasattr(cache._cache, 'get_client'):
            redis_client = cache._cache.get_client()
            redis_info = redis_client.info()
            stats['redis_info'] = {
                'connected_clients': redis_info.get('connected_clients', 0),
                'used_memory_human': redis_info.get('used_memory_human', '0B'),
                'keyspace_hits': redis_info.get('keyspace_hits', 0),
                'keyspace_misses': redis_info.get('keyspace_misses', 0),
            }
            
            # Calculate hit ratio
            hits = redis_info.get('keyspace_hits', 0)
            misses = redis_info.get('keyspace_misses', 0)
            if hits + misses > 0:
                stats['hit_ratio'] = round(hits / (hits + misses) * 100, 2)
        
        return stats
    except Exception as e:
        logger.warning(f"Failed to get cache stats: {e}")
        return {'error': str(e)}