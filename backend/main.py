from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import json
import hashlib
import hmac
import urllib.parse
from db.models import Database
from utils.admin_checker import is_admin, add_admin, remove_admin

app = FastAPI()

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="/workspace/frontend/static"), name="static")

# Initialize database
db = Database()

# Pydantic models
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    image_url: Optional[str] = None

class ProductUpdate(ProductCreate):
    id: int

class OrderStatusUpdate(BaseModel):
    order_id: int
    status: str

class AdminAction(BaseModel):
    action: str  # "add" or "remove"
    admin_id: str

# Telegram WebApp auth verification
def verify_telegram_webapp_data(initData: str, bot_token: str) -> dict:
    """
    Verify Telegram WebApp initData to ensure the request is legitimate
    """
    try:
        # Parse query parameters
        parsed_data = dict(urllib.parse.parse_qsl(initData))
        received_hash = parsed_data.pop('hash', '')
        
        # Sort data alphabetically by key
        sorted_data = sorted(parsed_data.items())
        data_check_string = '\n'.join([f'{k}={v}' for k, v in sorted_data])
        
        # Create secret key using SHA256 of bot token
        secret_key = hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()
        
        # Calculate expected hash
        expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        # Compare hashes
        if received_hash != expected_hash:
            raise ValueError("Invalid hash")
        
        # Return user data
        return json.loads(parsed_data['user']) if 'user' in parsed_data else {}
    except Exception as e:
        print(f"Error verifying Telegram WebApp data: {e}")
        return {}

def require_auth(request: Request):
    """
    Verify that the request comes from Telegram WebApp
    """
    # In production, you would verify the initData here
    # For now, we'll skip this for development purposes
    # You should replace 'YOUR_BOT_TOKEN' with your actual bot token
    # user_data = verify_telegram_webapp_data(
    #     request.headers.get('X-Init-Data', ''), 
    #     'YOUR_BOT_TOKEN'
    # )
    # if not user_data:
    #     raise HTTPException(status_code=401, detail="Unauthorized")
    # return user_data
    
    # For development purposes, return a mock user
    return {"id": "123456789", "username": "test_user"}

def require_admin(user_data: dict = Depends(require_auth)):
    """
    Verify that the user is an admin
    """
    if not is_admin(str(user_data["id"])):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_data

@app.get("/")
async def root():
    return {"message": "Telegram Mini Shop API"}

@app.get("/products", response_model=List[dict])
async def get_products():
    """
    Get all products
    """
    products = db.get_all_products()
    return products

@app.post("/products", dependencies=[Depends(require_admin)])
async def create_product(product: ProductCreate, user_data: dict = Depends(require_auth)):
    """
    Create a new product (admin only)
    """
    product_id = db.add_product(
        name=product.name,
        description=product.description,
        price=product.price,
        image_url=product.image_url
    )
    return {"id": product_id, "message": "Product created successfully"}

@app.put("/products/{product_id}", dependencies=[Depends(require_admin)])
async def update_product(product_id: int, product: ProductUpdate, user_data: dict = Depends(require_auth)):
    """
    Update an existing product (admin only)
    """
    db.update_product(
        product_id=product_id,
        name=product.name,
        description=product.description,
        price=product.price,
        image_url=product.image_url
    )
    return {"message": "Product updated successfully"}

@app.delete("/products/{product_id}", dependencies=[Depends(require_admin)])
async def delete_product(product_id: int, user_data: dict = Depends(require_auth)):
    """
    Delete a product (admin only)
    """
    db.delete_product(product_id)
    return {"message": "Product deleted successfully"}

@app.post("/orders", response_model=dict)
async def create_order(request: Request):
    """
    Create a new order
    """
    data = await request.json()
    product_id = data.get("product_id")
    user_id = data.get("user_id")
    user_username = data.get("user_username", "")
    user_full_name = data.get("user_full_name", "")
    
    if not product_id or not user_id:
        raise HTTPException(status_code=400, detail="Missing product_id or user_id")
    
    order_id = db.place_order(product_id, user_id, user_username, user_full_name)
    
    # Here you could add logic to notify admins about the new order
    # For example, sending a message to a Telegram channel/group
    
    return {
        "order_id": order_id,
        "message": "Order placed successfully. Seller will contact you soon."
    }

@app.get("/orders", dependencies=[Depends(require_admin)])
async def get_orders(user_data: dict = Depends(require_auth)):
    """
    Get all orders (admin only)
    """
    orders = db.get_orders()
    return orders

