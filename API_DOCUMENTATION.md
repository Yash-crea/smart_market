# Comprehensive API Endpoints Documentation

Your grocery store website now has a complete REST API with machine learning capabilities! Here are all the available endpoints:

## 🔗 Base URL
- **Local Development:** `http://127.0.0.1:8000/api/v1/`

## 🔐 Authentication Endpoints

### Register New User
```http
POST /api/v1/auth/register/
Content-Type: application/json

{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Login & Get Token
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
    "username": "testuser",
    "password": "securepassword123"
}
```

**Response:**
```json
{
    "token": "abc123def456...",
    "user_id": 1,
    "email": "test@example.com",
    "username": "testuser",
    "is_staff": false
}
```

## 🛍️ Product Management

### Get All Products
```http
GET /api/v1/products/
GET /api/v1/products/?category=electronics&min_price=10&max_price=100&search=phone
```

### Get Single Product
```http
GET /api/v1/products/1/
```

### Smart Products with ML Features
```http
GET /api/v1/smart-products/
GET /api/v1/smart-products/?season=spring&festival=holi&in_stock=true
```

### Product Categories
```http
GET /api/v1/categories/
GET /api/v1/categories/1/products/  # All products in category
```

## 🤖 Machine Learning Recommendations

### Get Personalized Recommendations
```http
GET /api/v1/recommendations/?algorithm_type=hybrid&limit=10&include_context=true
```

**Algorithm Types:**
- `seasonal` - Based on current season
- `weather` - Weather-dependent products  
- `trending` - High-demand predictions
- `discount` - Promotional products
- `hybrid` - Combined approach (recommended)

**Response:**
```json
{
    "algorithm_type": "hybrid",
    "recommendations": [
        {
            "id": 1,
            "type": "smart_product", 
            "name": "Winter Jacket",
            "price": 99.99,
            "score": 95.5,
            "reason": "Perfect for winter season"
        }
    ],
    "context": {
        "current_season": "winter",
        "upcoming_festivals": ["christmas"],
        "is_weekend": false,
        "weather_condition": "cold"
    },
    "total_count": 10
}
```

### Specialized Product Recommendations
```http
GET /api/v1/smart-products/seasonal/     # Current season products
GET /api/v1/smart-products/festival/     # Festival products
GET /api/v1/smart-products/promotional/  # On sale products
GET /api/v1/products/trending/           # Trending by ML predictions
GET /api/v1/products/low-stock/          # Products needing restock
```

### Log User Interactions (for ML learning)
```http
POST /api/v1/interactions/log/
Authorization: Token abc123def456...
Content-Type: application/json

{
    "product_id": 1,
    "product_type": "smart",
    "interaction_type": "view",
    "recommendation_type": "seasonal"
}
```

**Interaction Types:** `view`, `add_to_cart`, `purchase`

## 🛒 Shopping Cart Management

### Get User's Cart
```http
GET /api/v1/carts/
Authorization: Token abc123def456...
```

### Add Item to Cart
```http
POST /api/v1/cart/add-item/
Authorization: Token abc123def456...
Content-Type: application/json

{
    "product_id": 1,
    "product_type": "smart",
    "quantity": 2
}
```

### Update Cart Item Quantity
```http
POST /api/v1/cart/update-quantity/
Authorization: Token abc123def456...
Content-Type: application/json

{
    "item_id": 1,
    "quantity": 3
}
```

### Remove Item from Cart
```http
POST /api/v1/cart/remove-item/
Authorization: Token abc123def456...
Content-Type: application/json

{
    "item_id": 1
}
```

### Clear Entire Cart
```http
POST /api/v1/cart/clear/
Authorization: Token abc123def456...
```

## 📦 Order Management

### Get User Orders
```http
GET /api/v1/orders/
Authorization: Token abc123def456...
```

### Create Order from Cart
```http
POST /api/v1/orders/create-from-cart/
Authorization: Token abc123def456...
Content-Type: application/json

{
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "customer_phone": "123-456-7890",
    "shipping_address": "123 Main St",
    "shipping_city": "New York",
    "shipping_postal_code": "10001"
}
```

### Get Single Order
```http
GET /api/v1/orders/1/
Authorization: Token abc123def456...
```

## 🧠 Machine Learning Models

### Get ML Models
```http
GET /api/v1/ml-models/
Authorization: Token abc123def456...
```

### Train ML Model
```http
POST /api/v1/ml/train/1/
Authorization: Token abc123def456...
```

### Generate Prediction
```http
POST /api/v1/ml/predict/
Authorization: Token abc123def456...
Content-Type: application/json

{
    "product_id": 1,
    "product_type": "smart",
    "horizon": "7d",
    "include_weather": true,
    "include_seasonal": true
}
```

### Get Predictions History
```http
GET /api/v1/predictions/?model_id=1&product_id=1&horizon=7d
Authorization: Token abc123def456...
```

