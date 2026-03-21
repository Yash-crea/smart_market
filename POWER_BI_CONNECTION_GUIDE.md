# Power BI Connection Guide for Django Grocery Store APIs

## 🔌 Connecting Your Django APIs to Power BI

### Prerequisites
- Power BI Desktop or Power BI Service access
- Django server running (localhost:8000 or production URL)
- API endpoints accessible and returning JSON data

---

## Method 1: Web Data Source Connection

### Step 1: Start Django Server
```bash
cd grocerystore
python manage.py runserver 0.0.0.0:8000
```

### Step 2: Available API Endpoints for Power BI

#### 📊 **Sales & Analytics APIs**
```
GET /api/v1/powerbi/sales-analytics/
GET /api/v1/powerbi/demand-forecasts/
GET /api/v1/powerbi/inventory-alerts/
GET /api/v1/powerbi/ml-predictions/generate/
GET /api/v1/powerbi/ml-models/performance/
```

#### 🎯 **Recommendation APIs**
```
GET /api/v1/recommendations/personalized/?user_id=123&limit=50
GET /api/v1/recommendations/analytics/
GET /api/v1/forecast/30day/123/
GET /api/v1/models/status/
```

#### 📦 **Product & Inventory APIs**
```
GET /api/v1/products/?format=json
GET /api/v1/smart-products/?format=json
GET /api/v1/categories/?format=json
GET /api/v1/orders/?format=json
```

---

## Method 2: Custom Power Query M Functions

### Sales Analytics Connector
```powerquery
let
    BaseURL = "http://localhost:8000/api/v1/",
    
    // Function to get sales data
    GetSalesAnalytics = () =>
        let
            Source = Json.Document(Web.Contents(BaseURL & "powerbi/sales-analytics/")),
            Data = Source[data],
            Table = Table.FromList(Data, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
            Expanded = Table.ExpandRecordColumn(Table, "Column1", 
                {"product_name", "category", "total_sales", "revenue", "date"}, 
                {"Product Name", "Category", "Total Sales", "Revenue", "Date"})
        in
            Expanded,
    
    // Function to get demand forecasts
    GetDemandForecasts = () =>
        let
            Source = Json.Document(Web.Contents(BaseURL & "powerbi/demand-forecasts/")),
            Data = Source[forecasts],
            Table = Table.FromList(Data, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
            Expanded = Table.ExpandRecordColumn(Table, "Column1", 
                {"product_name", "predicted_demand", "forecast_date", "confidence"}, 
                {"Product", "Predicted Demand", "Forecast Date", "Confidence"})
        in
            Expanded,
    
    // Function to get recommendations analytics
    GetRecommendationAnalytics = () =>
        let
            Source = Json.Document(Web.Contents(BaseURL & "recommendations/analytics/")),
            Data = Source[analytics],
            Table = Table.FromList(Data, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
            Expanded = Table.ExpandRecordColumn(Table, "Column1", 
                {"product_name", "recommendation_score", "click_rate", "conversion_rate"}, 
                {"Product", "Score", "Click Rate", "Conversion Rate"})
        in
            Expanded

in
    [
        SalesAnalytics = GetSalesAnalytics,
        DemandForecasts = GetDemandForecasts,
        RecommendationAnalytics = GetRecommendationAnalytics
    ]
```

---

## Method 3: Direct JSON Import

### Step 1: Open Power BI Desktop
1. Click **Get Data**
2. Select **Web**
3. Enter your API URL

### Step 2: Configure Each Data Source

#### Sales Data Connection
```
URL: http://localhost:8000/api/v1/powerbi/sales-analytics/
Advanced Options:
- HTTP request header: Content-Type: application/json
- Timeout: 30 seconds
```

#### ML Predictions Connection
```
URL: http://localhost:8000/api/v1/powerbi/ml-predictions/generate/
Method: GET
Headers: Accept: application/json
```

#### Product Recommendations Connection
```
URL: http://localhost:8000/api/v1/recommendations/personalized/?limit=100&format=json
Headers: Content-Type: application/json
```

---

## Method 4: Python Script in Power BI

### Custom Python Data Source
```python
import pandas as pd
import requests
import json

# API Configuration
base_url = "http://localhost:8000/api/v1/"
headers = {"Content-Type": "application/json"}

def fetch_api_data(endpoint):
    """Fetch data from Django API"""
    try:
        response = requests.get(base_url + endpoint, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching {endpoint}: {e}")
        return None

# Fetch Sales Analytics
sales_data = fetch_api_data("powerbi/sales-analytics/")
if sales_data and 'data' in sales_data:
    df_sales = pd.DataFrame(sales_data['data'])
else:
    df_sales = pd.DataFrame()

# Fetch Demand Forecasts
forecast_data = fetch_api_data("powerbi/demand-forecasts/")
if forecast_data and 'forecasts' in forecast_data:
    df_forecasts = pd.DataFrame(forecast_data['forecasts'])
else:
    df_forecasts = pd.DataFrame()

# Fetch Product Data
products_data = fetch_api_data("products/?format=json")
if products_data and 'results' in products_data:
    df_products = pd.DataFrame(products_data['results'])
elif isinstance(products_data, list):
    df_products = pd.DataFrame(products_data)
else:
    df_products = pd.DataFrame()

# Fetch ML Model Performance
model_data = fetch_api_data("models/status/")
if model_data and 'models' in model_data:
    df_models = pd.DataFrame(model_data['models'])
else:
    df_models = pd.DataFrame()

print("Data loaded successfully!")
print(f"Sales records: {len(df_sales)}")
print(f"Forecast records: {len(df_forecasts)}")
print(f"Products: {len(df_products)}")
print(f"ML Models: {len(df_models)}")
```

