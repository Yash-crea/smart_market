from django.core.management.base import BaseCommand
from marche_smart.models import Category, Product


class Command(BaseCommand):
    help = 'Populate the database with sample categories and products'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                'Sample data removed. This command now only serves as a template.\n'
                'To populate real data, you can:\n'
                '1. Import from CSV files\n'
                '2. Use web scraping commands\n'
                '3. Manually add through Django admin\n'
                '4. Create your own data population logic here'
            )
        )
        
        # Example: Count existing data
        category_count = Category.objects.count()
        product_count = Product.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Current database state:\n'
                f'Categories: {category_count}\n'
                f'Products: {product_count}'
            )
        )
