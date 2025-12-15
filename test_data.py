#!/usr/bin/env python3
"""
Script to initialize the database with sample data for testing
"""

from db.models import Database

def initialize_sample_data():
    db = Database()
    
    # Add some sample products
    sample_products = [
        {
            "name": "Wireless Headphones",
            "description": "High-quality wireless headphones with noise cancellation",
            "price": 99.99,
            "image_url": "https://example.com/headphones.jpg"
        },
        {
            "name": "Smart Watch",
            "description": "Feature-rich smartwatch with health monitoring",
            "price": 199.99,
            "image_url": "https://example.com/smartwatch.jpg"
        },
        {
            "name": "Laptop Stand",
            "description": "Adjustable aluminum laptop stand for better ergonomics",
            "price": 39.99,
            "image_url": "https://example.com/laptop-stand.jpg"
        }
    ]
    
    for product in sample_products:
        db.add_product(
            name=product["name"],
            description=product["description"],
            price=product["price"],
            image_url=product["image_url"]
        )
    
    print("Sample data added successfully!")
    print(f"Added {len(sample_products)} products to the database.")
    
    # Show all products
    products = db.get_all_products()
    print("\nCurrent products in database:")
    for product in products:
        print(f"- {product['name']}: ${product['price']}")

if __name__ == "__main__":
    initialize_sample_data()