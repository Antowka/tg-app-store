from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import json
import hashlib
import hmac
import urllib.parse

from fastapi.templating import Jinja2Templates

from db.models import Database
from utils.admin_checker import is_admin, add_admin, remove_admin

app = FastAPI()

# Подключаем папку с шаблонами
templates = Jinja2Templates(directory="./workspace/templates")

# Mount static files for templates
app.mount("/static", StaticFiles(directory="./workspace/static"), name="static")

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
@app.get("/miniapp")
async def mini_app(request: Request):
    """
    Serve the main page for the Telegram Mini App
    """
    return templates.TemplateResponse(
        "app.html",
        {"request": request}
    )