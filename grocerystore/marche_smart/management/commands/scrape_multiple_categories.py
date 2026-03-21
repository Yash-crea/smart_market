import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from marche_smart.models import SmartProducts, Category
from decimal import Decimal, InvalidOperation
import re
import time


class Command(BaseCommand):
    help = 'Scrape multiple product categories from Winners website'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Limit number of products to scrape per category (default: 50)'
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting Winners multi-category product scraping...")
        
        limit_per_category = options['limit']
        
        # Different product categories to scrape (only valid URLs)
        categories = {
            'BUTTER': 'https://www.winners.mu/beurre',
        }
        
        total_saved = 0
        
        for category_name, url in categories.items():
            self.stdout.write(f"\n--- Scraping {category_name} products ---")
            products = self.scrape_winners_products(url, limit_per_category, category_name)
            
            if products:
                self.stdout.write(f"Found {len(products)} {category_name} products. Saving to database...")
                
                saved_count = 0
                for product in products:
                    if self.save_product(product):
                        saved_count += 1
                
                total_saved += saved_count
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully saved {saved_count} {category_name} products!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'No {category_name} products found.')
                )
            
            # Add delay between categories to be respectful to the server
            time.sleep(2)
        
        self.stdout.write(
            self.style.SUCCESS(f'\n=== SCRAPING COMPLETE ===\nTotal products saved: {total_saved}')
        )

    def scrape_winners_products(self, url, limit, category):
        """Scrape products from Winners website"""
        products = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            self.stdout.write(f"Fetching: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            self.stdout.write("Page loaded successfully")
            
            # Try structured product extraction first
            products = self.extract_structured_products(soup, limit, category)
            
            # If no structured products found, try text extraction
            if len(products) == 0:
                self.stdout.write("No structured products found, trying text extraction...")
                products = self.extract_text_products(soup, limit, category)
            
            self.stdout.write(f"Extraction complete. Found {len(products)} products.")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error scraping {url}: {str(e)}')
            )
        
        return products[:limit]

    def extract_structured_products(self, soup, limit, category):
        """Try to extract products from structured HTML"""
        products = []
        
        # Try common product container selectors
        selectors = [
            'div.product-item-info',
            '.product-item',
            '.product',
            'article',
            '.item-box',
            '.product-grid-item'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                self.stdout.write(f"Found {len(elements)} elements with selector: {selector}")
                
                for element in elements:
                    product = self.extract_product_from_element(element, category)
                    if product:
                        products.append(product)
                        if len(products) >= limit:
                            break
                break
        
        return products

    def extract_product_from_element(self, element, category):
        """Extract product info from HTML element"""
        try:
            # Try to find product name
            name_selectors = ['a[href]', 'h1', 'h2', 'h3', '.title', '.name']
            name = ''
            
            for sel in name_selectors:
                name_elem = element.select_one(sel)
                if name_elem and name_elem.get_text(strip=True):
                    name = name_elem.get_text(strip=True)
                    break
            
            # Try to find price
            price = ''
            price_selectors = ['.price', '.cost', '.amount']
            
            for sel in price_selectors:
                price_elem = element.select_one(sel)
                if price_elem and 'Rs' in price_elem.get_text():
                    price = price_elem.get_text(strip=True)
                    break
            
            # If no price in selectors, search all text
            if not price:
                all_text = element.get_text()
                price_match = re.search(r'Rs\s*([\d,\.]+)', all_text)
                if price_match:
                    price = f"Rs {price_match.group(1)}"
            
            # Try to find image
            image_url = ''
            img = element.select_one('img[src]')
            if img:
                image_url = img.get('src', '')
                if image_url.startswith('/'):
                    image_url = 'https://www.winners.mu' + image_url
            
            # Validate and return product
            if name and price and len(name) > 3:
                return {
                    'name': name.upper()[:150],
                    'price': price,
                    'image_url': image_url,
                    'category': category
                }
                
        except Exception as e:
            self.stdout.write(f"Error extracting product: {e}")
        
        return None

    def extract_text_products(self, soup, limit, category):
        """Extract products from page text using patterns"""
        products = []
        
        # Get all text from the page
        page_text = soup.get_text()
        
        # Different patterns for different categories
        patterns = {
            'BUTTER': r'([A-Z][A-Z\s&-]*(?:BUTTER|BEURRE)[A-Z\s\d-]*?)\s+Rs\s*([\d,\.]+)',
            'MILK': r'([A-Z][A-Z\s&-]*(?:MILK|LAIT|LATTE)[A-Z\s\d%-]*?)\s+Rs\s*([\d,\.]+)',
            'CHEESE': r'([A-Z][A-Z\s&-]*(?:CHEESE|FROMAGE)[A-Z\s\d%-]*?)\s+Rs\s*([\d,\.]+)',
            'YOGURT': r'([A-Z][A-Z\s&-]*(?:YOGURT|YAOURT|YOGHURT)[A-Z\s\d%-]*?)\s+Rs\s*([\d,\.]+)',
        }
        
        pattern = patterns.get(category, patterns['BUTTER'])
        matches = re.findall(pattern, page_text)
        
        self.stdout.write(f"Found {len(matches)} text pattern matches")
        
        for match in matches:
            name, price_value = match
            name = name.strip()
            
            # Validate name length and content
            if 3 < len(name) < 100:
                products.append({
                    'name': name[:150],
                    'price': f"Rs {price_value}",
                    'image_url': '',
                    'category': category
                })
                
                if len(products) >= limit:
                    break
        
        return products

    def save_product(self, product_data):
        """Save product to database"""
        try:
            # Extract numeric price
            price = self.extract_price(product_data['price'])
            
            # Prepare data for database
            data = {
                'name': product_data['name'],
                'description': f'Scraped from Winners.mu - {product_data["category"]} category',
                'price': price,
                'category': product_data['category'],
                'stock_quantity': 10,  # Default stock
                'is_promotional': False,
                'image_url': product_data.get('image_url') or None,
            }
            
            # Check if product with same name already exists
            existing = SmartProducts.objects.filter(name=data['name']).first()
            
            if existing:
                # Update existing product
                for key, value in data.items():
                    setattr(existing, key, value)
                existing.save()
                self.stdout.write(f"Updated: {data['name']}")
            else:
                # Create new product
                product = SmartProducts(**data)
                product.save()
                self.stdout.write(f"Created: {data['name']}")
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error saving {product_data.get('name', 'Unknown')}: {e}")
            )
            return False

    def extract_price(self, price_str):
        """Extract numeric price from price string"""
        if not price_str:
            return Decimal('0.00')
        
        # Remove everything except digits and decimal points
        price_clean = re.sub(r'[^\d.]', '', str(price_str))
        
        try:
            return Decimal(price_clean) if price_clean else Decimal('0.00')
        except (InvalidOperation, ValueError):
            return Decimal('0.00')