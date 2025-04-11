from django.core.management.base import BaseCommand
from store.models import Product
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Generate slugs for all products that are missing them'

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        for product in products:
            if not product.slug:
                product.slug = slugify(product.name)
                product.save()
                self.stdout.write(self.style.SUCCESS(f'Slug generated for product: {product.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Slug already exists for product: {product.name}'))
        self.stdout.write(self.style.SUCCESS('Slug generation completed.')) 