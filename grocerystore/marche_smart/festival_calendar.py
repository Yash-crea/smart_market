"""
Smart Festival Calendar System with Auto-Detection
Accurate 2026 festival dates with dynamic business logic
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class FestivalCalendar:
    """
    Smart festival detection system with accurate 2026 dates
    Auto-updates recommendations based on current date and approaching festivals
    """
    
    # Accurate 2026 Festival Calendar
    FESTIVALS_2026 = {
        'holi': {
            'date': datetime(2026, 3, 14),
            'name': 'Holi',
            'type': 'religious',
            'intensity': 8,  # Scale 1-10
            'products': ['colors', 'sweets', 'gujiya', 'thandai', 'bhang', 'snacks', 'traditional_sweets'],
            'boost_start_days': 7,   # Start boost 7 days before
            'boost_end_days': 2,     # Continue boost 2 days after
            'regional': 'hindu_community'
        },
        'ugadi': {
            'date': datetime(2026, 3, 19),
            'name': 'Ugadi (Telugu New Year)',
            'type': 'religious',
            'intensity': 9,  # Scale 1-10
            'products': ['sweets', 'traditional_items', 'new_clothes', 'decorations', 'puja_items'],
            'boost_start_days': 14,  # Start boost 14 days before
            'boost_end_days': 3,     # Continue boost 3 days after
            'regional': 'south_indian'
        },
        'eid_ul_fitr': {
            'date': datetime(2026, 3, 21),
            'name': 'Eid-Ul-Fitr',
            'type': 'religious',
            'intensity': 8,
            'products': ['dates', 'sweets', 'dry_fruits', 'meat', 'new_clothes', 'gifts'],
            'boost_start_days': 10,
            'boost_end_days': 2,
            'regional': 'muslim_community'
        },
        'labour_day': {
            'date': datetime(2026, 5, 1),
            'name': 'Labour Day',
            'type': 'national',
            'intensity': 4,
            'products': ['beverages', 'snacks', 'ready_meals'],
            'boost_start_days': 3,
            'boost_end_days': 1,
            'regional': 'national'
        },
        'assumption_of_mary': {
            'date': datetime(2026, 8, 15),
            'name': 'Assumption of Mary',
            'type': 'religious',
            'intensity': 6,
            'products': ['flowers', 'candles', 'sweets', 'wine'],
            'boost_start_days': 7,
            'boost_end_days': 1,
            'regional': 'christian_community'
        },
        'ganesh_chaturthi': {
            'date': datetime(2026, 9, 15),
            'name': 'Ganesh Chaturthi',
            'type': 'religious',
            'intensity': 9,
            'products': ['modak', 'sweets', 'flowers', 'puja_items', 'decorations', 'eco_ganesh_idols'],
            'boost_start_days': 14,
            'boost_end_days': 11,  # 11-day celebration
            'regional': 'maharashtrian'
        },
        'all_saints_day': {
            'date': datetime(2026, 11, 1),
            'name': "All Saints' Day",
            'type': 'religious',
            'intensity': 5,
            'products': ['flowers', 'candles', 'prayers_books'],
            'boost_start_days': 3,
            'boost_end_days': 1,
            'regional': 'christian_community'
        },
        'indentured_labourers': {
            'date': datetime(2026, 11, 2),
            'name': 'Arrival of Indentured Labourers',
            'type': 'historical',
            'intensity': 4,
            'products': ['cultural_items', 'traditional_food'],
            'boost_start_days': 2,
            'boost_end_days': 1,
            'regional': 'mauritian'
        },
        'diwali': {
            'date': datetime(2026, 11, 11),
            'name': 'Diwali',
            'type': 'religious',
            'intensity': 10,  # Highest priority
            'products': ['sweets', 'dry_fruits', 'diyas', 'decorations', 'fireworks', 'new_clothes', 'gold', 'silver'],
            'boost_start_days': 21,  # Start very early for Diwali
            'boost_end_days': 5,
            'regional': 'hindu_community'
        },
        'christmas': {
            'date': datetime(2026, 12, 25),
            'name': 'Christmas Day',
            'type': 'religious',
            'intensity': 9,
            'products': ['cake', 'wine', 'decorations', 'gifts', 'turkey', 'plum_cake', 'christmas_trees'],
            'boost_start_days': 30,  # Long preparation period
            'boost_end_days': 2,
            'regional': 'christian_community'
        }
    }
    
    @classmethod
    def get_current_date_info(cls, current_date: datetime = None) -> Dict:
        """Get comprehensive festival context for current date"""
        if current_date is None:
            current_date = datetime.now()
        
        # Handle both date and datetime objects
        if isinstance(current_date, date) and not isinstance(current_date, datetime):
            current_date = datetime.combine(current_date, datetime.min.time())
            
        active_festivals = []
        approaching_festivals = []
        boost_active_festivals = []
        
        for festival_key, festival_data in cls.FESTIVALS_2026.items():
            festival_date = festival_data['date']
            days_difference = (festival_date - current_date).days
            
            # Festival period logic
            boost_start = festival_data['boost_start_days']
            boost_end = festival_data['boost_end_days']
            
            # Check if we're in boost period (before festival)
            if -boost_end <= days_difference <= boost_start:
                boost_active_festivals.append({
                    'key': festival_key,
                    'name': festival_data['name'],
                    'days_away': days_difference,
                    'intensity': festival_data['intensity'],
                    'products': festival_data['products'],
                    'boost_multiplier': cls._calculate_boost_multiplier(days_difference, festival_data),
                    'phase': cls._get_festival_phase(days_difference)
                })
            
            # Active festival (today is festival day ± boost_end days)
            if abs(days_difference) <= boost_end:
                active_festivals.append({
                    'key': festival_key,
                    'name': festival_data['name'],
                    'intensity': festival_data['intensity'],
                    'products': festival_data['products']
                })
            
            # Approaching festivals (next 30 days)
            elif 0 <= days_difference <= 30:
                approaching_festivals.append({
                    'key': festival_key,
                    'name': festival_data['name'],
                    'days_away': days_difference,
                    'intensity': festival_data['intensity'],
                    'products': festival_data['products']
                })
        
        # Sort by priority (intensity and proximity)
        boost_active_festivals.sort(key=lambda x: (x['intensity'], -x['days_away']), reverse=True)
        approaching_festivals.sort(key=lambda x: x['days_away'])
        
        return {
            'current_date': current_date,
            'active_festivals': active_festivals,
            'approaching_festivals': approaching_festivals,
            'boost_active_festivals': boost_active_festivals,
            'season': cls._get_current_season(current_date),
            'total_festivals_this_month': len([f for f in cls.FESTIVALS_2026.values() 
                                             if f['date'].month == current_date.month]),
            'next_major_festival': cls._get_next_major_festival(current_date)
        }
    
    @classmethod
    def _calculate_boost_multiplier(cls, days_difference: int, festival_data: Dict) -> float:
        """
        Calculate dynamic boost multiplier based on proximity to festival
        Closer to festival = higher boost
        """
        intensity = festival_data['intensity']
        boost_start = festival_data['boost_start_days']
        
        if days_difference <= 0:  # Festival day or after
            return intensity / 10 * 2.0  # Maximum boost during festival
        elif days_difference <= 3:  # Very close (1-3 days)
            return intensity / 10 * 1.8
        elif days_difference <= 7:  # Close (4-7 days)
            return intensity / 10 * 1.5
        elif days_difference <= 14:  # Approaching (8-14 days)
            return intensity / 10 * 1.3
        else:  # Far but within boost period
            return intensity / 10 * 1.1
    
    @classmethod
    def _get_festival_phase(cls, days_difference: int) -> str:
        """Get current phase of festival preparation"""
        if days_difference <= 0:
            return 'active'
        elif days_difference <= 3:
            return 'imminent'
        elif days_difference <= 7:
            return 'preparation'
        elif days_difference <= 14:
            return 'early_preparation'
        else:
            return 'planning'
    
    @classmethod
    def _get_current_season(cls, current_date: datetime) -> str:
        """Get current season based on month"""
        month = current_date.month
        season_map = {
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'monsoon', 10: 'monsoon', 11: 'monsoon'
        }
        return season_map.get(month, 'unknown')
    
    @classmethod
    def _get_next_major_festival(cls, current_date: datetime) -> Optional[Dict]:
        """Get next major festival (intensity >= 8)"""
        major_festivals = [
            (key, data) for key, data in cls.FESTIVALS_2026.items()
            if data['intensity'] >= 8 and data['date'] >= current_date
        ]
        
        if major_festivals:
            next_festival = min(major_festivals, key=lambda x: x[1]['date'])
            key, data = next_festival
            days_away = (data['date'] - current_date).days
            
            return {
                'key': key,
                'name': data['name'],
                'date': data['date'],
                'days_away': days_away,
                'intensity': data['intensity']
            }
        return None
    
    @classmethod
    def get_festival_boost_for_product(cls, product_data: Dict, current_date: datetime = None) -> Dict:
        """
        Calculate festival-based boost for a specific product
        Returns boost multiplier and reasoning
        """
        if current_date is None:
            current_date = datetime.now()
            
        festival_info = cls.get_current_date_info(current_date)
        boost_multiplier = 1.0
        boost_reasons = []
        
        # Check for product in active boost festivals
        for festival in festival_info['boost_active_festivals']:
            product_keywords = product_data.get('name', '').lower()
            product_category = product_data.get('category', '').lower()
            
            # Check if product matches festival products
            festival_products = festival['products']
            for festival_product in festival_products:
                if (festival_product in product_keywords or 
                    festival_product in product_category or
                    cls._is_product_relevant_to_festival(product_data, festival_product)):
                    
                    current_multiplier = festival['boost_multiplier']
                    if current_multiplier > boost_multiplier:
                        boost_multiplier = current_multiplier
                        boost_reasons.append(
                            f"{festival['name']} in {festival['days_away']} days - {festival['phase']} phase"
                        )
        
        return {
            'boost_multiplier': boost_multiplier,
            'reasons': boost_reasons,
            'festival_context': festival_info['boost_active_festivals']
        }
    
    @classmethod
    def _is_product_relevant_to_festival(cls, product_data: Dict, festival_product: str) -> bool:
        """Smart matching of products to festival categories"""
        product_name = product_data.get('name', '').lower()
        product_category = product_data.get('category', '').lower()
        
        # Smart product matching rules
        festival_mappings = {
            'sweets': ['sweet', 'mithai', 'laddu', 'gulab jamun', 'rasgulla', 'barfi', 'halwa', 'chocolate'],
            'traditional_items': ['traditional', 'ethnic', 'cultural', 'religious'],
            'new_clothes': ['clothes', 'dress', 'shirt', 'saree', 'kurta', 'fashion'],
            'decorations': ['decoration', 'lights', 'rangoli', 'flowers', 'garland'],
            'puja_items': ['puja', 'religious', 'incense', 'diya', 'candle', 'prayer'],
            'dates': ['dates', 'khajur', 'dried fruit'],
            'dry_fruits': ['cashew', 'almond', 'pistachio', 'walnut', 'dry fruit', 'nuts'],
            'meat': ['chicken', 'mutton', 'beef', 'meat'],
            'gifts': ['gift', 'present', 'toy', 'jewelry'],
            'cake': ['cake', 'pastry', 'bakery'],
            'wine': ['wine', 'alcohol', 'beer', 'whiskey']
        }
        
        if festival_product in festival_mappings:
            return any(keyword in product_name or keyword in product_category 
                      for keyword in festival_mappings[festival_product])
        
        return festival_product in product_name or festival_product in product_category


def get_current_festival_recommendations(limit: int = 20, current_date: datetime = None) -> List[Dict]:
    """
    Get festival-based product recommendations for current date
    This replaces static festival logic with dynamic calendar-based recommendations
    """
    if current_date is None:
        current_date = datetime.now()
    
    festival_info = FestivalCalendar.get_current_date_info(current_date)
    
    # Log current festival context
    logger.info(f"Festival context for {current_date.date()}: "
               f"{len(festival_info['boost_active_festivals'])} active boost festivals, "
               f"{len(festival_info['approaching_festivals'])} approaching festivals")
    
    recommendations = []
    
    # Priority 1: Products for currently boosted festivals
    if festival_info['boost_active_festivals']:
        for festival in festival_info['boost_active_festivals'][:3]:  # Top 3 festivals
            festival_products = festival['products'][:5]  # Top 5 products per festival
            
            for product_type in festival_products:
                recommendations.append({
                    'product_type': product_type,
                    'festival': festival['name'],
                    'days_away': festival['days_away'],
                    'boost_multiplier': festival['boost_multiplier'],
                    'phase': festival['phase'],
                    'urgency': 'high' if festival['days_away'] <= 3 else 'medium',
                    'reason': f"Perfect for {festival['name']} ({festival['phase']} phase)"
                })
    
    # Priority 2: Seasonal recommendations
    season = festival_info['season']
    seasonal_products = {
        'spring': ['fresh_vegetables', 'light_clothes', 'flowers', 'health_drinks'],
        'summer': ['cold_drinks', 'ice_cream', 'cotton_clothes', 'sunscreen'],
        'monsoon': ['umbrellas', 'raincoats', 'hot_beverages', 'immunity_boosters'],
        'winter': ['warm_clothes', 'hot_drinks', 'soups', 'heaters']
    }
    
    if season in seasonal_products:
        for product_type in seasonal_products[season][:3]:
            recommendations.append({
                'product_type': product_type,
                'festival': f'{season.title()} Season',
                'boost_multiplier': 1.3,
                'phase': 'seasonal',
                'urgency': 'low',
                'reason': f'Perfect for {season} season'
            })
    
    return recommendations[:limit]


# Example usage for ML integration
def get_ml_festival_features(current_date: datetime = None) -> Dict:
    """
    Extract festival features for ML model training/prediction
    """
    festival_info = FestivalCalendar.get_current_date_info(current_date)
    
    features = {
        'days_to_next_major_festival': 365,  # Default if no festivals
        'festival_intensity_score': 0,
        'active_festivals_count': len(festival_info['active_festivals']),
        'boost_festivals_count': len(festival_info['boost_active_festivals']),
        'season_numeric': {'spring': 1, 'summer': 2, 'monsoon': 3, 'winter': 4}.get(festival_info['season'], 0),
        'month': current_date.month if current_date else datetime.now().month,
        'is_festival_period': len(festival_info['boost_active_festivals']) > 0
    }
    
    # Add features for specific upcoming festivals
    if festival_info['next_major_festival']:
        features['days_to_next_major_festival'] = festival_info['next_major_festival']['days_away']
        features['festival_intensity_score'] = festival_info['next_major_festival']['intensity']
    
    # Add boost multiplier for most intense current festival
    if festival_info['boost_active_festivals']:
        top_festival = festival_info['boost_active_festivals'][0]
        features['current_max_boost'] = top_festival['boost_multiplier']
        features['current_festival_phase'] = {
            'active': 4, 'imminent': 3, 'preparation': 2, 'early_preparation': 1, 'planning': 0
        }.get(top_festival['phase'], 0)
    else:
        features['current_max_boost'] = 1.0
        features['current_festival_phase'] = 0
    
    return features