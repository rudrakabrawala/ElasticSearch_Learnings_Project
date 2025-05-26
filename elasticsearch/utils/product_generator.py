"""Utility functions for generating product data."""

from faker import Faker
import random
from datetime import datetime

def generate_product_data(num_products=100):
    """Generate sample product data for testing.
    
    Args:
        num_products (int): Number of products to generate
        
    Returns:
        list: List of generated product documents
    """
    fake = Faker()
    
    # Define product categories and their subcategories
    categories = {
        "Electronics": ["Smartphones", "Laptops", "Headphones", "Tablets", "Accessories"],
        "Clothing": ["Shirts", "Pants", "Shoes", "Accessories", "Outerwear"],
        "Books": ["Fiction", "Non-Fiction", "Textbooks", "Comics", "Biographies"],
        "Home & Garden": ["Furniture", "Tools", "Decor", "Kitchen", "Garden"],
        "Sports & Outdoors": ["Equipment", "Apparel", "Accessories", "Fitness", "Camping"]
    }
    
    # Define brands for each category
    brands = {
        "Electronics": ["Apple", "Samsung", "Sony", "Bose", "Dell", "HP", "Lenovo"],
        "Clothing": ["Nike", "Adidas", "Zara", "H&M", "Levi's", "Gucci", "Puma"],
        "Books": ["Penguin", "HarperCollins", "Random House", "Scholastic", "Wiley"],
        "Home & Garden": ["IKEA", "Home Depot", "Wayfair", "Williams-Sonoma", "Pottery Barn"],
        "Sports & Outdoors": ["Nike", "Adidas", "Under Armour", "The North Face", "Columbia"]
    }
    
    products = []
    
    for i in range(num_products):
        # Select random category and subcategory
        category = random.choice(list(categories.keys()))
        subcategory = random.choice(categories[category])
        
        # Generate product data
        product = {
            "ID": i + 1,
            "Name": {
                "text": fake.catch_phrase(),
                "keyword": f"{subcategory} - {fake.word().capitalize()} {fake.word().capitalize()}"
            },
            "Description": fake.text(max_nb_chars=200),
            "Category": category,
            "Subcategory": subcategory,
            "Price": round(random.uniform(10.0, 2000.0), 2),
            "StockQty": random.randint(0, 1000),
            "Brand": random.choice(brands[category]),
            "CreatedTime": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
            "UpdatedTime": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
            "Rating": round(random.uniform(0, 5), 1),
            "Active": random.choice([True, False])
        }
        
        products.append(product)
    
    return products

def format_product_details(product):
    """Format product details for display.
    
    Args:
        product (dict): Product document
        
    Returns:
        str: Formatted product details
    """
    return f"""
Product ID: {product.get('ID', 'N/A')}
Name: {product.get('Name', {}).get('text', 'N/A')}
Category: {product.get('Category', 'N/A')} > {product.get('Subcategory', 'N/A')}
Brand: {product.get('Brand', 'N/A')}
Price: ${product.get('Price', 0):.2f}
Stock: {product.get('StockQty', 0)} units
Rating: {product.get('Rating', 0):.1f}/5.0
Status: {'Active' if product.get('Active', False) else 'Inactive'}
Description: {product.get('Description', 'N/A')}
Created: {product.get('CreatedTime', 'N/A')}
Updated: {product.get('UpdatedTime', 'N/A')}
{'='*50}""" 