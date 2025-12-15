# Telegram Mini Shop

A Telegram Mini App for a shop with product cards that allows users to browse and purchase products directly from a Telegram channel or community.

## Features

- **Product Management**: Admins can add, edit, and delete products
- **Order Processing**: Users can place orders which are sent to admins
- **Admin Interface**: Built-in admin panel accessible through the Mini App
- **User Authentication**: Integration with Telegram WebApp authentication
- **SQLite Database**: Local storage for products and orders

## Architecture

- **Backend**: FastAPI application serving the API and frontend
- **Database**: SQLite for storing products and orders
- **Frontend**: HTML/CSS/JavaScript served as a Telegram Mini App
- **Authentication**: Telegram WebApp initialization data validation

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python run_server.py
   ```

3. Access the Mini App at `http://localhost:8000/miniapp`

## Configuration

- Admin user IDs are stored in `config/admins.json`
- Modify this file to add/remove admin users
- The database (`shop.db`) will be created automatically on first run

## API Endpoints

- `GET /products` - Get all products
- `POST /products` - Add a new product (admin only)
- `PUT /products/{id}` - Update a product (admin only)
- `DELETE /products/{id}` - Delete a product (admin only)
- `POST /orders` - Place a new order
- `GET /orders` - Get all orders (admin only)
- `PUT /orders/status` - Update order status (admin only)

## How It Works

1. **For Users**:
   - Browse products in the Mini App
   - Click "Buy Now" to place an order
   - Receive confirmation that seller will contact them

2. **For Admins**:
   - Access admin controls in the Mini App
   - Add/edit/delete products
   - View and manage orders
   - Update order statuses

## Security

- Only users listed in `config/admins.json` can access admin functions
- Telegram WebApp authentication ensures requests come from valid sources
- Input validation on all endpoints