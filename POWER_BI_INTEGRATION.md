# Power BI Integration Guide

## 🚀 Complete ML-Powered Django API → Power BI Integration

Your Django application now provides **5 specialized Power BI endpoints** that deliver real-time ML forecasts and analytics data in Power BI-optimized JSON format.

## 📊 Power BI Endpoints Overview

### 1. **Demand Forecasting Data**
**URL**: `GET /api/v1/powerbi/demand-forecasts/`

**Power BI Use Case**: Main forecasting dashboard with trend predictions
```
Headers: Authorization: Token your_auth_token
Query Params: 
  ?days_ahead=30&include_confidence=true
```

**Returns**:
- Product demand predictions (7-day & 30-day forecasts)
- Confidence intervals for uncertainty visualization
- Seasonal categories and trends
- Stock reorder recommendations

---

### 2. **Sales Analytics Data**
**URL**: `GET /api/v1/powerbi/sales-analytics/`

**Power BI Use Case**: Revenue dashboards and sales performance tracking
```
Query Params:
  ?days=30&group_by=day
  (group_by options: day, week, month)
```

**Returns**:
- Time-series sales data
- Category performance breakdown
- Top-selling products
- Revenue trends and summary statistics

---

### 3. **Inventory Alerts Data**
**URL**: `GET /api/v1/powerbi/inventory-alerts/`

**Power BI Use Case**: Stock management and reorder alert dashboards
```
Headers: Authorization: Token your_auth_token
```

**Returns**:
- Low stock alerts with priority levels
- Days until stockout predictions
- Suggested reorder quantities
- Inventory optimization recommendations

---

### 4. **ML Model Performance**
**URL**: `GET /api/v1/powerbi/ml-models/performance/`

**Power BI Use Case**: ML model monitoring and accuracy tracking
```
Headers: Authorization: Token your_auth_token
```

**Returns**:
- Model accuracy metrics (MAE, RMSE, R²)
- Recent prediction performance
- Training history and model status

---

### 5. **Generate ML Predictions**
**URL**: `POST /api/v1/powerbi/ml-predictions/generate/`

**Power BI Use Case**: Trigger real-time prediction updates
```
Headers: Authorization: Token your_auth_token
```

**Returns**:
- Success status and prediction count
- Timestamp of updated forecasts

---

## 🔧 Power BI Connection Setup

### Step 1: Get Authentication Token
First, authenticate to get your API token:
```http
POST http://127.0.0.1:8000/api/v1/auth/login/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

Response:
```json
{
    "token": "your_auth_token_here",
    "user_id": 1,
    "username": "your_username"
}
```

### Step 2: Configure Power BI Data Sources

#### Option A: Web Data Source (Recommended)
1. Open Power BI Desktop
2. **Get Data** → **Web**
3. **Advanced** Tab:
   - **URL Parts**: Enter your endpoint URL
   - **HTTP Request Header Parameters**:
     - Name: `Authorization`
     - Value: `Token your_auth_token_here`

Example URLs for Power BI:
```
Demand Forecasts:
http://127.0.0.1:8000/api/v1/powerbi/demand-forecasts/?include_confidence=true

Sales Analytics:
http://127.0.0.1:8000/api/v1/powerbi/sales-analytics/?days=30&group_by=day

Inventory Alerts:
http://127.0.0.1:8000/api/v1/powerbi/inventory-alerts/
```

#### Option B: Python Script in Power BI
```python
import requests
import pandas as pd
import json

# Configuration
base_url = "http://127.0.0.1:8000/api/v1"
headers = {"Authorization": "Token your_auth_token_here"}

# Fetch demand forecasts
response = requests.get(f"{base_url}/powerbi/demand-forecasts/", headers=headers)
data = response.json()