@app.put("/orders/status", dependencies=[Depends(require_admin)])
async def update_order_status(update_data: OrderStatusUpdate, user_data: dict = Depends(require_auth)):
    """
    Update order status (admin only)
    """
    db.update_order_status(update_data.order_id, update_data.status)
    return {"message": "Order status updated successfully"}

@app.post("/admin", dependencies=[Depends(require_admin)])
async def manage_admins(admin_action: AdminAction, user_data: dict = Depends(require_auth)):
    """
    Add or remove admins (admin only)
    """
    if admin_action.action == "add":
        success = add_admin(admin_action.admin_id)
        if success:
            return {"message": f"Admin {admin_action.admin_id} added successfully"}
        else:
            return {"message": f"Admin {admin_action.admin_id} already exists"}
    
    elif admin_action.action == "remove":
        success = remove_admin(admin_action.admin_id)
        if success:
            return {"message": f"Admin {admin_action.admin_id} removed successfully"}
        else:
            return {"message": f"Admin {admin_action.admin_id} not found"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'add' or 'remove'.")

@app.get("/user/check-admin")
async def check_admin(request: Request):
    """
    Check if the current user is an admin
    """
    # Extract user data from request headers (in real implementation, this would come from Telegram WebApp init data)
    user_id = request.headers.get("X-User-ID", "unknown")
    return {"is_admin": is_admin(user_id)}

# Frontend endpoints
@app.get("/miniapp", response_class=HTMLResponse)
async def mini_app():
    """
    Serve the main page for the Telegram Mini App
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram Shop Mini App</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .product-card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                background: white;
            }
            .product-image {
                width: 100%;
                height: 200px;
                object-fit: cover;
                border-radius: 5px;
            }
            .product-title {
                font-size: 1.2em;
                font-weight: bold;
                margin: 10px 0 5px 0;
            }
            .product-price {
                color: #2e8b57;
                font-weight: bold;
                font-size: 1.1em;
            }
            .product-description {
                margin: 10px 0;
                color: #555;
            }
            .buy-button {
                background-color: #2e8b57;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
            }
            .buy-button:hover {
                background-color: #256f4a;
            }
            .admin-section {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }
            .admin-controls button {
                margin-right: 10px;
                margin-bottom: 10px;
            }
            .order-item {
                border: 1px solid #eee;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Telegram Shop</h1>
            
            <div id="products-container">
                <!-- Products will be loaded here -->
            </div>
            
            <div id="admin-section" class="admin-section" style="display: none;">
                <h2>Admin Controls</h2>
                
                <h3>Add New Product</h3>
                <form id="add-product-form">
                    <input type="text" id="product-name" placeholder="Product Name" required><br><br>
                    <textarea id="product-description" placeholder="Description" required></textarea><br><br>
                    <input type="number" id="product-price" placeholder="Price" step="0.01" required><br><br>
                    <input type="text" id="product-image" placeholder="Image URL (optional)"><br><br>
                    <button type="submit">Add Product</button>
                </form>
                
                <h3>Orders</h3>
                <div id="orders-container">
                    <!-- Orders will be loaded here -->
                </div>
            </div>
        </div>

        <script>
            // Initialize Telegram WebApp
            const tg = window.Telegram.WebApp;
            
            // Expand the web app to full size
            tg.expand();
            
            // Enable closing confirmation
            tg.enableClosingConfirmation();
            
            // Function to load products
            async function loadProducts() {
                try {
                    const response = await fetch('/products');
                    const products = await response.json();
                    
                    const container = document.getElementById('products-container');
                    container.innerHTML = '';
                    
                    products.forEach(product => {
                        const card = document.createElement('div');
                        card.className = 'product-card';
                        
                        card.innerHTML = `
                            <div class="product-title">${product.name}</div>
                            ${product.image_url ? `<img src="${product.image_url}" alt="${product.name}" class="product-image">` : ''}
                            <div class="product-description">${product.description}</div>
                            <div class="product-price">$${product.price.toFixed(2)}</div>
                            <button class="buy-button" onclick="buyProduct(${product.id})">Buy Now</button>
                            ${window.isAdmin ? `<button onclick="deleteProduct(${product.id})" style="background-color: #ff4444; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 1em; margin-top: 10px;">Delete</button>` : ''}
                        `;
                        
                        container.appendChild(card);
                    });
                } catch (error) {
                    console.error('Error loading products:', error);
                }
            }
            
            // Function to handle buying a product
            async function buyProduct(productId) {
                // Get user info from Telegram WebApp
                const user = tg.initDataUnsafe?.user || { id: 'unknown', username: 'unknown', first_name: 'Unknown' };
                
                try {
                    const response = await fetch('/orders', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            product_id: productId,
                            user_id: user.id,
                            user_username: user.username || '',
                            user_full_name: `${user.first_name || ''} ${user.last_name || ''}`.trim()
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        tg.showAlert('Order placed successfully! Seller will contact you soon.');
                    } else {
                        tg.showAlert('Error placing order: ' + (result.detail || 'Unknown error'));
                    }
                } catch (error) {
                    console.error('Error placing order:', error);
                    tg.showAlert('Error placing order: ' + error.message);
                }
            }
            
            // Function to delete a product (admin only)
            async function deleteProduct(productId) {
                if (!confirm('Are you sure you want to delete this product?')) {
                    return;
                }
                
                try {
                    const response = await fetch(`/products/${productId}`, {
                        method: 'DELETE'
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        tg.showAlert('Product deleted successfully!');
                        loadProducts(); // Refresh products list
                    } else {
                        tg.showAlert('Error deleting product: ' + (result.detail || 'Unknown error'));
                    }
                } catch (error) {
                    console.error('Error deleting product:', error);
                    tg.showAlert('Error deleting product: ' + error.message);
                }
            }
            
            // Global variable to track admin status
            let isAdmin = false;
            
            // Function to check if user is admin
            async function checkAdmin() {
                try {
                    // In real implementation, we'd pass the user ID from Telegram
                    const userId = tg.initDataUnsafe?.user?.id || 'unknown';
                    const response = await fetch('/user/check-admin', {
                        headers: {
                            'X-User-ID': userId.toString()
                        }
                    });
                    const result = await response.json();
                    
                    if (result.is_admin) {
                        isAdmin = true;
                        document.getElementById('admin-section').style.display = 'block';
                        loadOrders(); // Load orders for admin
                    }
                } catch (error) {
                    console.error('Error checking admin status:', error);
                }
            }
            
            // Function to load orders (admin only)
            async function loadOrders() {
                try {
                    const response = await fetch('/orders');
                    if (response.ok) {
                        const orders = await response.json();
                        const container = document.getElementById('orders-container');
                        
                        container.innerHTML = '';
                        
                        if (orders.length === 0) {
                            container.innerHTML = '<p>No orders yet.</p>';
                            return;
                        }
                        
                        orders.forEach(order => {
                            const orderElement = document.createElement('div');
                            orderElement.className = 'order-item';
                            
                            orderElement.innerHTML = `
                                <strong>Order #${order.id}</strong> - ${order.status}<br>
                                Product: ${order.product_name}<br>
                                User: ${order.user_full_name} (@${order.user_username})<br>
                                User ID: ${order.user_id}<br>
                                Date: ${new Date(order.created_at).toLocaleString()}<br>
                                <button onclick="updateOrderStatus(${order.id}, 'completed')">Mark as Completed</button>
                                <button onclick="updateOrderStatus(${order.id}, 'cancelled')">Cancel</button>
                            `;
                            
                            container.appendChild(orderElement);
                        });
                    }
                } catch (error) {
                    console.error('Error loading orders:', error);
                }
            }
            
            // Function to update order status (admin only)
            async function updateOrderStatus(orderId, status) {
                try {
                    const response = await fetch('/orders/status', {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            order_id: orderId,
                            status: status
                        })
                    });
                    
                    if (response.ok) {
                        tg.showAlert(`Order status updated to ${status}`);
                        loadOrders(); // Refresh orders list
                    } else {
                        tg.showAlert('Error updating order status');
                    }
                } catch (error) {
                    console.error('Error updating order status:', error);
                    tg.showAlert('Error updating order status: ' + error.message);
                }
            }
            
            // Handle form submission for adding a product
            document.getElementById('add-product-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const name = document.getElementById('product-name').value;
                const description = document.getElementById('product-description').value;
                const price = parseFloat(document.getElementById('product-price').value);
                const imageUrl = document.getElementById('product-image').value || null;
                
                try {
                    const response = await fetch('/products', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            name: name,
                            description: description,
                            price: price,
                            image_url: imageUrl
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        tg.showAlert('Product added successfully!');
                        document.getElementById('add-product-form').reset();
                        loadProducts(); // Refresh products list
                    } else {
                        tg.showAlert('Error adding product: ' + (result.detail || 'Unknown error'));
                    }
                } catch (error) {
                    console.error('Error adding product:', error);
                    tg.showAlert('Error adding product: ' + error.message);
                }
            });
            
            // Initial load
            loadProducts();
            checkAdmin();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)