#!/usr/bin/env python3
"""
Web scraper for Winners.mu home appliances/supplies
Extracts product data and adds to Django grocery store
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin, urlparse
import re

# Add Django project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocerystore.settings')

# Initialize Django
import django
django.setup()

# Import Django modules (after setup)
try:
    from django.db import transaction
    from marche_smart.models import Category, Product, SmartProducts
except ImportError as e:
    print(f"Error importing Django models: {e}")
    print("Make sure you're running this from the correct directory with Django installed")
    sys.exit(1)

class WinnersScraper:
    def __init__(self):
        self.base_url = "https://www.winners.mu"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def clean_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return 0.0
        
        # Remove currency symbols and extra whitespace
        price_clean = re.sub(r'[^\d.,]', '', str(price_text))
        price_clean = price_clean.replace(',', '')
        
        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return 0.0
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        return ' '.join(text.strip().split())
    
    def get_product_image_url(self, img_element):
        """Extract full image URL from img element"""
        if not img_element:
            return None
            
        # Try different image source attributes
        for attr in ['src', 'data-src', 'data-original']:
            if img_element.has_attr(attr):
                img_url = img_element[attr]
                if img_url and img_url.startswith('http'):
                    return img_url
                elif img_url:
                    return urljoin(self.base_url, img_url)
        return None
    
    def scrape_products_page(self, url):
        """Scrape products from the main page"""
        print(f"🔍 Scraping: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Try multiple selectors for product containers
            product_selectors = [
                '.product-item',
                '.product-card', 
                '.item-box',
                '.product-container',
                '[data-product]',
                '.product',
                'article.product'
            ]
            
            product_elements = []
            for selector in product_selectors:
                elements = soup.select(selector)
                if elements:
                    product_elements = elements
                    print(f"✅ Found {len(elements)} products using selector: {selector}")
                    break
            
            if not product_elements:
                # Fallback: try to find divs with product-like classes
                product_elements = soup.find_all('div', class_=re.compile(r'product|item', re.I))
                print(f"🔄 Fallback: Found {len(product_elements)} potential product containers")
            
            for element in product_elements[:25]:  # Get more than 20 in case some don't have images
                try:
                    product_data = self.extract_product_data(element)
                    if product_data and product_data.get('image_url'):
                        products.append(product_data)
                        print(f"✅ Found product: {product_data['name'][:50]}...")
                        
                        if len(products) >= 20:
                            break
                            
                except Exception as e:
                    print(f"⚠️ Error extracting product: {e}")
                    continue
            
            print(f"📦 Successfully scraped {len(products)} products with images")
            return products
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return []
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return []
    
    def extract_product_data(self, element):
        """Extract product data from a product element"""
        try:
            # Product name - try multiple selectors
            name_selectors = [
                '.product-name', '.product-title', '.name', '.title',
                'h3', 'h4', 'h5', '[data-product-name]'
            ]
            
            name = None
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    name = self.clean_text(name_elem.get_text())
                    break
            
            if not name:
                # Fallback: try any heading or strong text
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b']:
                    elem = element.find(tag)
                    if elem:
                        name = self.clean_text(elem.get_text())
                        break
            
            # Price - try multiple selectors
            price_selectors = [
                '.price', '.product-price', '.amount', '.cost',
                '[data-price]', '.price-current', '.sale-price'
            ]
            
            price = 0.0
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price = self.clean_price(price_elem.get_text())
                    if price > 0:
                        break
            
            # Image URL
            img_element = element.select_one('img')
            image_url = self.get_product_image_url(img_element)
            
            # Description - try to get from various places
            desc_selectors = [
                '.description', '.product-description', '.summary',
                '.product-summary', '.excerpt'
            ]
            
            description = ""
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem:
                    description = self.clean_text(desc_elem.get_text())
                    break
            
            # Generate description from name if none found
            if not description and name:
                description = f"Quality {name.lower()} for your home needs"
            
            # Basic validation
            if not name or not image_url:
                return None
            
            # Set default price if not found
            if price <= 0:
                price = random.uniform(15.0, 150.0)  # Random reasonable price
            
            return {
                'name': name[:150],  # Limit name length
                'description': description[:500] if description else f"Quality home supply item - {name}",
                'price': round(price, 2),
                'image_url': image_url,
                'category': 'Home Supply',
                'stock_quantity': random.randint(5, 50),
                'is_promotional': random.choice([True, False])
            }
            
        except Exception as e:
            print(f"⚠️ Error extracting product data: {e}")
            return None
    
    def save_to_database(self, products):
        """Save scraped products to Django database"""
        print("💾 Saving products to database...")
        
        try:
            with transaction.atomic():
                # Create or get Home Supply category
                category, created = Category.objects.get_or_create(
                    name='Home Supply',
                    defaults={
                        'description': 'Essential home supplies and appliances for everyday living'
                    }
                )
                
                if created:
                    print("✅ Created 'Home Supply' category")
                else:
                    print("✅ Using existing 'Home Supply' category")
                
                saved_count = 0
                for product_data in products:
                    try:
                        # Check if product already exists
                        if SmartProducts.objects.filter(name=product_data['name']).exists():
                            print(f"⚠️ Product already exists: {product_data['name']}")
                            continue
                        
                        # Create SmartProducts entry (more features than regular Product)
                        smart_product = SmartProducts.objects.create(
                            name=product_data['name'],
                            description=product_data['description'],
                            price=product_data['price'],
                            category=product_data['category'],
                            stock_quantity=product_data['stock_quantity'],
                            image_url=product_data['image_url'],
                            is_promotional=product_data['is_promotional'],
                            
                            # Seasonal and temporal features
                            peak_season='all_year',
                            weekend_boost=random.choice([True, False]),
                            festival_association='new_year',  # Home supplies often needed for new year
                            seasonal_priority=random.randint(5, 8),
                            
                            # ML forecasting features
                            avg_weekly_sales=random.randint(5, 25),
                            avg_monthly_sales=random.randint(20, 100),
                            demand_trend=random.choice(['stable', 'increasing']),
                            price_elasticity=round(random.uniform(0.8, 1.2), 3),
                            promotion_lift=round(random.uniform(1.1, 1.5), 2),
                            
                            # Inventory management
                            min_stock_level=5,
                            max_stock_level=100,
                            reorder_point=10,
                            lead_time_days=7
                        )
                        
                        saved_count += 1
                        print(f"✅ Saved: {smart_product.name} - Rs {smart_product.price}")
                        
                    except Exception as e:
                        print(f"❌ Error saving product {product_data['name']}: {e}")
                        continue
                
                print(f"🎉 Successfully saved {saved_count} products to database!")
                return saved_count
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            return 0
    
    def run_scraping(self):
        """Main scraping workflow"""
        print("🚀 Starting Winners.mu Home Supply Scraping")
        print("=" * 50)
        
        # Target URL 
        url = "https://www.winners.mu/articles-menagers#/pageSize=25&viewMode=grid&orderBy=0"
        
        # Alternative URLs if the main one doesn't work
        alternative_urls = [
            "https://www.winners.mu/articles-menagers",
            "https://www.winners.mu/electromenager", 
            "https://www.winners.mu/maison-jardin",
            "https://www.winners.mu/ustensiles-cuisine",
            "https://www.winners.mu/petit-electromenager"
        ]
        
        products = []
        
        # Try main URL first
        products = self.scrape_products_page(url)
        
        # If main URL didn't work, try alternatives
        if len(products) < 10:
            print("🔄 Main URL didn't return enough products, trying alternatives...")
            for alt_url in alternative_urls:
                try:
                    alt_products = self.scrape_products_page(alt_url)
                    products.extend(alt_products)
                    if len(products) >= 20:
                        break
                except Exception as e:
                    print(f"⚠️ Alternative URL failed: {alt_url} - {e}")
                    continue
        
        # Limit to 20 products
        products = products[:20]
        
        if products:
            # Save to database
            saved_count = self.save_to_database(products)
            
            # Save to JSON file as backup
            with open('winners_home_supply_products.json', 'w') as f:
                json.dump(products, f, indent=2)
            
            print(f"\n🎯 SCRAPING SUMMARY:")
            print(f"📦 Products found: {len(products)}")
            print(f"💾 Products saved: {saved_count}")
            print(f"📁 Backup saved to: winners_home_supply_products.json")
            
        else:
            print("❌ No products found. The website structure might have changed.")
            
            # Create sample products as fallback
            print("🔄 Creating sample home supply products...")
            sample_products = self.create_sample_products()
            saved_count = self.save_to_database(sample_products)
            print(f"✅ Created {saved_count} sample products")
        
        print("\n✅ Scraping completed!")
        return len(products)
    
    def create_sample_products(self):
        """Create sample home supply products if scraping fails"""
        sample_products = [
            {
                'name': 'Premium Non-Stick Frying Pan Set',
                'description': 'Professional grade non-stick frying pans, set of 3 sizes',
                'price': 85.00,
                'image_url': 'https://via.placeholder.com/400x400/FF6B6B/FFFFFF?text=Frying+Pan',
                'category': 'Home Supply',
                'stock_quantity': 25,
                'is_promotional': True
            },
            {
                'name': 'Electric Rice Cooker 1.8L',
                'description': 'Automatic rice cooker with keep-warm function, perfect for families',
                'price': 120.00,
                'image_url': 'https://via.placeholder.com/400x400/4ECDC4/FFFFFF?text=Rice+Cooker',
                'category': 'Home Supply',
                'stock_quantity': 15,
                'is_promotional': False
            },
            {
                'name': 'Stainless Steel Cookware Set',
                'description': '7-piece stainless steel cookware set with glass lids',
                'price': 180.00,
                'image_url': 'https://via.placeholder.com/400x400/45B7D1/FFFFFF?text=Cookware+Set',
                'category': 'Home Supply',
                'stock_quantity': 12,
                'is_promotional': True
            },
            {
                'name': 'Digital Kitchen Scale',
                'description': 'Precision digital kitchen scale up to 5kg, LCD display',
                'price': 45.00,
                'image_url': 'https://via.placeholder.com/400x400/96CEB4/FFFFFF?text=Kitchen+Scale',
                'category': 'Home Supply',
                'stock_quantity': 30,
                'is_promotional': False
            },
            {
                'name': 'Multi-Purpose Storage Containers',
                'description': 'Set of 10 airtight food storage containers with lids',
                'price': 65.00,
                'image_url': 'https://via.placeholder.com/400x400/FFEAA7/333333?text=Storage+Set',
                'category': 'Home Supply',
                'stock_quantity': 40,
                'is_promotional': True
            }
        ]
        
        # Generate more sample products
        for i in range(15):
            sample_products.append({
                'name': f'Home Essential Item {i+6}',
                'description': f'Quality home supply product for everyday use - Item {i+6}',
                'price': round(random.uniform(20.0, 200.0), 2),
                'image_url': f'https://via.placeholder.com/400x400/{random.choice(["FF6B6B", "4ECDC4", "45B7D1", "96CEB4", "FFEAA7"])}/FFFFFF?text=Home+Item+{i+6}',
                'category': 'Home Supply',
                'stock_quantity': random.randint(5, 50),
                'is_promotional': random.choice([True, False])
            })
        
        return sample_products

def main():
    """Main function"""
    scraper = WinnersScraper()
    products_found = scraper.run_scraping()
    
    if products_found > 0:
        print(f"\n🎉 Successfully added {products_found} home supply products!")
        print("🌐 Check your shop section - products should now appear under 'Home Supply' category")
    else:
        print("\n⚠️ No products were added. Please check the logs above for details.")

if __name__ == "__main__":
    main()