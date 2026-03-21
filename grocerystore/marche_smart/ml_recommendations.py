"""
Enhanced ML-based Contextual Recommendation Engine
Leverages historical data, seasonal patterns, user behavior, and real-time context
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum, Avg, F

from .models import (
    Product, SmartProducts, ProductRecommendationLog, OrderItem, 
    SeasonalSalesData, WeatherData, Cart, CartItem
)
from .ml_engine import create_ml_engine
from .festival_calendar import FestivalCalendar


class ContextualRecommendationEngine:
    """
    Advanced ML recommendation engine that uses contextual data:
    - Historical purchase patterns
    - Seasonal trends from trained models
    - Real-time user behavior
    - Weather and festival context
    """
    
    def __init__(self):
        self.ml_engine = create_ml_engine()
        self.festival_calendar = FestivalCalendar()
    
    def get_personalized_recommendations(
        self, 
        user: Optional[User] = None,
        context: Dict = None,
        algorithm: str = 'hybrid_ml',
        limit: int = 10
    ) -> Dict:
        """
        Generate personalized recommendations using ML predictions and contextual data
        
        Args:
            user: User object for personalized recommendations
            context: Additional context (location, time, weather, etc.)
            algorithm: Algorithm type ('ml_seasonal', 'ml_weather', 'user_behavior', 'hybrid_ml')  
            limit: Number of recommendations to return
            
        Returns:
            Dictionary with recommendations and context information
        """
        
        # Gather contextual data
        current_context = self._gather_context_data(user, context)
        
        # Generate recommendations based on algorithm
        if algorithm == 'ml_seasonal':
            recommendations = self._ml_seasonal_recommendations(current_context, limit)
        elif algorithm == 'ml_weather':
            recommendations = self._ml_weather_recommendations(current_context, limit)
        elif algorithm == 'user_behavior':
            recommendations = self._user_behavior_recommendations(user, current_context, limit)
        else:  # hybrid_ml
            recommendations = self._hybrid_ml_recommendations(user, current_context, limit)
        
        return {
            'algorithm': algorithm,
            'recommendations': recommendations,
            'context': current_context,
            'generated_at': timezone.now(),
            'personalized': user is not None,
            'total_recommendations': len(recommendations)
        }
    
    def _gather_context_data(self, user: Optional[User], additional_context: Dict = None) -> Dict:
        """Gather comprehensive contextual data for recommendations"""
        current_time = timezone.now()
        current_date = current_time.date()
        
        # Basic temporal context
        context = {
            'current_date': current_date,
            'current_time': current_time,
            'day_of_week': current_date.weekday(),
            'is_weekend': current_date.weekday() >= 5,
            'hour_of_day': current_time.hour,
            'month': current_date.month,
            'season': self._get_current_season(current_date.month),
        }
        
        # Festival context using the existing festival calendar
        festival_info = self.festival_calendar.get_current_date_info(current_date)
        context.update({
            'active_festivals': festival_info.get('active_festivals', []),
            'boost_festivals': festival_info.get('boost_active_festivals', []),
            'is_festival_period': len(festival_info.get('active_festivals', [])) > 0,
            'festival_boost_score': festival_info.get('festival_boost_multiplier', 1.0)
        })
        
        # Weather context (get latest weather data)
        try:
            latest_weather = WeatherData.objects.latest('date')
            context.update({
                'current_weather': {
                    'temperature': float(latest_weather.temperature_avg),
                    'condition': latest_weather.condition,
                    'humidity': float(latest_weather.humidity),
                    'rainfall': float(latest_weather.rainfall),
                    'impact_score': float(latest_weather.sales_impact_score)
                }
            })
        except WeatherData.DoesNotExist:
            context['current_weather'] = {
                'temperature': 25.0, 'condition': 'sunny', 'humidity': 60.0,
                'rainfall': 0.0, 'impact_score': 1.0
            }
        
        # User behavioral context
        if user:
            context['user_profile'] = self._get_user_behavioral_context(user)
        
        # Add any additional context
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def _get_user_behavioral_context(self, user: User) -> Dict:
        """Extract user behavioral patterns from historical data"""
        
        # Recent purchase history (last 30 days)
        recent_orders = OrderItem.objects.filter(
            order__user=user,  # Fixed: use 'user' field instead of 'customer'
            order__created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        # Category preferences
        category_preferences = recent_orders.values(
            'product__category__name'
        ).annotate(
            order_count=Count('id'),
            total_spent=Sum('subtotal')
        ).order_by('-order_count')
        
        # Purchase timing patterns - use Python to extract hours (SQLite compatible)
        purchase_hours_data = {}
        for oi in recent_orders.select_related('order')[:100]:
            hour = oi.order.created_at.hour
            purchase_hours_data[hour] = purchase_hours_data.get(hour, 0) + 1
        # Sort by count desc and pick top hours
        sorted_hours = sorted(purchase_hours_data.items(), key=lambda x: x[1], reverse=True)
        
        # Weekend vs weekday behavior
        weekend_count = recent_orders.filter(
            order__created_at__week_day__in=[1, 7]  # Sunday=1, Saturday=7
        ).count()
        weekday_count = recent_orders.exclude(
            order__created_at__week_day__in=[1, 7]
        ).count()
        
        # Price sensitivity (average price points)
        price_stats = recent_orders.aggregate(
            avg_price=Avg('product__price'),
            max_price=Avg('product__price'),
            min_price=Avg('product__price'),
            total_spent=Sum('subtotal')
        )
        
        return {
            'recent_order_count': recent_orders.count(),
            'preferred_categories': [cat['product__category__name'] for cat in category_preferences[:3]],
            'preferred_shopping_hours': [h[0] for h in sorted_hours[:2]],
            'weekend_preference': weekend_count > weekday_count,
            'average_order_value': price_stats['avg_price'] or 0,
            'price_segment': self._classify_price_segment(price_stats['avg_price'] or 0)
        }
    
    def _ml_seasonal_recommendations(self, context: Dict, limit: int) -> List[Dict]:
        """Generate recommendations using seasonal ML predictions"""
        
        # Get current season and festival context
        current_season = context['season']
        festival_boost = context['festival_boost_score']
        
        # Get products with high seasonal predictions for current context
        ml_predictions = []
        
        # Generate ML predictions for current seasonal context
        for product in Product.objects.filter(peak_season=current_season)[:20]:
            # Prepare contextual data for ML prediction
            product_context = {
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
                'temperature': context['current_weather']['temperature'],
                'rainfall': context['current_weather']['rainfall'],
                'humidity': context['current_weather']['humidity'],
                'weather_condition': context['current_weather']['condition'],
                'weather_impact': context['current_weather']['impact_score'],
                'is_weekend': context['is_weekend'],
                'is_festival': context['is_festival_period'],
                'festival_name': context['active_festivals'][0]['name'] if context['active_festivals'] else 'none'
            }
            
            # Get ML prediction
            prediction = self.ml_engine.predict_demand(product_context)
            
            if 'error' not in prediction:
                ml_predictions.append({
                    'product': product,
                    'prediction': prediction,
                    'contextual_score': prediction['predicted_demand'] * festival_boost
                })
        
        # Sort by contextual score and return top recommendations
        ml_predictions.sort(key=lambda x: x['contextual_score'], reverse=True)
        
        recommendations = []
        for pred in ml_predictions[:limit]:
            product = pred['product']
            prediction = pred['prediction']
            
            recommendations.append({
                'id': product.id,
                'type': 'regular_product',
                'name': product.name,
                'category': product.category.name if product.category else 'unknown',
                'price': float(product.price),
                'predicted_demand': prediction['predicted_demand'],
                'confidence_score': prediction['confidence_score'],
                'contextual_score': pred['contextual_score'],
                'reasons': [
                    f"Perfect for {current_season} season",
                    f"ML model predicts {prediction['predicted_demand']} demand",
                    f"High confidence ({prediction['confidence_score']:.1f}%)"
                ]
            })
        
        return recommendations
    
    def _ml_weather_recommendations(self, context: Dict, limit: int) -> List[Dict]:
        """Generate weather-sensitive recommendations using ML"""
        
        weather = context['current_weather']
        
        # Get weather-dependent products
        weather_products = SmartProducts.objects.filter(
            weather_dependent=True,
            stock_quantity__gt=0
        )
        
        recommendations = []
        for product in weather_products[:limit * 2]:  # Get more to filter 
            # Generate recommendation with weather context
            score = 70  # Base score
            reasons = []
            
            # Weather-based scoring
            if weather['condition'] == 'rainy' and 'umbrella' in product.name.lower():
                score += 25
                reasons.append("Perfect for rainy weather")
            elif weather['condition'] == 'sunny' and weather['temperature'] > 30:
                if any(term in product.name.lower() for term in ['cold', 'ice', 'cool']):
                    score += 20
                    reasons.append(f"Great for hot weather ({weather['temperature']}°C)")
            elif weather['condition'] == 'cold' and weather['temperature'] < 15:
                if any(term in product.name.lower() for term in ['warm', 'hot', 'tea']):
                    score += 15
                    reasons.append(f"Perfect for cold weather ({weather['temperature']}°C)")
            
            # Use existing ML prediction if available
            if hasattr(product, 'predicted_demand_7d') and product.predicted_demand_7d:
                score += min(product.predicted_demand_7d, 20)  # Add up to 20 points for high demand
                reasons.append(f"High predicted demand ({product.predicted_demand_7d} units/week)")
            
            if score > 70:  # Only include weather-relevant products
                recommendations.append({
                    'id': product.id,
                    'type': 'smart_product',
                    'name': product.name,
                    'category': product.category or 'unknown',
                    'price': float(product.price),
                    'weather_relevance_score': score,
                    'current_weather': weather['condition'],
                    'reasons': reasons
                })
        
        # Sort by weather relevance
        recommendations.sort(key=lambda x: x['weather_relevance_score'], reverse=True)
        return recommendations[:limit]
    
    def _user_behavior_recommendations(self, user: User, context: Dict, limit: int) -> List[Dict]:
        """Generate recommendations based on user behavioral patterns"""
        
        if not user:
            return []
        
        user_profile = context.get('user_profile', {})
        preferred_categories = user_profile.get('preferred_categories', [])
        
        recommendations = []
        
        # Category-based recommendations
        if preferred_categories:
            category_products = Product.objects.filter(
                category__name__in=preferred_categories,
                in_stock=True
            )
            
            for product in category_products[:limit]:
                score = 85  # Base score for preferred category
                reasons = [f"Based on your preference for {product.category.name} products"]
                
                # Check if user has purchased similar items
                previous_purchases = OrderItem.objects.filter(
                    order__user=user,  # Fixed: use 'user' field instead of 'customer'
                    product__category=product.category
                ).count()
                
                if previous_purchases > 0:
                    score += min(previous_purchases * 5, 15)
                    reasons.append(f"You've purchased {previous_purchases} similar items before")
                
                recommendations.append({
                    'id': product.id,
                    'type': 'regular_product',
                    'name': product.name,
                    'category': product.category.name,
                    'price': float(product.price),
                    'behavioral_score': score,
                    'reasons': reasons
                })
        
        # Time-based recommendations (shopping pattern)
        current_hour = context['current_time'].hour
        preferred_hours = user_profile.get('preferred_shopping_hours', [])
        
        if current_hour in preferred_hours:
            # Recommend products typically bought during this time
            time_based_products = OrderItem.objects.filter(
                order__user=user,  # Fixed: use 'user' field instead of 'customer'
                order__created_at__hour=current_hour
            ).values('product').annotate(
                purchase_count=Count('id')
            ).order_by('-purchase_count')[:5]
            
            for item in time_based_products:
                try:
                    product = Product.objects.get(id=item['product'])
                    recommendations.append({
                        'id': product.id,
                        'type': 'regular_product',
                        'name': product.name,
                        'category': product.category.name if product.category else 'unknown',
                        'price': float(product.price),
                        'behavioral_score': 90,
                        'reasons': [f"You often shop for this at {current_hour}:00"]
                    })
                except Product.DoesNotExist:
                    continue
        
        return sorted(recommendations, key=lambda x: x.get('behavioral_score', 0), reverse=True)[:limit]
    
    def _hybrid_ml_recommendations(self, user: Optional[User], context: Dict, limit: int) -> List[Dict]:
        """Combine multiple ML approaches for optimal recommendations"""
        
        # Get recommendations from different approaches
        seasonal_recs = self._ml_seasonal_recommendations(context, limit // 3)
        weather_recs = self._ml_weather_recommendations(context, limit // 3)
        behavior_recs = self._user_behavior_recommendations(user, context, limit // 3) if user else []
        
        # Combine and deduplicate
        all_recs = seasonal_recs + weather_recs + behavior_recs
        
        # Remove duplicates based on product ID
        seen_ids = set()
        unique_recs = []
        for rec in all_recs:
            if rec['id'] not in seen_ids:
                seen_ids.add(rec['id'])
                unique_recs.append(rec)
        
        # Score based on multiple factors
        for rec in unique_recs:
            total_score = 0
            scoring_factors = []
            
            # Add scores from different sources
            if 'contextual_score' in rec:
                total_score += rec['contextual_score'] * 0.4
                scoring_factors.append('seasonal_ml')
            
            if 'weather_relevance_score' in rec:
                total_score += rec['weather_relevance_score'] * 0.3
                scoring_factors.append('weather_context')
            
            if 'behavioral_score' in rec:
                total_score += rec['behavioral_score'] * 0.3
                scoring_factors.append('user_behavior')
            
            rec['hybrid_score'] = total_score
            rec['scoring_factors'] = scoring_factors
        
        # Sort by hybrid score
        unique_recs.sort(key=lambda x: x.get('hybrid_score', 0), reverse=True)
        
        return unique_recs[:limit]
    
    def _get_current_season(self, month: int) -> str:
        """Get current season based on month"""
        season_map = {
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'monsoon', 10: 'monsoon', 11: 'monsoon'
        }
        return season_map.get(month, 'all_year')
    
    def _classify_price_segment(self, avg_price: float) -> str:
        """Classify user into price segments"""
        if avg_price < 100:
            return 'budget'
        elif avg_price < 500:
            return 'mid_range'
        else:
            return 'premium'