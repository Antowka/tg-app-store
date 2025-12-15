import sqlite3
from datetime import datetime
from typing import List, Optional

class Database:
    def __init__(self, db_path: str = "shop.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                user_username TEXT,
                user_full_name TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_product(self, name: str, description: str, price: float, image_url: str = None) -> int:
        """Add a new product to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO products (name, description, price, image_url)
            VALUES (?, ?, ?, ?)
        ''', (name, description, price, image_url))
        
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return product_id

    def update_product(self, product_id: int, name: str, description: str, price: float, image_url: str = None):
        """Update an existing product"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE products
            SET name = ?, description = ?, price = ?, image_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (name, description, price, image_url, product_id))
        
        conn.commit()
        conn.close()

    def delete_product(self, product_id: int):
        """Delete a product from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        
        conn.commit()
        conn.close()

    def get_all_products(self) -> List[dict]:
        """Get all products from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        products = []
        for row in rows:
            products.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'price': row[3],
                'image_url': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            })
        
        conn.close()
        return products

    def get_product_by_id(self, product_id: int) -> Optional[dict]:
        """Get a specific product by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'price': row[3],
                'image_url': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            }
        
        conn.close()
        return None

    def place_order(self, product_id: int, user_id: int, user_username: str, user_full_name: str) -> int:
        """Place a new order"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (product_id, user_id, user_username, user_full_name)
            VALUES (?, ?, ?, ?)
        ''', (product_id, user_id, user_username, user_full_name))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return order_id

    def get_orders(self) -> List[dict]:
        """Get all orders from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT o.id, o.product_id, p.name as product_name, o.user_id, o.user_username, 
                   o.user_full_name, o.status, o.created_at
            FROM orders o
            JOIN products p ON o.product_id = p.id
            ORDER BY o.created_at DESC
        ''')
        rows = cursor.fetchall()
        
        orders = []
        for row in rows:
            orders.append({
                'id': row[0],
                'product_id': row[1],
                'product_name': row[2],
                'user_id': row[3],
                'user_username': row[4],
                'user_full_name': row[5],
                'status': row[6],
                'created_at': row[7]
            })
        
        conn.close()
        return orders

    def update_order_status(self, order_id: int, status: str):
        """Update order status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        
        conn.commit()
        conn.close()