# Convert to DataFrame for Power BI
df = pd.DataFrame(data['forecasts'])
```

---

## 📈 Power BI Dashboard Examples

### 1. **Demand Forecasting Dashboard**
**Data Source**: `/powerbi/demand-forecasts/`

**Recommended Visuals**:
- **Line Chart**: Predicted demand over time
- **Bar Chart**: Products by forecast accuracy
- **Table**: Products needing restock
- **Scatter Plot**: Price vs predicted demand
- **Card**: Total products forecasted

**Key Metrics**:
- `predicted_demand_7d`, `predicted_demand_30d`
- `forecast_accuracy`
- `needs_restock` (boolean flag)

### 2. **Sales Performance Dashboard** 
**Data Source**: `/powerbi/sales-analytics/`

**Recommended Visuals**:
- **Area Chart**: Revenue over time
- **Donut Chart**: Sales by category
- **Table**: Top performing products
- **KPI Card**: Total revenue, order count
- **Trend Line**: Average order value

**Key Metrics**:
- `total_revenue`, `order_count`
- `avg_order_value`
- Category breakdown data

### 3. **Inventory Management Dashboard**
**Data Source**: `/powerbi/inventory-alerts/`

**Recommended Visuals**:
- **Gauge**: Stock levels by product
- **Table**: Priority alerts (high/medium)
- **Bar Chart**: Days until stockout
- **Card**: Total alerts count
- **Heat Map**: Stock levels by category

**Key Metrics**:
- `days_until_stockout`
- `suggested_reorder_qty`
- `priority` levels

---

## 🔄 Setting Up Automatic Data Refresh

### Power BI Service (Online)
1. Publish your dashboard to Power BI Service
2. Go to **Dataset Settings**
3. **Scheduled Refresh**:
   - Set up refresh schedule (hourly/daily)
   - Power BI will automatically call your API endpoints

### Real-time Updates
For real-time dashboards:
1. Use Power BI **Streaming Datasets**
2. Call the ML prediction generation endpoint periodically
3. Push data to Power BI REST API

---

## 🛠 Advanced Integration Features

### Custom Filters and Parameters
Your endpoints support filtering:
```
# Filter by date range
/powerbi/sales-analytics/?days=7&group_by=day

# Include/exclude confidence intervals
/powerbi/demand-forecasts/?include_confidence=false

# Category-specific data (add to your API)
/powerbi/demand-forecasts/?category=Vegetables
```

### Error Handling in Power BI
Your API returns structured error responses:
```json
{
    "success": false,
    "error": "No training data available",
    "message": "Please train ML models first"
}
```

Handle these in Power BI M queries:
```m
let
    Source = Web.Contents("your_api_url"),
    JsonData = Json.Document(Source),
    CheckSuccess = if JsonData[success] = false then 
        error JsonData[message] 
    else 
        JsonData[forecasts]
in
    CheckSuccess
```

---

## 📋 ML Model Training Workflow

### 1. Train Models (One-time setup)
```bash
# Install ML requirements
pip install -r ml_requirements.txt

# Train your ML models
python manage.py train_ml_models --batch-predict
```

### 2. Scheduled Retraining (Production)
Set up a cron job for model retraining:
```bash
# Add to crontab - retrain weekly
0 2 * * 0 cd /path/to/your/project && python manage.py train_ml_models --batch-predict
```

### 3. Power BI Integration Flow
```
1. Django ML Engine generates predictions
2. Data stored in database with timestamps  
3. Power BI calls API endpoints
4. Real-time dashboards display ML forecasts
5. Business decisions made from AI insights
```

## 🎯 Business Value

With this integration, you get:

- **📈 Predictive Analytics**: Real-time demand forecasting
- **📊 Visual Insights**: Professional Power BI dashboards  
- **🔄 Automated Workflows**: ML predictions → API → Power BI
- **💼 Business Intelligence**: Data-driven inventory management
- **⚡ Real-time Updates**: Fresh forecasts for better decisions

Your Django ML API now powers enterprise-grade analytics workflows! 🚀