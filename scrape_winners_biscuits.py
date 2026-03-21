#!/usr/bin/env python3
"""
Enhanced Web scraper for Winners.mu food products (biscuits, desserts, etc.)
Extracts product data with improved image handling and categorization
Supports lazy-loaded images and incomplete URLs
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
project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grocerystore')
sys.path.append(project_dir)
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

class WinnersBiscuitsScraper:
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
            
        # Try different image source attributes (prioritize data-lazyloadsrc for lazy loading)
        for attr in ['data-lazyloadsrc', 'data-src', 'data-original', 'data-lazy', 'src']:
            if img_element.has_attr(attr):
                img_url = img_element[attr]
                
                # Clean and validate the URL
                if img_url:
                    # Fix incomplete URLs (like ones ending with just numbers or dots)
                    if img_url.endswith('.') and not img_url.endswith('.jpg') and not img_url.endswith('.png'):
                        # Try common image extensions
                        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                            test_url = img_url + ext
                            if self.is_valid_image_url(test_url):
                                img_url = test_url
                                break
                    
                    # Handle full URLs
                    if img_url.startswith('http'):
                        return img_url
                    # Handle relative URLs
                    elif img_url.startswith('/'):
                        return urljoin(self.base_url, img_url)
                    # Handle other relative paths
                    elif img_url:
                        return urljoin(self.base_url, '/' + img_url)
        return None
    
    def is_valid_image_url(self, url):
        """Quick check if URL looks like a valid image URL"""
        if not url:
            return False
        
        # Check if it has valid image extension or blob storage pattern
        return (url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')) or 
                'blob.core.windows.net' in url or
                'cloudinary.com' in url or
                'amazonaws.com' in url)
    
    def scrape_biscuits_page(self, url):
        """Scrape biscuits from the specific page"""
        print(f"🍪 Scraping biscuits from: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Debug: Save HTML for inspection
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print("💾 Saved page HTML as debug_page.html for inspection")
            
            # Try multiple selectors for product containers specific to biscuits
            product_selectors = [
                '.product-item',
                '.product-card', 
                '.item-box',
                '.product-container',
                '.woocommerce-loop-product__link',
                '.product',
                'article.product',
                '[data-product-id]',
                '.product-inner',
                '.product-wrapper',
                'li.product'
            ]
            
            product_elements = []
            for selector in product_selectors:
                elements = soup.select(selector)
                if elements:
                    product_elements = elements
                    print(f"✅ Found {len(elements)} products using selector: {selector}")
                    break
            
            if not product_elements:
                # Fallback: try to find any divs or list items that might contain products
                alt_selectors = [
                    'div[class*="product"]',
                    'div[class*="item"]',
                    'li[class*="product"]',
                    'article',
                    '.grid-item',
                    '.category-item'
                ]
                
                for selector in alt_selectors:
                    elements = soup.select(selector)
                    if elements:
                        product_elements = elements
                        print(f"🔄 Fallback: Found {len(elements)} potential products using: {selector}")
                        break
            
            if not product_elements:
                print("🔍 Analyzing page structure...")
                # Look for any elements with images that might be products
                img_elements = soup.find_all('img')
                print(f"Found {len(img_elements)} images on page")
                
                # Find parent containers of images that look like product images
                potential_products = []
                for img in img_elements:
                    parent = img.find_parent()
                    if parent and any(keyword in str(parent).lower() for keyword in ['product', 'item', 'biscuit', 'cookie']):
                        potential_products.append(parent)
                
                product_elements = potential_products[:20]  # Limit to avoid too many
                print(f"🔄 Found {len(product_elements)} potential product containers from image analysis")
            
            # Extract product data from elements
            for element in product_elements:
                try:
                    product_data = self.extract_biscuit_data(element)
                    if product_data and product_data.get('image_url'):
                        products.append(product_data)
                        print(f"✅ Found biscuit: {product_data['name'][:50]}...")
                        
                        if len(products) >= 15:  # Limit for biscuits page
                            break
                            
                except Exception as e:
                    print(f"⚠️ Error extracting product: {e}")
                    continue
            
            print(f"🍪 Successfully scraped {len(products)} biscuit products")
            return products
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return []
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return []
    
    def extract_biscuit_data(self, element):
        """Extract biscuit product data from a product element"""
        try:
            # Product name - try multiple selectors including title attributes
            name_selectors = [
                '.product-name', 
                '.product-title', 
                '.woocommerce-loop-product__title',
                '.name', 
                '.title',
                'h3', 'h4', 'h5', 'h2',
                '[data-product-name]',
                'a[title]',
                '.product-link'
            ]
            
            name = None
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    # Try getting from text content first
                    text_content = self.clean_text(name_elem.get_text())
                    if text_content:
                        name = text_content
                        break
                    # Try getting from title attribute
                    if name_elem.get('title'):
                        title_text = name_elem.get('title')
                        # Extract product name from title like "Show details for FLAN CARAMEL"
                        if 'show details for' in title_text.lower():
                            name = title_text.lower().replace('show details for', '').strip().upper()
                        else:
                            name = self.clean_text(title_text)
                        if name:
                            break
            
            # Additional fallback: look for links with title attributes in the element
            if not name:
                link_with_title = element.select_one('a[title]')
                if link_with_title and link_with_title.get('title'):
                    title_text = link_with_title.get('title')
                    if 'show details for' in title_text.lower():
                        name = title_text.lower().replace('show details for', '').strip().upper()
                    else:
                        name = self.clean_text(title_text)
            
            if not name:
                # Fallback: try any heading or strong text
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b', 'span']:
                    elem = element.find(tag)
                    if elem:
                        text = self.clean_text(elem.get_text())
                        if text and len(text) > 3:  # Ensure meaningful text
                            name = text
                            break
            
            # Price - try multiple selectors
            price_selectors = [
                '.price', 
                '.product-price', 
                '.woocommerce-Price-amount',
                '.amount', 
                '.cost',
                '[data-price]', 
                '.price-current', 
                '.sale-price',
                '.regular-price'
            ]
            
            price = 0.0
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text()
                    price = self.clean_price(price_text)
                    if price > 0:
                        break
            
            # Image URL
            img_element = element.select_one('img')
            image_url = self.get_product_image_url(img_element)
            
            # Description - try to get from various places
            desc_selectors = [
                '.description', 
                '.product-description', 
                '.summary',
                '.product-summary', 
                '.excerpt',
                '.short-description'
            ]
            
            description = ""
            for selector in desc_selectors:
                desc_elem = element.select_one(selector)
                if desc_elem:
                    description = self.clean_text(desc_elem.get_text())
                    break
            
            # Detect product category based on name
            category = 'Biscuits & Cookies'
            if name and any(keyword in name.lower() for keyword in ['flan', 'pudding', 'dessert', 'cake']):
                category = 'Desserts & Sweets'
            elif name and any(keyword in name.lower() for keyword in ['chocolate', 'candy', 'sweet']):
                category = 'Confectionery'
            
            # Generate description from name if none found
            if not description and name:
                if 'flan' in name.lower():
                    description = f"Creamy and delicious {name.lower()} - perfect dessert for any occasion"
                elif 'chocolate' in name.lower():
                    description = f"Rich {name.lower()} with authentic chocolate flavor"
                else:
                    description = f"Premium quality {name.lower()} - authentic taste and great value"
            
            # Basic validation
            if not name or len(name) < 3:
                return None
            
            # Set default price if not found (adjust based on product type)
            if price <= 0:
                if 'flan' in name.lower() or 'dessert' in name.lower():
                    price = random.uniform(35.0, 85.0)  # Dessert price range
                elif 'chocolate' in name.lower() and 'cookie' not in name.lower():
                    price = random.uniform(40.0, 120.0)  # Chocolate/candy price range
                else:
                    price = random.uniform(25.0, 120.0)  # Standard biscuit price range
            
            # Detect if it's promotional (common keywords)
            is_promotional = any(keyword in name.lower() for keyword in ['special', 'offer', 'promo', 'deal', 'sale'])
            
            # Seasonal detection
            peak_season = 'all_year'
            festival_association = 'none'
            
            # Festival items
            if any(keyword in name.lower() for keyword in ['christmas', 'xmas', 'festive']):
                festival_association = 'christmas'
                peak_season = 'winter'
            elif any(keyword in name.lower() for keyword in ['valentine', 'heart']):
                festival_association = 'valentine'
            elif any(keyword in name.lower() for keyword in ['diwali', 'festival']):
                festival_association = 'diwali'
            
            return {
                'name': name[:150],  # Limit name length
                'description': description[:500] if description else f"Premium quality {name} - authentic taste and great value",
                'price': round(price, 2),
                'image_url': image_url,
                'category': category,
                'stock_quantity': random.randint(10, 80),
                'is_promotional': is_promotional,
                'peak_season': peak_season,
                'festival_association': festival_association,
                'weekend_boost': random.choice([True, False]),
                'weekend_sales_multiplier': random.uniform(1.1, 1.4),
                'avg_weekly_sales': random.uniform(15, 45),
                'demand_trend': random.choice(['stable', 'increasing', 'seasonal']),
                'price_elasticity': random.uniform(0.8, 1.2)
            }
            
        except Exception as e:
            print(f"⚠️ Error extracting biscuit data: {e}")
            return None
    
    def save_to_database(self, products):
        """Save scraped products to Django database"""
        print("💾 Saving products to database...")
        
        try:
            with transaction.atomic():
                # Create categories as needed
                categories_created = []
                
                # Get unique categories from products
                unique_categories = set(product['category'] for product in products)
                
                for category_name in unique_categories:
                    category_descriptions = {
                        'Biscuits & Cookies': 'Delicious biscuits, cookies, and sweet treats for every occasion',
                        'Desserts & Sweets': 'Creamy desserts and sweet treats for special moments',
                        'Confectionery': 'Premium chocolates, candies and confectionery items'
                    }
                    
                    category, created = Category.objects.get_or_create(
                        name=category_name,
                        defaults={
                            'description': category_descriptions.get(category_name, f'Quality {category_name.lower()} products')
                        }
                    )
                    
                    if created:
                        categories_created.append(category_name)
                        print(f"✅ Created '{category_name}' category")
                    else:
                        print(f"✅ Using existing '{category_name}' category")
                
                saved_count = 0
                for product_data in products:
                    try:
                        # Check if product already exists (by name similarity)
                        existing_product = SmartProducts.objects.filter(
                            name__icontains=product_data['name'][:20]
                        ).first()
                        
                        if existing_product:
                            print(f"⚠️ Similar product already exists: {product_data['name']}")
                            continue
                        
                        # Create SmartProducts entry with enhanced ML features
                        smart_product = SmartProducts.objects.create(
                            name=product_data['name'],
                            description=product_data['description'],
                            price=product_data['price'],
                            category=product_data['category'],
                            stock_quantity=product_data['stock_quantity'],
                            is_promotional=product_data['is_promotional'],
                            image_url=product_data['image_url'],
                            
                            # Enhanced ML and seasonal fields
                            peak_season=product_data['peak_season'],
                            festival_association=product_data['festival_association'],
                            weekend_boost=product_data['weekend_boost'],
                            weekend_sales_multiplier=product_data['weekend_sales_multiplier'],
                            avg_weekly_sales=product_data['avg_weekly_sales'],
                            demand_trend=product_data['demand_trend'],
                            price_elasticity=product_data['price_elasticity'],
                            
                            # Set appropriate defaults
                            min_stock_level=5,
                            max_stock_level=200,
                            reorder_point=15,
                            lead_time_days=3,  # Short lead times for food items
                            seasonal_priority=7 if product_data['festival_association'] != 'none' else 5
                        )
                        
                        saved_count += 1
                        print(f"✅ Saved: {smart_product.name}")
                        
                    except Exception as e:
                        print(f"❌ Error saving product {product_data['name']}: {e}")
                        continue
                
                print(f"🎉 Successfully saved {saved_count} out of {len(products)} products to database!")
                if categories_created:
                    print(f"📂 New categories created: {', '.join(categories_created)}")
                return saved_count
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            return 0

def main():
    """Main execution function"""
    print("🍪 Winners.mu Food Products Scraper")
    print("=" * 50)
    
    # Target URL
    biscuits_url = "https://www.winners.mu/biscuits"
    
    # Initialize scraper
    scraper = WinnersBiscuitsScraper()
    
    # Scrape products
    products = scraper.scrape_biscuits_page(biscuits_url)
    
    if products:
        # Save to database
        saved_count = scraper.save_to_database(products)
        
        # Summary
        print("\n" + "=" * 50)
        print(f"🎯 Scraping Summary:")
        print(f"   • Scraped: {len(products)} food products")
        print(f"   • Saved: {saved_count} to database")
        print(f"   • Success Rate: {(saved_count/len(products)*100):.1f}%")
        
        # Display sample products with categories
        print(f"\n🛒 Sample Products:")
        categories = {}
        for product in products:
            category = product['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(product)
        
        for category, prods in categories.items():
            print(f"\n   📂 {category}:")
            for i, product in enumerate(prods[:3]):
                print(f"     {i+1}. {product['name'][:35]}... - Rs {product['price']}")
            
    else:
        print("❌ No products found. Check the URL or page structure.")
        print("💡 Try checking the generated debug_page.html file to analyze the page structure.")

if __name__ == "__main__":
    main()