## 🌤️ Weather Data (for Weather-based Recommendations)

### Get Current Weather
```http
GET /api/v1/weather/current/
Authorization: Token abc123def456...
```

### Get Weather Forecast
```http
GET /api/v1/weather/forecast/?days=7
Authorization: Token abc123def456...
```

### Add Weather Data
```http
POST /api/v1/weather/
Authorization: Token abc123def456...
Content-Type: application/json

{
    "date": "2026-03-07",
    "location": "Store Location",
    "temperature_avg": 20.5,
    "temperature_min": 15.0,
    "temperature_max": 25.0,
    "humidity": 65.5,
    "rainfall": 0.0,
    "wind_speed": 10.2,
    "condition": "sunny"
}
```

## 📊 Analytics & Reports

### Recommendation Analytics
```http
GET /api/v1/recommendations/analytics/?days=30
Authorization: Token abc123def456...
```

**Response:**
```json
{
    "total_recommendations": 150,
    "total_views": 120,
    "total_cart_adds": 45,
    "total_purchases": 25,
    "view_rate": 80.0,
    "cart_conversion_rate": 30.0,
    "purchase_conversion_rate": 16.7
}
```

### Sales Analytics
```http
GET /api/v1/analytics/orders/?days=30
Authorization: Token abc123def456...
```

### Seasonal Sales Trends
```http
GET /api/v1/seasonal-data/?year=2026&season=spring
GET /api/v1/analytics/sales-trends/?year=2026
Authorization: Token abc123def456...
```

## 🔍 Search & Filtering

All list endpoints support these query parameters:

### Products
- `search` - Search in name/description
- `category` - Filter by category
- `min_price` / `max_price` - Price range
- `in_stock` - Only in-stock items (`true`/`false`)

### Smart Products (additional filters)
- `season` - Filter by peak season
- `festival` - Filter by festival association
- `weather_dependent` - Weather-sensitive products

### Orders
- `status` - Filter by order status
- `start_date` / `end_date` - Date range filtering

## 📚 Testing Your API

### 1. Using curl (Command Line)
```bash
# Get recommendations
curl "http://127.0.0.1:8000/api/v1/recommendations/?algorithm_type=seasonal&limit=5"

# Register user
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123","email":"test@example.com"}' \
  http://127.0.0.1:8000/api/v1/auth/register/

# Add to cart (requires token)
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -d '{"product_id":1,"product_type":"smart","quantity":2}' \
  http://127.0.0.1:8000/api/v1/cart/add-item/
```

### 2. Using JavaScript (Frontend)
```javascript
// Get recommendations
async function getRecommendations() {
    const response = await fetch('/api/v1/recommendations/?algorithm_type=hybrid&limit=10');
    const data = await response.json();
    console.log(data);
}

// Add to cart (with authentication)
async function addToCart(productId, quantity) {
    const response = await fetch('/api/v1/cart/add-item/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${userToken}`
        },
        body: JSON.stringify({
            product_id: productId,
            product_type: 'smart',
            quantity: quantity
        })
    });
    return response.json();
}
```

### 3. Using Python requests
```python
import requests

# Get recommendations
response = requests.get('http://127.0.0.1:8000/api/v1/recommendations/')
recommendations = response.json()

# Login and get token
login_data = {'username': 'testuser', 'password': 'test123'}
response = requests.post('http://127.0.0.1:8000/api/v1/auth/login/', json=login_data)
token = response.json()['token']

# Add to cart
headers = {'Authorization': f'Token {token}'}
cart_data = {'product_id': 1, 'product_type': 'smart', 'quantity': 2}
response = requests.post('http://127.0.0.1:8000/api/v1/cart/add-item/', 
                        json=cart_data, headers=headers)
```

## 🚀 Key Features

✅ **Complete CRUD Operations** - Full Create, Read, Update, Delete for all resources
✅ **Token Authentication** - Secure API access with user tokens
✅ **Machine Learning Integration** - Smart recommendations and predictions
✅ **Real-time Cart Management** - Add/remove/update cart items
✅ **Order Processing** - Complete order flow from cart to completion
✅ **Analytics & Reporting** - Sales trends and recommendation performance
✅ **Weather-based Recommendations** - Products based on weather conditions
✅ **Seasonal Intelligence** - Season and festival-aware recommendations
✅ **Search & Filtering** - Advanced product search capabilities
✅ **User Behavior Tracking** - ML learning from user interactions
✅ **CORS Support** - Ready for frontend integration

## 🔧 Next Steps

1. **Start your server:** `python manage.py runserver`
2. **Test endpoints:** Use the examples above
3. **Create a superuser:** `python manage.py createsuperuser`
4. **Add sample data:** Create products and categories via admin or API
5. **Frontend Integration:** Use the API in React/Vue/Angular applications

Your API is production-ready and includes comprehensive machine learning capabilities!