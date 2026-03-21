"""
Django management command to scrape Winners.mu home supply products
Usage: python manage.py scrape_home_supply
"""

from django.core.management.base import BaseCommand
from django.db import transaction
import requests
from bs4 import BeautifulSoup
import json
import random
import re
from urllib.parse import urljoin
from marche_smart.models import Category, SmartProducts


class Command(BaseCommand):
    help = 'Scrape home supply products from Winners.mu and add to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of products to scrape (default: 20)',
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(
            self.style.SUCCESS(f'Starting to scrape {count} home supply products from Winners.mu...')
        )
        
        scraper = WinnersScraper(self.stdout, self.style)
        products_added = scraper.run_scraping(count)
        
        if products_added > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully added {products_added} home supply products!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('No products were added. Creating sample products instead...')
            )
            sample_count = scraper.create_and_save_sample_products()
            self.stdout.write(
                self.style.SUCCESS(f'Created {sample_count} sample home supply products!')
            )


class WinnersScraper:
    def __init__(self, stdout, style):
        self.stdout = stdout
        self.style = style
        self.base_url = "https://www.winners.mu"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        })
    
    def clean_price(self, price_text):
        """Extract numeric price from text"""
        if not price_text:
            return 0.0
        price_clean = re.sub(r'[^\d.,]', '', str(price_text))
        price_clean = price_clean.replace(',', '')
        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return random.uniform(25.0, 200.0)
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        return ' '.join(text.strip().split())
    
    def scrape_products_page(self, url, count):
        """Scrape products from Winners.mu"""
        self.stdout.write(f"🔍 Attempting to scrape: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple product selectors
            product_selectors = [
                '.product-item', '.product-card', '.item-box',
                '.product', 'article.product', '[data-product]'
            ]
            
            products = []
            for selector in product_selectors:
                elements = soup.select(selector)
                if elements:
                    self.stdout.write(f"Found {len(elements)} products with selector: {selector}")
                    
                    for element in elements[:count + 10]:  # Get extra in case some fail
                        product_data = self.extract_product_data(element)
                        if product_data and len(products) < count:
                            products.append(product_data)
                    
                    if products:
                        break
            
            return products
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Error scraping {url}: {e}"))
            return []
    
    def extract_product_data(self, element):
        """Extract product data from HTML element"""
        try:
            # Extract name
            name_selectors = ['.product-name', '.product-title', 'h3', 'h4', 'h5']
            name = None
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    name = self.clean_text(name_elem.get_text())
                    break
            
            if not name:
                return None
            
            # Extract price
            price_selectors = ['.price', '.product-price', '.amount']
            price = 0.0
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price = self.clean_price(price_elem.get_text())
                    break
            
            if price <= 0:
                price = random.uniform(30.0, 250.0)
            
            # Extract image URL
            img_element = element.select_one('img')
            image_url = None
            if img_element:
                for attr in ['src', 'data-src', 'data-original']:
                    if img_element.has_attr(attr):
                        img_url = img_element[attr]
                        if img_url:
                            if img_url.startswith('http'):
                                image_url = img_url
                            else:
                                image_url = urljoin(self.base_url, img_url)
                            break
            
            # Generate placeholder image if none found
            if not image_url:
                product_hash = abs(hash(name)) % 6
                colors = ["FF6B6B", "4ECDC4", "45B7D1", "96CEB4", "FFEAA7", "DDA0DD"]
                image_url = f"https://via.placeholder.com/400x300/{colors[product_hash]}/FFFFFF?text={name.replace(' ', '+')[:20]}"
            
            # Extract description
            desc_elem = element.select_one('.description, .product-description')
            description = self.clean_text(desc_elem.get_text()) if desc_elem else f"Quality {name.lower()} for your home"
            
            return {
                'name': name[:150],
                'description': description[:300],
                'price': round(price, 2),
                'image_url': image_url,
                'stock_quantity': random.randint(10, 50)
            }
            
        except Exception as e:
            return None
    
    def save_to_database(self, products):
        """Save products to database"""
        try:
            with transaction.atomic():
                # Create Home Supply category
                category, created = Category.objects.get_or_create(
                    name='Home Supply',
                    defaults={'description': 'Essential home supplies and household items'}
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS("✅ Created 'Home Supply' category"))
                
                saved_count = 0
                for product_data in products:
                    try:
                        # Check if product already exists
                        if SmartProducts.objects.filter(name=product_data['name']).exists():
                            continue
                        
                        # Create SmartProducts entry
                        smart_product = SmartProducts.objects.create(
                            name=product_data['name'],
                            description=product_data['description'],
                            price=product_data['price'],
                            category='Home Supply',
                            stock_quantity=product_data['stock_quantity'],
                            image_url=product_data['image_url'],
                            is_promotional=random.choice([True, False]),
                            
                            # Smart product features
                            peak_season='all_year',
                            festival_association='new_year',
                            weekend_boost=random.choice([True, False]),
                            avg_weekly_sales=random.randint(3, 15),
                            avg_monthly_sales=random.randint(12, 60),
                            demand_trend='stable',
                            price_elasticity=round(random.uniform(0.8, 1.2), 3),
                            promotion_lift=round(random.uniform(1.1, 1.4), 2),
                            min_stock_level=5,
                            reorder_point=10,
                            lead_time_days=7
                        )
                        
                        saved_count += 1
                        self.stdout.write(f"✅ Saved: {smart_product.name} - Rs {smart_product.price}")
                        
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Error saving product: {e}"))
                        continue
                
                return saved_count
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Database error: {e}"))
            return 0
    
    def create_sample_home_supply_products(self):
        """Create high-quality sample home supply products"""
        return [
            {
                'name': 'Premium Non-Stick Cookware Set',
                'description': 'Professional 7-piece non-stick cookware set with glass lids and heat-resistant handles',
                'price': 185.00,
                'image_url': 'https://via.placeholder.com/400x300/FF6B6B/FFFFFF?text=Cookware+Set',
                'stock_quantity': 15
            },
            {
                'name': 'Digital Multi-Cooker 6L',
                'description': 'Versatile pressure cooker with 12 cooking programs including rice, steam, and slow cook',
                'price': 220.00,
                'image_url': 'https://via.placeholder.com/400x300/4ECDC4/FFFFFF?text=Multi-Cooker',
                'stock_quantity': 12
            },
            {
                'name': 'Stainless Steel Kitchen Knife Set',
                'description': 'Professional 8-piece knife set with wooden block and sharpening steel',
                'price': 95.00,
                'image_url': 'https://via.placeholder.com/400x300/45B7D1/FFFFFF?text=Knife+Set',
                'stock_quantity': 20
            },
            {
                'name': 'Electric Food Processor 1000W',
                'description': 'Powerful food processor with multiple attachments for chopping, slicing, and mixing',
                'price': 165.00,
                'image_url': 'https://via.placeholder.com/400x300/96CEB4/FFFFFF?text=Food+Processor',
                'stock_quantity': 8
            },
            {
                'name': 'Ceramic Dinnerware Set 16-Piece',
                'description': 'Elegant ceramic dinner set for 4 people, dishwasher and microwave safe',
                'price': 120.00,
                'image_url': 'https://via.placeholder.com/400x300/FFEAA7/333333?text=Dinnerware+Set',
                'stock_quantity': 25
            },
            {
                'name': 'Smart Coffee Maker with Timer',
                'description': 'Programmable coffee maker with thermal carafe and auto-brew timer',
                'price': 145.00,
                'image_url': 'https://via.placeholder.com/400x300/DDA0DD/FFFFFF?text=Coffee+Maker',
                'stock_quantity': 18
            },
            {
                'name': 'Glass Storage Container Set',
                'description': 'Set of 12 airtight glass containers with leak-proof lids for food storage',
                'price': 75.00,
                'image_url': 'https://via.placeholder.com/400x300/FFB6C1/333333?text=Storage+Set',
                'stock_quantity': 35
            },
            {
                'name': 'Bamboo Cutting Board Collection',
                'description': 'Eco-friendly bamboo cutting boards in 3 sizes with antimicrobial properties',
                'price': 55.00,
                'image_url': 'https://via.placeholder.com/400x300/90EE90/333333?text=Cutting+Boards',
                'stock_quantity': 30
            },
            {
                'name': 'Electric Hand Mixer 300W',
                'description': 'Lightweight hand mixer with 5 speeds and stainless steel beaters',
                'price': 65.00,
                'image_url': 'https://via.placeholder.com/400x300/F0E68C/333333?text=Hand+Mixer',
                'stock_quantity': 22
            },
            {
                'name': 'Silicone Baking Mat Set',
                'description': 'Non-stick silicone baking mats, set of 3 different sizes with measuring guides',
                'price': 35.00,
                'image_url': 'https://via.placeholder.com/400x300/FF7F50/FFFFFF?text=Baking+Mats',
                'stock_quantity': 40
            },
            {
                'name': 'Stainless Steel Spice Rack',
                'description': 'Magnetic spice rack with 12 jars, perfect for kitchen organization',
                'price': 45.00,
                'image_url': 'https://via.placeholder.com/400x300/20B2AA/FFFFFF?text=Spice+Rack',
                'stock_quantity': 28
            },
            {
                'name': 'Non-Slip Kitchen Floor Mats',
                'description': 'Set of 2 anti-fatigue kitchen mats with non-slip backing',
                'price': 40.00,
                'image_url': 'https://via.placeholder.com/400x300/9370DB/FFFFFF?text=Kitchen+Mats',
                'stock_quantity': 15
            },
            {
                'name': 'Digital Kitchen Timer 3-Channel',
                'description': 'Multi-timer with 3 independent channels and magnetic backing',
                'price': 25.00,
                'image_url': 'https://via.placeholder.com/400x300/32CD32/FFFFFF?text=Kitchen+Timer',
                'stock_quantity': 45
            },
            {
                'name': 'Copper Moscow Mule Mugs Set',
                'description': 'Set of 4 authentic copper mugs with brass handles for cocktails',
                'price': 85.00,
                'image_url': 'https://via.placeholder.com/400x300/CD853F/FFFFFF?text=Copper+Mugs',
                'stock_quantity': 12
            },
            {
                'name': 'Kitchen Utensil Holder Set',
                'description': 'Stainless steel utensil holder with 6 essential cooking tools',
                'price': 50.00,
                'image_url': 'https://via.placeholder.com/400x300/B0C4DE/333333?text=Utensil+Set',
                'stock_quantity': 20
            },
            {
                'name': 'Microwave-Safe Plate Covers Set',
                'description': 'BPA-free microwave covers in 3 sizes with steam vents',
                'price': 30.00,
                'image_url': 'https://via.placeholder.com/400x300/F5DEB3/333333?text=Plate+Covers',
                'stock_quantity': 35
            },
            {
                'name': 'Adjustable Kitchen Drawer Dividers',
                'description': 'Expandable drawer organizers, set of 8 for kitchen organization',
                'price': 32.00,
                'image_url': 'https://via.placeholder.com/400x300/D2B48C/333333?text=Drawer+Dividers',
                'stock_quantity': 25
            },
            {
                'name': 'Foldable Kitchen Step Stool',
                'description': 'Heavy-duty folding step stool with non-slip surface, supports up to 150kg',
                'price': 70.00,
                'image_url': 'https://via.placeholder.com/400x300/A0522D/FFFFFF?text=Step+Stool',
                'stock_quantity': 18
            },
            {
                'name': 'LED Under-Cabinet Lighting Kit',
                'description': 'Wireless LED strip lights with remote control for kitchen cabinets',
                'price': 60.00,
                'image_url': 'https://via.placeholder.com/400x300/6495ED/FFFFFF?text=LED+Lights',
                'stock_quantity': 22
            },
            {
                'name': 'Premium Dish Drying Rack',
                'description': 'Two-tier stainless steel dish rack with drainboard and utensil holder',
                'price': 80.00,
                'image_url': 'https://via.placeholder.com/400x300/708090/FFFFFF?text=Dish+Rack',
                'stock_quantity': 16
            }
        ]
    
    def create_and_save_sample_products(self):
        """Create and save sample products when scraping fails"""
        sample_products = self.create_sample_home_supply_products()
        return self.save_to_database(sample_products)
    
    def run_scraping(self, count=20):
        """Main scraping workflow"""
        # URLs to try
        urls = [
            "https://www.winners.mu/articles-menagers#/pageSize=25&viewMode=grid&orderBy=0",
            "https://www.winners.mu/articles-menagers",
            "https://www.winners.mu/electromenager",
            "https://www.winners.mu/maison-jardin"
        ]
        
        all_products = []
        for url in urls:
            products = self.scrape_products_page(url, count - len(all_products))
            all_products.extend(products)
            
            if len(all_products) >= count:
                break
        
        # If scraping didn't get enough products, add samples
        if len(all_products) < 5:  # If we got very few products
            self.stdout.write(self.style.WARNING("Scraping yielded few products, using sample products"))
            sample_products = self.create_sample_home_supply_products()[:count]
            saved_count = self.save_to_database(sample_products)
        else:
            # Use scraped products
            all_products = all_products[:count]
            saved_count = self.save_to_database(all_products)
        
        return saved_count