import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from marche_smart.models import SmartProducts, Category
from decimal import Decimal, InvalidOperation
import re
import time


class Command(BaseCommand):
    help = 'Scrape cooking oils, dairy products, and home supply items from Winners website'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=25,
            help='Limit number of products to scrape per URL (default: 25)'
        )
        parser.add_argument(
            '--url',
            type=str,
            choices=['oils', 'dairy', 'dairy-extended', 'home-supply', 'all'],
            default='all',
            help='Which category to scrape: oils, dairy, dairy-extended (all dairy categories), home-supply, or all'
        )
               
    def handle(self, *args, **options):
        self.stdout.write("Starting Winners product scraping...")
        
        limit = options['limit']
        url_choice = options['url']
        
        # Define URLs to scrape
        urls = []
        if url_choice in ['oils', 'all']:
            urls.append(("https://www.winners.mu/huiles-alimentaires", "oils"))
        if url_choice in ['dairy', 'all']:
            urls.append(("https://www.winners.mu/lait-poudre-uht-concentres", "dairy"))
        if url_choice in ['home-supply', 'all']:
            urls.append(("https://www.winners.mu/articles-menagers#/pageSize=25&viewMode=grid&orderBy=0", "home-supply"))
        if url_choice in ['dairy-extended']:
            # Extended dairy categories - all dairy related sections
            dairy_urls = [
                ("https://www.winners.mu/lait-poudre-uht-concentres", "dairy"),
                ("https://www.winners.mu/beurre", "dairy"),
                ("https://www.winners.mu/fromages-libre-service-2", "dairy"), 
                ("https://www.winners.mu/margarine", "dairy"),
                ("https://www.winners.mu/oeufs", "dairy"),
                ("https://www.winners.mu/cremes-fraiches", "dairy"),
                ("https://www.winners.mu/fromages-frais", "dairy"),
                ("https://www.winners.mu/lait-frais", "dairy"),
                ("https://www.winners.mu/yaourts", "dairy")
            ]
            urls.extend(dairy_urls)

        total_products = []
        for url, category_type in urls:
            self.stdout.write(f"Scraping {category_type} products from: {url}")
            products = self.scrape_winners_products(url, limit, category_type)
            total_products.extend(products)
            
            # Small delay between requests to be respectful
            if len(urls) > 1:
                time.sleep(2)
            # Small delay between requests to be respectful
            if len(urls) > 1:
                time.sleep(2)
        
        if total_products:
            self.stdout.write(f"Found {len(total_products)} total products. Saving to database...")
            
            saved_count = 0
            for product in total_products:
                if self.save_product(product):
                    saved_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully saved {saved_count} products to database!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('No products found. Check the website structure.')
            )

    def categorize_product(self, product_name, category_type):
        """Categorize product based on name and source URL"""
        name_lower = product_name.lower()
        
        if category_type == "dairy":
            # Enhanced dairy categorization
            if any(keyword in name_lower for keyword in ['butter', 'beurre', 'margarine']):
                if 'margarine' in name_lower:
                    return 'BUTTER'  # Using existing category for consistency 
                else:
                    return 'BUTTER'
            elif any(keyword in name_lower for keyword in ['cheese', 'fromage', 'cheddar', 'mozzarella', 'gouda', 'emmental']):
                return 'Fresh Milk & Dairy'
            elif any(keyword in name_lower for keyword in ['egg', 'oeuf', 'oeufs']):
                return 'Fresh Milk & Dairy' 
            elif any(keyword in name_lower for keyword in ['yogurt', 'yaourt', 'yoghurt']):
                return 'Fresh Milk & Dairy'
            elif any(keyword in name_lower for keyword in ['milk powder', 'lait poudre', 'powdered milk', 'powder']):
                return 'Milk Powder'
            elif any(keyword in name_lower for keyword in ['uht', 'long life', 'longue conservation']):
                return 'UHT Milk'
            elif any(keyword in name_lower for keyword in ['concentrate', 'concentre', 'condensed', 'condense']):
                return 'Condensed & Concentrated Milk'
            elif any(keyword in name_lower for keyword in ['cream', 'creme', 'crème']):
                return 'Dairy Cream'
            elif any(keyword in name_lower for keyword in ['fresh milk', 'lait frais', 'milk', 'lait']):
                return 'Fresh Milk & Dairy'
            else:
                return 'Dairy Products'
                
        elif category_type == "oils":
            # Cooking oil products (existing logic)
            if any(keyword in name_lower for keyword in ['olive', 'oliva', 'lolivier']):
                return 'Olive Oils'
            elif any(keyword in name_lower for keyword in ['avocado', 'macadamia', 'sesame', 'coconut', 'mustard', 'walnut', 'almond']):
                return 'Specialty Oils'
            elif any(keyword in name_lower for keyword in ['ghee', 'vanaspati', 'clarified']):
                return 'Vanaspati & Ghee'
            else:
                return 'Cooking Oils & Ghee'
        
        elif category_type == "home-supply":
            # Home supply categorization
            if any(keyword in name_lower for keyword in ['cleaner', 'detergent', 'soap', 'shampoo', 'nettoyant']):
                return 'Cleaning & Laundry'
            elif any(keyword in name_lower for keyword in ['toilet', 'tissue', 'paper', 'papier', 'hygiene']):
                return 'Paper & Hygiene Products'
            elif any(keyword in name_lower for keyword in ['kitchen', 'cuisine', 'utensil', 'ustensile', 'cookware']):
                return 'Kitchen & Dining'
            elif any(keyword in name_lower for keyword in ['storage', 'container', 'box', 'bag', 'rangement']):
                return 'Storage & Organization'
            elif any(keyword in name_lower for keyword in ['towel', 'serviette', 'cloth', 'linge']):
                return 'Textiles & Linens'
            elif any(keyword in name_lower for keyword in ['battery', 'batterie', 'light', 'lumiere', 'electrical']):
                return 'Electrical & Batteries'
            else:
                return 'Home & Garden'
        
        # Default fallback
        return 'General Products'

    def scrape_winners_products(self, url, limit, category_type):
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
            
            # Method 1: Try structured product extraction
            products = self.extract_structured_products(soup, limit, category_type)
            
            # Method 2: If no structured products found, try text extraction
            if len(products) == 0:
                self.stdout.write("No structured products found, trying text extraction...")
                products = self.extract_text_products(soup, limit, category_type)
            
            self.stdout.write(f"Extraction complete. Found {len(products)} products.")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error scraping {url}: {str(e)}')
            )
        
        return products[:limit]

    def extract_structured_products(self, soup, limit, category_type):
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
                    product = self.extract_product_from_element(element, category_type)
                    if product:
                        products.append(product)
                        if len(products) >= limit:
                            break
                break
        
        return products

    def extract_product_from_element(self, element, category_type):
        """Extract product info from HTML element"""
        try:
            # Try to find product name
            name_selectors = ['a[href]', 'h1', 'h2', 'h3', '.title', '.name', '.product-name', '.item-title']
            name = ''
            
            # Define product keywords based on category type
            if category_type == "dairy":
                keywords = ['milk', 'lait', 'cream', 'creme', 'powder', 'poudre', 'uht', 'concentrate', 'concentre', 'butter', 'beurre', 'cheese', 'fromage', 'egg', 'oeuf', 'yogurt', 'yaourt', 'margarine']
            elif category_type == "home-supply":
                keywords = ['cleaner', 'detergent', 'soap', 'shampoo', 'nettoyant', 'toilet', 'tissue', 'paper', 'papier', 'hygiene', 'kitchen', 'cuisine', 'utensil', 'ustensile', 'cookware', 'storage', 'container', 'box', 'bag', 'rangement', 'towel', 'serviette', 'cloth', 'linge', 'battery', 'batterie', 'light', 'lumiere', 'electrical']
            else:  # oils
                keywords = ['oil', 'huile', 'olive', 'coconut', 'sunflower', 'vegetable', 'corn', 'soya', 'sesame', 'mustard', 'canola', 'ghee', 'vanaspati']
            
            for sel in name_selectors:
                name_elem = element.select_one(sel)
                if name_elem and name_elem.get_text(strip=True):
                    candidate_name = name_elem.get_text(strip=True)
                    # Check if this looks like the right product type
                    if any(keyword.lower() in candidate_name.lower() for keyword in keywords):
                        name = candidate_name
                        break
            
            # If no specific name found, try general selectors
            if not name:
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
            
            # Try to find image with multiple strategies
            image_url = ''
            
            # Strategy 1: Regular img src
            img = element.select_one('img[src]')
            if img and img.get('src'):
                candidate_url = img.get('src', '')
                if self.is_valid_image_url(candidate_url):
                    image_url = candidate_url
            
            # Strategy 2: Lazy loading images (include data-lazyloadsrc from Winners)
            if not image_url:
                img_lazy = element.select_one('img[data-lazyloadsrc], img[data-src], img[data-original], img[data-lazy]')
                if img_lazy:
                    candidate_url = (img_lazy.get('data-lazyloadsrc') or 
                                   img_lazy.get('data-src') or 
                                   img_lazy.get('data-original') or 
                                   img_lazy.get('data-lazy') or '')
                    if self.is_valid_image_url(candidate_url):
                        image_url = candidate_url
            
            # Strategy 3: Background images in style attributes
            if not image_url:
                style_elem = element.select_one('[style*="background-image"]')
                if style_elem:
                    style = style_elem.get('style', '')
                    bg_match = re.search(r'background-image:\s*url\([\'"]?([^\'")]+)[\'"]?\)', style)
                    if bg_match:
                        image_url = bg_match.group(1)
            
            # Normalize URL
            if image_url:
                if image_url.startswith('/'):
                    image_url = 'https://www.winners.mu' + image_url
                elif image_url.startswith('//'):
                    image_url = 'https:' + image_url
            
            # Only use fallback if no real image found
            if not image_url:
                if category_type == "home-supply":
                    image_url = self.get_fallback_home_supply_image(name)
                elif category_type == "oils":
                    image_url = self.get_fallback_oils_image(name)
                elif category_type == "dairy":
                    image_url = self.get_fallback_dairy_image(name)
            
            # Validate and return product
            if name and price and len(name) > 3:
                # Get appropriate category for this product
                category_name = self.categorize_product(name, category_type)
                
                return {
                    'name': name.upper()[:150],
                    'price': price,
                    'image_url': image_url,
                    'category': category_name,
                    'category_type': category_type
                }
                
        except Exception as e:
            self.stdout.write(f"Error extracting product: {e}")
        
        return None

    def extract_text_products(self, soup, limit, category_type):
        """Extract products from page text using patterns"""
        products = []
        
        # Get all text from the page
        page_text = soup.get_text()
        
        # Define pattern based on category type
        if category_type == "dairy":
            # Pattern to match dairy product names followed by prices
            pattern = r'([A-Z][A-Z\s&-]*(?:MILK|LAIT|CREAM|CREME|POWDER|POUDRE|UHT|CONCENTRATE|CONCENTRE|BUTTER|BEURRE|CHEESE|FROMAGE|EGG|OEUF|YOGURT|YAOURT|MARGARINE)[A-Z\s\d-]*?)\s+Rs\s*([\d,\.]+)'
            keywords = ['MILK', 'LAIT', 'CREAM', 'CREME', 'POWDER', 'POUDRE', 'UHT', 'CONCENTRATE', 'CONCENTRE', 'BUTTER', 'BEURRE', 'CHEESE', 'FROMAGE', 'EGG', 'OEUF', 'YOGURT', 'YAOURT', 'MARGARINE']
        elif category_type == "home-supply":
            # Pattern to match home supply product names followed by prices
            pattern = r'([A-Z][A-Z\s&-]*(?:CLEANER|DETERGENT|SOAP|SHAMPOO|NETTOYANT|TOILET|TISSUE|PAPER|PAPIER|HYGIENE|KITCHEN|CUISINE|UTENSIL|USTENSILE|COOKWARE|STORAGE|CONTAINER|BOX|BAG|RANGEMENT|TOWEL|SERVIETTE|CLOTH|LINGE|BATTERY|BATTERIE|LIGHT|LUMIERE|ELECTRICAL)[A-Z\s\d-]*?)\s+Rs\s*([\d,\.]+)'
            keywords = ['CLEANER', 'DETERGENT', 'SOAP', 'SHAMPOO', 'NETTOYANT', 'TOILET', 'TISSUE', 'PAPER', 'PAPIER', 'HYGIENE', 'KITCHEN', 'CUISINE', 'UTENSIL', 'USTENSILE', 'COOKWARE', 'STORAGE', 'CONTAINER', 'BOX', 'BAG', 'RANGEMENT', 'TOWEL', 'SERVIETTE', 'CLOTH', 'LINGE', 'BATTERY', 'BATTERIE', 'LIGHT', 'LUMIERE', 'ELECTRICAL']
        else:  # oils
            # Pattern to match cooking oil product names followed by prices
            pattern = r'([A-Z][A-Z\s&-]*(?:OIL|HUILE|OLIVE|COCONUT|SUNFLOWER|VEGETABLE|CORN|SOYA|SESAME|MUSTARD|CANOLA|GHEE|VANASPATI)[A-Z\s\d-]*?)\s+Rs\s*([\d,\.]+)'
            keywords = ['OIL', 'HUILE', 'OLIVE', 'COCONUT', 'SUNFLOWER', 'VEGETABLE', 'CORN', 'SOYA', 'SESAME', 'MUSTARD', 'CANOLA', 'GHEE', 'VANASPATI']
        
        matches = re.findall(pattern, page_text)
        self.stdout.write(f"Found {len(matches)} {category_type} pattern matches")
        
        for match in matches:
            name, price_value = match
            name = name.strip()
            
            # Validate name length and content
            if 5 < len(name) < 100 and any(keyword in name.upper() for keyword in keywords):
                # Get appropriate category for this product
                category_name = self.categorize_product(name, category_type)
                
                # Generate fallback image for all categories
                image_url = ''
                if category_type == "home-supply":
                    image_url = self.get_fallback_home_supply_image(name)
                elif category_type == "oils":
                    image_url = self.get_fallback_oils_image(name)
                elif category_type == "dairy":
                    image_url = self.get_fallback_dairy_image(name)
                
                products.append({
                    'name': name[:150],
                    'price': f"Rs {price_value}",
                    'image_url': image_url,
                    'category': category_name,
                    'category_type': category_type
                })
                
                if len(products) >= limit:
                    break
        
        return products

    def is_valid_image_url(self, url):
        """Check if image URL is valid (not placeholder/empty)"""
        if not url or len(url) < 10:
            return False
        # Check for common placeholder patterns
        invalid_patterns = [
            'data:image/gif;base64',
            'placeholder', 
            '1x1',
            'transparent.gif',
            'blank.gif',
            'spacer.gif'
        ]
        # Accept real image URLs (especially from ewinners blob storage)
        if 'ewinners' in url.lower() or url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            return True
        # Accept real image URLs (especially from ewinners blob storage)
        if 'ewinners' in url.lower() or url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            return True
        return not any(pattern in url.lower() for pattern in invalid_patterns)

    def get_fallback_oils_image(self, product_name):
        """Generate appropriate image URL for cooking oils"""
        name_lower = product_name.lower()
        
        if any(keyword in name_lower for keyword in ['olive', 'oliva']):
            return "https://via.placeholder.com/300x300/F0FDF4/16A34A?text=OLIVE+OIL"
        elif any(keyword in name_lower for keyword in ['coconut', 'coco']):
            return "https://via.placeholder.com/300x300/FFFBEB/D97706?text=COCONUT+OIL"
        elif any(keyword in name_lower for keyword in ['sunflower']):
            return "https://via.placeholder.com/300x300/FEF3C7/CA8A04?text=SUNFLOWER+OIL"
        elif any(keyword in name_lower for keyword in ['sesame']):
            return "https://via.placeholder.com/300x300/FDF2F8/BE185D?text=SESAME+OIL"
        elif any(keyword in name_lower for keyword in ['ghee', 'vanaspati']):
            return "https://via.placeholder.com/300x300/FEF7CD/A3A000?text=GHEE"
        else:
            return "https://via.placeholder.com/300x300/FEF2E2/EA580C?text=COOKING+OIL"

    def get_fallback_dairy_image(self, product_name):
        """Generate appropriate image URL for dairy products"""
        name_lower = product_name.lower()
        
        if any(keyword in name_lower for keyword in ['milk', 'lait']):
            return "https://via.placeholder.com/300x300/FEFCE8/CA8A04?text=MILK"
        elif any(keyword in name_lower for keyword in ['butter', 'beurre']):
            return "https://via.placeholder.com/300x300/FEF3C7/D97706?text=BUTTER"
        elif any(keyword in name_lower for keyword in ['cheese', 'fromage']):
            return "https://via.placeholder.com/300x300/FEF7CD/CA8A04?text=CHEESE"
        elif any(keyword in name_lower for keyword in ['yogurt', 'yaourt']):
            return "https://via.placeholder.com/300x300/F0F9FF/2563EB?text=YOGURT"
        elif any(keyword in name_lower for keyword in ['cream', 'creme']):
            return "https://via.placeholder.com/300x300/FAF5FF/9333EA?text=CREAM"
        elif any(keyword in name_lower for keyword in ['powder', 'poudre']):
            return "https://via.placeholder.com/300x300/F8FAFC/475569?text=POWDER"
        elif any(keyword in name_lower for keyword in ['egg', 'oeuf']):
            return "https://via.placeholder.com/300x300/FEF2E2/EA580C?text=EGGS"
        else:
            return "https://via.placeholder.com/300x300/ECFDF5/10B981?text=DAIRY"
    
    def get_fallback_home_supply_image(self, product_name):
        """Generate appropriate image URL for home supply products"""
        name_lower = product_name.lower()
        
        # Use reliable image sources with simple URLs
        # Check LUMINARC brand first for branded images
        if any(keyword in name_lower for keyword in ['luminarc', 'keep', 'pure']):
            # LUMINARC branded products - use branded placeholder
            return "https://via.placeholder.com/300x300/E8F4FD/2C5282?text=LUMINARC+GLASS"
        elif any(keyword in name_lower for keyword in ['jar', 'container', 'box', 'storage']):
            # Storage containers and jars
            return "https://via.placeholder.com/300x300/F0F9FF/1E40AF?text=STORAGE"
        elif any(keyword in name_lower for keyword in ['kitchen', 'utensil', 'cookware']):
            # Kitchen items
            return "https://via.placeholder.com/300x300/FEF3C7/D97706?text=KITCHEN"
        elif any(keyword in name_lower for keyword in ['cleaner', 'detergent', 'soap']):
            # Cleaning products
            return "https://via.placeholder.com/300x300/ECFDF5/059669?text=CLEANING"
        elif any(keyword in name_lower for keyword in ['towel', 'cloth', 'fabric']):
            # Textiles
            return "https://via.placeholder.com/300x300/FDF2F8/BE185D?text=TEXTILES"
        elif any(keyword in name_lower for keyword in ['light', 'battery', 'electrical']):
            # Electronics
            return "https://via.placeholder.com/300x300/FFFBEB/F59E0B?text=ELECTRICAL"
        else:
            # Generic home supply
            return "https://via.placeholder.com/300x300/F3F4F6/6B7280?text=HOME+SUPPLY"

    def save_product(self, product_data):
        """Save product to database"""
        try:
            # Extract numeric price
            price = self.extract_price(product_data['price'])
            
            # Get or create category
            category_name = product_data['category']
            category_type = product_data.get('category_type', 'general')
            
            # Create category description based on type
            if category_type == 'dairy':
                category_description = f'{category_name} - Fresh and processed dairy products from Winners.mu'
            elif category_type == 'oils':
                category_description = f'{category_name} - Cooking oils and related products from Winners.mu'
            elif category_type == 'home-supply':
                category_description = f'{category_name} - Home and household supply items from Winners.mu'
            else:
                category_description = f'{category_name} products from Winners.mu'
            
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={'description': category_description}
            )
            
            # Prepare data for database
            data = {
                'name': product_data['name'],
                'description': f'{category_name} product scraped from Winners.mu',
                'price': price,
                'category': category_name,  # Keep as string for SmartProducts model
                'stock_quantity': 10,  # Default stock
                'is_promotional': False,
                'image_url': product_data.get('image_url') or None,
            }
            
            # Check if product exists
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
 