---

## Authentication & Security

### Option 1: API Key Authentication (Recommended)
Add to Django settings.py:
```python
# API Key for Power BI
POWER_BI_API_KEY = "your-secure-api-key-here"

# Add to middleware or view decorators
def api_key_required(view_func):
    def wrapper(request, *args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.GET.get('api_key')
        if api_key != settings.POWER_BI_API_KEY:
            return JsonResponse({'error': 'Invalid API key'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper
```

Power BI Header:
```
X-API-Key: your-secure-api-key-here
```

### Option 2: Token Authentication
Power BI Advanced Options:
```
Headers:
Authorization: Token your-django-token-here
Content-Type: application/json
```

---

## Data Refresh Setup

### Automated Refresh Schedule
1. **Power BI Service**: Set up scheduled refresh every 1-8 hours
2. **On-Premises Gateway**: For local Django server
3. **Real-time Streaming**: For live dashboards

### Refresh Configuration
```json
{
    "refreshSchedule": {
        "frequency": "hourly",
        "interval": 2,
        "enabled": true
    },
    "dataSource": {
        "connectionString": "http://your-django-server.com/api/v1/",
        "timeout": 60
    }
}
```

---

## Sample Power BI Dashboard Queries

### Sales Performance Query
```powerquery
let
    Source = Json.Document(Web.Contents("http://localhost:8000/api/v1/powerbi/sales-analytics/")),
    Data = Source[data],
    #"Converted to Table" = Table.FromList(Data, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    #"Expanded Column1" = Table.ExpandRecordColumn(#"Converted to Table", "Column1", 
        {"product_name", "category", "total_sales", "revenue", "date", "growth_rate"}, 
        {"Product", "Category", "Sales", "Revenue", "Date", "Growth"}),
    #"Changed Type" = Table.TransformColumnTypes(#"Expanded Column1",{
        {"Date", type date}, 
        {"Sales", Int64.Type}, 
        {"Revenue", type number}, 
        {"Growth", type number}})
in
    #"Changed Type"
```

### ML Model Performance Query
```powerquery
let
    Source = Json.Document(Web.Contents("http://localhost:8000/api/v1/models/status/")),
    Models = Source[models],
    #"Converted to Table" = Table.FromList(Models, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    #"Expanded Models" = Table.ExpandRecordColumn(#"Converted to Table", "Column1", 
        {"model_name", "accuracy", "rmse", "mae", "last_trained"}, 
        {"Model", "Accuracy", "RMSE", "MAE", "Last Trained"})
in
    #"Expanded Models"
```

---

## Troubleshooting Common Issues

### 1. CORS Error
Add to Django settings.py:
```python
CORS_ALLOWED_ORIGINS = [
    "https://app.powerbi.com",
    "https://powerbi.microsoft.com",
]
CORS_ALLOW_CREDENTIALS = True
```

### 2. Timeout Issues
```python
# Increase timeout in Django views
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
@api_view(['GET'])
def powerbi_sales_analytics(request):
    # Your view logic
    pass
```

### 3. Large Data Sets
```python
# Implement pagination
from rest_framework.pagination import PageNumberPagination

class PowerBIPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 5000
```

---

## Advanced Features

### Real-time Streaming Dataset
```python
# Django view for streaming data
from django.http import StreamingHttpResponse
import json
import time

def stream_sales_data(request):
    def generate_data():
        while True:
            # Get latest data
            latest_sales = get_latest_sales_data()
            yield f"data: {json.dumps(latest_sales)}\n\n"
            time.sleep(30)  # Update every 30 seconds
    
    response = StreamingHttpResponse(generate_data(), content_type='text/plain')
    response['Cache-Control'] = 'no-cache'
    return response
```

### Custom Connectors
Create `.pqx` file for Power BI custom connector:
```powerquery
[Version = "1.0.0"]
section GroceryStoreConnector;

[DataSource.Kind="GroceryStore", Publish="GroceryStore.Publish"]
shared GroceryStore.Contents = (url as text) =>
    let
        source = Json.Document(Web.Contents(url)),
        data = source[data],
        table = Table.FromRecords(data)
    in
        table;
```

---

This guide provides multiple methods to connect your Django APIs to Power BI, from simple web connections to advanced streaming datasets and custom connectors.