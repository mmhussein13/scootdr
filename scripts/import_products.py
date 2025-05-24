#!/usr/bin/env python
"""
Script to import sample products, categories, and brands into the database
This helps populate the database with initial data for testing and demos
"""
import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scooterrentals.settings')
os.environ.setdefault('DJANGO_SECRET_KEY', 'temp-key-for-scripts-only')
django.setup()

from landing.models import Product, Category, Brand
from landing.views import get_sample_products

def create_categories_and_brands():
    """Create categories and brands from sample products"""
    sample_products = get_sample_products()
    
    # Extract unique categories and brands
    categories = set(product['category'] for product in sample_products)
    brands = set(product['brand'] for product in sample_products)
    
    # Create categories
    category_map = {}
    for cat_name in categories:
        category, created = Category.objects.get_or_create(
            name=cat_name,
            defaults={
                'description': f'{cat_name} scooters',
                'is_active': True
            }
        )
        category_map[cat_name] = category
        if created:
            print(f"Created category: {cat_name}")
        else:
            print(f"Category already exists: {cat_name}")
    
    # Create brands
    brand_map = {}
    for brand_name in brands:
        brand, created = Brand.objects.get_or_create(
            name=brand_name,
            defaults={
                'description': f'{brand_name} scooters',
                'is_active': True
            }
        )
        brand_map[brand_name] = brand
        if created:
            print(f"Created brand: {brand_name}")
        else:
            print(f"Brand already exists: {brand_name}")
    
    return category_map, brand_map

def import_products():
    """Import sample products into the database"""
    # Create categories and brands first
    category_map, brand_map = create_categories_and_brands()
    
    # Get sample products
    sample_products = get_sample_products()
    
    # Import products
    for product_data in sample_products:
        # Check if product already exists by name
        if Product.objects.filter(name=product_data['name']).exists():
            print(f"Product already exists: {product_data['name']}")
            continue
        
        # Create new product
        product = Product(
            name=product_data['name'],
            description=product_data['description'],
            price=product_data['price'],
            image_url=product_data['image'],
            category=category_map[product_data['category']],
            brand=brand_map[product_data['brand']],
            stock=20 if product_data.get('in_stock', True) else 0,
            is_featured=True if product_data['id'] <= 3 else False,
            is_active=True
        )
        product.save()
        print(f"Created product: {product.name}")

if __name__ == '__main__':
    print("Starting product import...")
    import_products()
    print("Product import complete!")