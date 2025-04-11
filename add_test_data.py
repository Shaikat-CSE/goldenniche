import os
import django
import random
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goldennichebd.settings')
django.setup()

from store.models import Category, Product

def create_test_data():
    # Create categories
    categories = [
        {
            'name': 'Spices',
            'description': 'High-quality spices from around the world.'
        },
        {
            'name': 'Fruits',
            'description': 'Fresh and premium fruits.'
        },
        {
            'name': 'Cookware',
            'description': 'Premium cookware for your kitchen.'
        },
        {
            'name': 'Home Decor',
            'description': 'Beautiful items to decorate your home.'
        }
    ]
    
    created_categories = []
    for category_data in categories:
        category, created = Category.objects.get_or_create(
            name=category_data['name'],
            defaults={
                'description': category_data['description'],
                'is_active': True
            }
        )
        created_categories.append(category)
        print(f"Category {'created' if created else 'already exists'}: {category.name}")
    
    # Create products
    products = [
        # Spices
        {
            'category': 'Spices',
            'name': 'Premium Cinnamon',
            'description': 'High-quality cinnamon sticks from Sri Lanka.',
            'price': Decimal('199.99'),
            'discount_price': Decimal('179.99'),
            'stock': 50,
            'is_featured': True,
            'is_new': True,
            'is_sale': True
        },
        {
            'category': 'Spices',
            'name': 'Organic Turmeric Powder',
            'description': 'Pure organic turmeric powder with high curcumin content.',
            'price': Decimal('149.99'),
            'discount_price': None,
            'stock': 100,
            'is_featured': True,
            'is_new': False,
            'is_sale': False
        },
        # Fruits
        {
            'category': 'Fruits',
            'name': 'Premium Mangoes',
            'description': 'Sweet and juicy mangoes from the best orchards.',
            'price': Decimal('299.99'),
            'discount_price': Decimal('249.99'),
            'stock': 30,
            'is_featured': True,
            'is_new': True,
            'is_sale': True
        },
        {
            'category': 'Fruits',
            'name': 'Organic Apples',
            'description': 'Fresh and crisp organic apples.',
            'price': Decimal('199.99'),
            'discount_price': None,
            'stock': 80,
            'is_featured': False,
            'is_new': True,
            'is_sale': False
        },
        # Cookware
        {
            'category': 'Cookware',
            'name': 'Non-stick Frying Pan',
            'description': 'High-quality non-stick frying pan for everyday cooking.',
            'price': Decimal('1299.99'),
            'discount_price': Decimal('999.99'),
            'stock': 20,
            'is_featured': True,
            'is_new': False,
            'is_sale': True
        },
        {
            'category': 'Cookware',
            'name': 'Stainless Steel Pot Set',
            'description': 'Premium stainless steel pot set for all your cooking needs.',
            'price': Decimal('2499.99'),
            'discount_price': None,
            'stock': 15,
            'is_featured': True,
            'is_new': True,
            'is_sale': False
        },
        # Home Decor
        {
            'category': 'Home Decor',
            'name': 'Handcrafted Vase',
            'description': 'Beautiful handcrafted vase to enhance your home decor.',
            'price': Decimal('799.99'),
            'discount_price': Decimal('699.99'),
            'stock': 25,
            'is_featured': True,
            'is_new': True,
            'is_sale': True
        },
        {
            'category': 'Home Decor',
            'name': 'Decorative Wall Art',
            'description': 'Elegant wall art to add style to your home.',
            'price': Decimal('1499.99'),
            'discount_price': None,
            'stock': 10,
            'is_featured': False,
            'is_new': True,
            'is_sale': False
        }
    ]
    
    for product_data in products:
        category = Category.objects.get(name=product_data['category'])
        product, created = Product.objects.get_or_create(
            name=product_data['name'],
            defaults={
                'category': category,
                'description': product_data['description'],
                'price': product_data['price'],
                'discount_price': product_data['discount_price'],
                'stock': product_data['stock'],
                'is_active': True,
                'is_featured': product_data['is_featured'],
                'is_new': product_data['is_new'],
                'is_sale': product_data['is_sale']
            }
        )
        print(f"Product {'created' if created else 'already exists'}: {product.name}")

if __name__ == '__main__':
    print("Creating test data...")
    create_test_data()
    print("Test data creation completed!") 