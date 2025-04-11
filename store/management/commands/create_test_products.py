from django.core.management.base import BaseCommand
from store.models import Category, Product
from django.utils.text import slugify
import os
import random
from django.conf import settings
from django.core.files.images import ImageFile

class Command(BaseCommand):
    help = 'Create test products and categories'

    def handle(self, *args, **kwargs):
        # Create categories if they don't exist
        categories = [
            {'name': 'Retiqo Spices', 'description': 'High-quality spices for your kitchen'},
            {'name': 'Premium Fruits', 'description': 'Fresh and premium quality fruits'},
            {'name': 'Prestige Cookware', 'description': 'High-quality cookware for your kitchen'},
            {'name': 'Home Decor', 'description': 'Beautiful items to decorate your home'},
        ]
        
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {category.name}'))
        
        # Get all categories
        all_categories = Category.objects.all()
        
        # Create products with exact slugs from templates
        products = [
            # Spices
            {'name': 'Turmeric Powder', 'slug': 'turmeric-powder', 'category': 'Retiqo Spices', 'price': 280, 'stock': 50, 'image': 'spice1.jpeg', 'old_price': 350},
            {'name': 'Cinnamon Sticks', 'slug': 'cinnamon-sticks', 'category': 'Retiqo Spices', 'price': 150, 'stock': 40, 'image': 'spice2.jpg', 'old_price': 180},
            {'name': 'Garam Masala', 'slug': 'garam-masala', 'category': 'Retiqo Spices', 'price': 220, 'stock': 30, 'image': 'spice3.jpg', 'old_price': 250},
            {'name': 'Premium Turmeric Powder', 'slug': 'premium-turmeric-powder', 'category': 'Retiqo Spices', 'price': 280, 'stock': 45, 'image': 'spice1.jpeg', 'old_price': 560},
            
            # Fruits
            {'name': 'Dragon Fruit', 'slug': 'dragon-fruit', 'category': 'Premium Fruits', 'price': 280, 'stock': 20, 'image': 'fruits1.jpeg', 'old_price': 350},
            {'name': 'Organic Apples', 'slug': 'organic-apples', 'category': 'Premium Fruits', 'price': 220, 'stock': 25, 'image': 'fruits.jpg', 'old_price': 250},
            {'name': 'Kiwi Fruit', 'slug': 'kiwi-fruit', 'category': 'Premium Fruits', 'price': 180, 'stock': 15, 'image': 'fruits1.jpeg', 'old_price': 200},
            {'name': 'Mixed Dried Fruits', 'slug': 'mixed-dried-fruits', 'category': 'Premium Fruits', 'price': 340, 'stock': 10, 'image': 'fruits2.jpg', 'old_price': 400},
            {'name': 'Premium Mangoes', 'slug': 'premium-mangoes', 'category': 'Premium Fruits', 'price': 450, 'stock': 10, 'image': 'fruits2.jpg', 'old_price': 500},
            
            # Cookware
            {'name': 'Premium Cookware Set', 'slug': 'premium-cookware-set', 'category': 'Prestige Cookware', 'price': 3500, 'stock': 10, 'image': 'cookware.jpg', 'old_price': 4000},
            {'name': 'Non-stick Frying Pan', 'slug': 'non-stick-frying-pan', 'category': 'Prestige Cookware', 'price': 1200, 'stock': 5, 'image': 'cookware1.jpg', 'old_price': 1500},
            {'name': 'Stainless Steel Pot', 'slug': 'stainless-steel-pot', 'category': 'Prestige Cookware', 'price': 1800, 'stock': 8, 'image': 'cookware2.jpg', 'old_price': 2000},
            {'name': 'Kitchen Utensil Set', 'slug': 'kitchen-utensil-set', 'category': 'Prestige Cookware', 'price': 900, 'stock': 12, 'image': 'cookware.jpg', 'old_price': 1000},
            {'name': 'Baking Tray Set', 'slug': 'baking-tray-set', 'category': 'Prestige Cookware', 'price': 1700, 'stock': 12, 'image': 'cookware2.jpg', 'old_price': 2000},
            
            # Home Decor
            {'name': 'Decorative Cushion Set', 'slug': 'decorative-cushion-set', 'category': 'Home Decor', 'price': 1200, 'stock': 15, 'image': 'decor.jpg', 'old_price': 1500},
            {'name': 'Modern Abstract Canvas Art', 'slug': 'modern-abstract-canvas-art', 'category': 'Home Decor', 'price': 2500, 'stock': 20, 'image': 'decor.jpg', 'old_price': 3000},
            {'name': 'Pendant Ceiling Light', 'slug': 'pendant-ceiling-light', 'category': 'Home Decor', 'price': 1800, 'stock': 25, 'image': 'decor.jpg', 'old_price': 2200},
            {'name': 'Framed Wall Art Set', 'slug': 'framed-wall-art-set', 'category': 'Home Decor', 'price': 3200, 'stock': 18, 'image': 'decor.jpg', 'old_price': 3800},
            {'name': 'Scented Candle Set', 'slug': 'scented-candle-set', 'category': 'Home Decor', 'price': 850, 'stock': 18, 'image': 'decor.jpg', 'old_price': 1000},
            {'name': 'Decorative Table Clock', 'slug': 'decorative-table-clock', 'category': 'Home Decor', 'price': 750, 'stock': 18, 'image': 'decor.jpg', 'old_price': 900},
            {'name': 'Ceramic Flower Vase', 'slug': 'ceramic-flower-vase', 'category': 'Home Decor', 'price': 650, 'stock': 18, 'image': 'decor.jpg', 'old_price': 800},
            {'name': 'Table Lamp', 'slug': 'table-lamp', 'category': 'Home Decor', 'price': 950, 'stock': 18, 'image': 'decor.jpg', 'old_price': 1200},
        ]
        
        # Make sure the static/img directory exists
        static_img_dir = os.path.join(settings.BASE_DIR, 'static', 'img')
        
        for product_data in products:
            # Get category
            try:
                category = Category.objects.get(name=product_data['category'])
                
                # Check if product already exists by slug
                if not Product.objects.filter(slug=product_data['slug']).exists():
                    # Create product without image first
                    product = Product(
                        category=category,
                        name=product_data['name'],
                        slug=product_data['slug'],
                        description=f"This is a description for {product_data['name']}. It is a high-quality product in the {category.name} category.",
                        price=product_data['price'],
                        stock=product_data['stock'],
                        is_active=True,
                        is_featured=random.choice([True, False]),
                        is_new=random.choice([True, False]),
                    )
                    
                    # Set old price
                    if 'old_price' in product_data:
                        product.discount_price = product_data['price']
                        product.price = product_data['old_price']
                    
                    # Save the product to get an ID
                    product.save()
                    
                    # Now handle the image
                    try:
                        # Try to find the image in the static/img directory
                        img_path = os.path.join(static_img_dir, product_data['image'])
                        if os.path.exists(img_path):
                            # Open the image file
                            with open(img_path, 'rb') as img_file:
                                # Save the image to the product
                                product.image.save(
                                    product_data['image'],
                                    ImageFile(img_file),
                                    save=True
                                )
                            self.stdout.write(self.style.SUCCESS(f'Added image to product: {product.name}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'Image not found: {img_path}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error adding image to product: {str(e)}'))
                    
                    self.stdout.write(self.style.SUCCESS(f'Created product: {product.name} with slug: {product.slug}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Product with slug {product_data["slug"]} already exists'))
            except Category.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Category not found: {product_data["category"]}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully created test products and categories')) 