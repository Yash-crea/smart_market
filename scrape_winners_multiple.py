#!/usr/bin/env python3
"""
Enhanced Web scraper for Winners.mu multiple food categories
Scrapes entremets (desserts) and tartes (tarts) from Winners.mu
Handles pagination and different product layouts
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

class WinnersMultiScraper:
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
        
        # Category mapping for different URLs
        self.category_mapping = {
            'entremets': {
                'category': 'Desserts & Entremets',
                'description': 'Exquisite French-style desserts and entremets for special occasions',
                'keywords': ['dessert', 'entremet', 'mousse', 'tiramisu', 'cheesecake']
            },
            'tarte': {
                'category': 'Tarts & Pastries', 
                'description': 'Delicious tarts and pastries with premium ingredients',
                'keywords': ['tart', 'tarte', 'pie', 'pastry', 'flan']
            },
            'gateau-assortis': {
                'category': 'Assorted Cakes & Pastries',
                'description': 'Premium assorted cakes and pastries for special celebrations',
                'keywords': ['gateau', 'cake', 'patisserie', 'assorted', 'mixed']
            },
            'biscuits': {
                'category': 'Biscuits & Cookies',
                'description': 'Crispy biscuits and cookies for every occasion',
                'keywords': ['biscuit', 'cookie', 'cracker']
            }
        }
        
    def detect_category_from_url(self, url):
        """Detect product category from URL"""
        url_lower = url.lower()
        for key, info in self.category_mapping.items():
            if key in url_lower:
                return info
        # Default fallback
        return {
            'category': 'Specialty Foods',
            'description': 'Premium specialty food products',
            'keywords': []
        }
        
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
    
    def is_valid_image_url(self, url):
        """Quick check if URL looks like a valid image URL"""
        if not url:
            return False
        
        # Check if it has valid image extension or blob storage pattern
        return (url.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')) or 
                'blob.core.windows.net' in url or
                'cloudinary.com' in url or
                'amazonaws.com' in url)
    
    def get_product_image_url(self, img_element):
        """Extract full image URL from img element with enhanced validation"""
        if not img_element:
            return None
            
        # Try different image source attributes (prioritize data-lazyloadsrc for lazy loading)
        for attr in ['data-lazyloadsrc', 'data-src', 'data-original', 'data-lazy', 'src']:
            if img_element.has_attr(attr):
                img_url = img_element[attr]
                
                # Clean and validate the URL
                if img_url:
                    # Handle blob storage URLs specifically
                    if 'blob.core.windows.net' in img_url:
                        # These are typically complete URLs
                        if img_url.startswith('http'):
                            return img_url
                        else:
                            return 'https:' + img_url if img_url.startswith('//') else img_url
                    
                    # Fix incomplete URLs (like ones ending with just numbers or dots)
                    if img_url.endswith('.') and not self.is_valid_image_url(img_url):
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
    
    def scrape_products_page(self, url):
        """Scrape products from any Winners.mu page"""
        print(f"🔍 Scraping: {url}")
        
        # Detect category from URL
        category_info = self.detect_category_from_url(url)
        print(f"📂 Detected category: {category_info['category']}")
        
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Debug: Save HTML for inspection
            url_safe = url.replace('/', '_').replace(':', '').replace('#', '')
            debug_filename = f'debug_page_{url_safe[-30:]}.html'
            with open(debug_filename, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print(f"💾 Saved page HTML as {debug_filename} for inspection")
            
            # Try multiple selectors for product containers
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
                'li.product',
                '.grid-item',
                '.category-item'
            ]
            
            product_elements = []
            for selector in product_selectors:
                elements = soup.select(selector)
                if elements:
                    product_elements = elements
                    print(f"✅ Found {len(elements)} products using selector: {selector}")
                    break
            
            if not product_elements:
                # Advanced fallbacks for different page layouts
                alt_selectors = [
                    'div[class*="product"]',
                    'div[class*="item"]',
                    'li[class*="product"]', 
                    'article',
                    'div[data-*]',
                    '.box',
                    '.card'
                ]
                
                for selector in alt_selectors:
                    elements = soup.select(selector)
                    if elements and len(elements) > 3:  # Ensure meaningful results
                        product_elements = elements
                        print(f"🔄 Fallback: Found {len(elements)} potential products using: {selector}")
                        break
            
            if not product_elements:
                print("🔍 Deep analysis of page structure...")
                # Look for any elements with images that might be products
                img_elements = soup.find_all('img')
                print(f"Found {len(img_elements)} images on page")
                
                # Find parent containers of images that look like product images
                potential_products = []
                for img in img_elements:
                    if any(keyword in str(img).lower() for keyword in ['product', 'item', 'tart', 'dessert', 'entremet']):
                        parent = img.find_parent()
                        if parent:
                            # Go up a few levels to find the product container
                            for level in range(3):
                                if parent.find_parent():
                                    parent = parent.find_parent()
                                else:
                                    break
                            potential_products.append(parent)
                
                # Remove duplicates
                product_elements = list(set(potential_products))[:20]
                print(f"🔄 Found {len(product_elements)} potential product containers from image analysis")
            
            # Extract product data from elements
            max_products = 20
            for element in product_elements[:30]:  # Process more to ensure we get enough valid ones
                try:
                    product_data = self.extract_product_data(element, category_info)
                    if product_data and product_data.get('image_url'):
                        products.append(product_data)
                        print(f"✅ Found product: {product_data['name'][:50]}...")
                        
                        if len(products) >= max_products:
                            break
                            
                except Exception as e:
                    print(f"⚠️ Error extracting product: {e}")
                    continue
            
            print(f"📦 Successfully scraped {len(products)} products from {category_info['category']}")
            return products
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return []
        except Exception as e:
            print(f"❌ Scraping error: {e}")
            return []
    
    def extract_product_data(self, element, category_info):
        """Extract product data from a product element"""
        try:
            # Product name - try multiple selectors including title attributes
            name_selectors = [
                '.product-name', 
                '.product-title', 
                '.woocommerce-loop-product__title',
                '.name', 
                '.title',
                'h3', 'h4', 'h5', 'h2', 'h1',
                '[data-product-name]',
                'a[title]',
                '.product-link',
                'strong',
                'b'
            ]
            
            name = None
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    # Try getting from text content first
                    text_content = self.clean_text(name_elem.get_text())
                    if text_content and len(text_content) > 2:
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
                        if name and len(name) > 2:
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
                '.regular-price',
                'span[class*="price"]'
            ]
            
            price = 0.0
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text()
                    price = self.clean_price(price_text)
                    if price > 0:
                        break
            
            # Image URL with enhanced debugging
            img_element = element.select_one('img')
            image_url = self.get_product_image_url(img_element)
            
            # Debug image extraction
            if img_element and not image_url:
                print(f"⚠️ Image element found but no valid URL extracted for: {name}")
                print(f"   Available attributes: {list(img_element.attrs.keys())}")
            elif image_url:
                print(f"🖼️ Image URL found: {image_url[:50]}...")
            
            # Basic validation - require both name and image for quality products
            if not name or len(name) < 3:
                return None
            
            if not image_url:
                print(f"⚠️ Skipping {name} - no valid image URL found")
                return None
            
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
            
            # Generate enhanced description based on category
            if not description and name:
                if 'entremet' in category_info['category'].lower():
                    description = f"Elegant {name.lower()} - sophisticated French-style dessert perfect for special occasions"
                elif 'tart' in category_info['category'].lower():
                    description = f"Artisanal {name.lower()} - handcrafted tart with premium ingredients and authentic flavors"
                elif 'assorted' in category_info['category'].lower():
                    description = f"Exquisite {name.lower()} - premium assorted selection perfect for celebrations and special events"
                else:
                    description = f"Premium {name.lower()} - quality food product with authentic taste and exceptional value"
            
            # Set intelligent pricing based on category
            if price <= 0:
                if 'entremet' in category_info['category'].lower():
                    price = random.uniform(85.0, 250.0)  # Premium dessert price range
                elif 'tart' in category_info['category'].lower():
                    price = random.uniform(60.0, 180.0)  # Tart price range
                elif 'assorted' in category_info['category'].lower():
                    price = random.uniform(120.0, 300.0)  # Premium assorted selection price range
                else:
                    price = random.uniform(40.0, 120.0)  # Standard price range
            
            # Detect promotional items
            is_promotional = any(keyword in name.lower() for keyword in ['special', 'offer', 'promo', 'deal', 'sale', 'limited'])
            
            # Enhanced seasonal detection
            peak_season = 'all_year'
            festival_association = 'none'
            
            # Festival and seasonal detection
            name_lower = name.lower()
            if any(keyword in name_lower for keyword in ['christmas', 'xmas', 'festive', 'noel']):
                festival_association = 'christmas'
                peak_season = 'winter'
            elif any(keyword in name_lower for keyword in ['valentine', 'heart', 'love']):
                festival_association = 'valentine'
            elif any(keyword in name_lower for keyword in ['diwali', 'festival', 'celebration']):
                festival_association = 'diwali'
            elif any(keyword in name_lower for keyword in ['easter', 'spring']):
                festival_association = 'easter'
                peak_season = 'spring'
            elif any(keyword in name_lower for keyword in ['summer', 'tropical', 'mango', 'coconut']):
                peak_season = 'summer'
            
            return {
                'name': name[:150],
                'description': description[:500] if description else f"Premium {category_info['category'].lower()} - {name}",
                'price': round(price, 2),
                'image_url': image_url,
                'category': category_info['category'],
                'stock_quantity': random.randint(5, 60),
                'is_promotional': is_promotional,
                'peak_season': peak_season,
                'festival_association': festival_association,
                'weekend_boost': random.choice([True, False]),
                'weekend_sales_multiplier': random.uniform(1.0, 1.5),
                'avg_weekly_sales': random.uniform(8, 35),
                'demand_trend': random.choice(['stable', 'increasing', 'seasonal']),
                'price_elasticity': random.uniform(0.7, 1.3)
            }
            
        except Exception as e:
            print(f"⚠️ Error extracting product data: {e}")
            return None
    
    def save_to_database(self, all_products):
        """Save all scraped products to Django database"""
        print("💾 Saving all products to database...")
        
        try:
            with transaction.atomic():
                # Create categories as needed
                categories_created = []
                
                # Get unique categories from products
                unique_categories = set(product['category'] for product in all_products)
                
                category_descriptions = {
                    'Biscuits & Cookies': 'Delicious biscuits, cookies, and sweet treats for every occasion',
                    'Desserts & Entremets': 'Exquisite French-style desserts and entremets for special occasions',
                    'Tarts & Pastries': 'Delicious tarts and pastries with premium ingredients',
                    'Assorted Cakes & Pastries': 'Premium assorted cakes and pastries for special celebrations',
                    'Confectionery': 'Premium chocolates, candies and confectionery items',
                    'Specialty Foods': 'Premium specialty food products for discerning customers'
                }
                
                for category_name in unique_categories:
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
                skipped_count = 0
                
                for product_data in all_products:
                    try:
                        # Check if product already exists (by name similarity)
                        existing_product = SmartProducts.objects.filter(
                            name__icontains=product_data['name'][:25]
                        ).first()
                        
                        if existing_product:
                            print(f"⚠️ Similar product already exists: {product_data['name'][:40]}...")
                            skipped_count += 1
                            continue
                        
                        # Create SmartProducts entry
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
                            
                            # Category-appropriate defaults
                            min_stock_level=3,
                            max_stock_level=150,
                            reorder_point=8,
                            lead_time_days=2,  # Fresh food items need short lead times
                            seasonal_priority=8 if product_data['festival_association'] != 'none' else 6
                        )
                        
                        saved_count += 1
                        print(f"✅ Saved: {smart_product.name[:50]}...")
                        
                    except Exception as e:
                        print(f"❌ Error saving product {product_data['name'][:30]}...: {e}")
                        continue
                
                print(f"🎉 Successfully saved {saved_count} out of {len(all_products)} products!")
                print(f"⚠️ Skipped {skipped_count} duplicate products")
                if categories_created:
                    print(f"📂 New categories created: {', '.join(categories_created)}")
                return saved_count
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            return 0

def main():
    """Main execution function"""
    print("🛒 Winners.mu Multi-Category Food Scraper")
    print("=" * 60)
    
    # Target URLs
    urls_to_scrape = [
        "https://www.winners.mu/entremets#/pageSize=25&viewMode=grid&orderBy=0",
        "https://www.winners.mu/tarte",
        "https://www.winners.mu/gateau-assortis"
    ]
    
    # Initialize scraper
    scraper = WinnersMultiScraper()
    
    all_products = []
    
    # Scrape each URL
    for url in urls_to_scrape:
        print(f"\n{'='*60}")
        products = scraper.scrape_products_page(url)
        
        if products:
            all_products.extend(products)
            print(f"✅ Scraped {len(products)} products from this page")
        else:
            print(f"❌ No products found from: {url}")
        
        # Small delay between requests
        time.sleep(2)
    
    if all_products:
        # Save all products to database
        print(f"\n{'='*60}")
        saved_count = scraper.save_to_database(all_products)
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"🎯 Final Summary:")
        print(f"   • Total URLs scraped: {len(urls_to_scrape)}")
        print(f"   • Total products found: {len(all_products)}")
        print(f"   • Successfully saved: {saved_count}")
        print(f"   • Overall success rate: {(saved_count/len(all_products)*100):.1f}%")
        
        # Display products by category
        print(f"\n🛒 Products by Category:")
        categories = {}
        for product in all_products:
            category = product['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(product)
        
        for category, prods in categories.items():
            print(f"\n   📂 {category} ({len(prods)} products):")
            for i, product in enumerate(prods[:3]):
                print(f"     {i+1}. {product['name'][:40]}... - Rs {product['price']}")
            if len(prods) > 3:
                print(f"     ... and {len(prods)-3} more")
                
    else:
        print("❌ No products found from any URL.")
        print("💡 Check the generated debug HTML files to analyze page structures.")

if __name__ == "__main__":
    main()