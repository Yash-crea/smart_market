# Power BI Dashboard Integration Guide
## Enhanced Owner & Customer Analytics

This guide explains how to connect your Django grocery store application's dashboard data to Power BI for enhanced business intelligence and analytics.

## 🎯 Overview

We've created specialized API endpoints that transform your existing Django dashboard views into Power BI-ready data sources. These endpoints provide comprehensive analytics for both owner and customer dashboards with optimized data structures for visualization.

## 📊 Available Dashboard Endpoints

### 1. Owner Dashboard Analytics
**Endpoint:** `/api/v1/powerbi/owner-dashboard/`
**Method:** GET
**Authentication:** Required (Owner role)

#### Data Provided:
- **Inventory Metrics**: Product counts, stock levels, inventory values
- **User Analytics**: User counts by role, activity rates
- **Order Performance**: Revenue, conversion rates, order statuses
- **Time Series Data**: Daily order trends (30 days)
- **Top Products**: Best-selling items with quantity and revenue
- **Operational Alerts**: Low stock warnings, unread notifications

#### Sample Response Structure:
```json
{
    "inventory_metrics": {
        "total_products": 150,
        "combined_inventory_value": 25000.50,
        "low_stock_alerts": 12,
        "regular_products": {
            "total_count": 100,
            "in_stock": 95,
            "stock_percentage": 95.0
        }
    },
    "order_metrics": {
        "total_orders": 1250,
        "total_revenue": 45000.75,
        "completion_rate": 87.5,
        "conversion_rate": 15.2
    },
    "daily_orders_30d": [
        {"date": "2024-01-15", "orders_count": 25},
        {"date": "2024-01-14", "orders_count": 32}
    ]
}
```

### 2. Customer Dashboard Analytics
**Endpoint:** `/api/v1/powerbi/customer-dashboard/`
**Method:** GET
**Authentication:** Required (Customer role)

#### Data Provided:
- **Personal Profile**: User information, membership details
- **Purchase History**: Order analytics, spending patterns
- **Cart Analytics**: Current cart value and items
- **Loyalty Metrics**: Status, points, next tier thresholds
- **Product Recommendations**: Personalized suggestions
- **Spending Trends**: 12-month spending analysis

#### Sample Response Structure:
```json
{
    "user_profile": {
        "user_id": 123,
        "full_name": "John Doe",
        "member_since": "2023-06-15T10:30:00Z"
    },
    "order_analytics": {
        "total_orders": 15,
        "total_spent": 1250.75,
        "average_order_value": 83.38,
        "completion_rate": 93.3
    },
    "loyalty_metrics": {
        "status": "Premium",
        "points_earned": 150,
        "next_tier_threshold": 250
    }
}
```

## 🔗 Power BI Connection Setup

### Step 1: API Authentication
Use token-based authentication for Power BI connections:

```python
# Get authentication token
POST /api/v1/auth/login/
{
    "username": "your_username",
    "password": "your_password"
}

# Response includes token for authorization
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
    "user_id": 123,
    "role": "Owner"
}
```

### Step 2: Power BI Data Source Configuration

#### For Owner Dashboard:
1. **Open Power BI Desktop**
2. **Get Data → Web**
3. **URL:** `http://your-domain.com/api/v1/powerbi/owner-dashboard/`
4. **Advanced Options:**
   - **HTTP request header parameters:**
     ```
     Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
     Content-Type: application/json
     ```

#### For Customer Dashboard:
1. **Get Data → Web**
2. **URL:** `http://your-domain.com/api/v1/powerbi/customer-dashboard/`
3. **Use same authentication headers**

### Step 3: Power Query M Language Setup
```m
let
    url = "http://your-domain.com/api/v1/powerbi/owner-dashboard/",
    headers = [
        Authorization = "Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
        #"Content-Type" = "application/json"
    ],
    source = Json.Document(Web.Contents(url, [Headers = headers])),
    
    // Extract inventory metrics
    inventory = source[inventory_metrics],
    inventoryTable = Record.ToTable(inventory),
    
    // Extract order metrics
    orders = source[order_metrics],
    ordersTable = Record.ToTable(orders),
    
    // Extract daily orders time series
    dailyOrders = Table.FromList(
        source[daily_orders_30d], 
        Splitter.SplitByNothing(), 
        null, 
        null, 
        ExtraValues.Error
    )
in
    dailyOrders
```

## 📈 Power BI Visualization Recommendations

### Owner Dashboard Visuals:

#### 1. **Inventory Health Card**
- **Visual Type:** Card
- **Metric:** `inventory_metrics.combined_inventory_value`
- **Format:** Currency
- **Conditional Formatting:** Green if > $20,000

#### 2. **Stock Level Gauge**
- **Visual Type:** Gauge
- **Metric:** `inventory_metrics.regular_products.stock_percentage`
- **Target:** 95%
- **Color Coding:** Red < 80%, Yellow 80-90%, Green > 90%

#### 3. **Daily Orders Trend**
- **Visual Type:** Line Chart
- **X-Axis:** `daily_orders_30d.date`
- **Y-Axis:** `daily_orders_30d.orders_count`
- **Trend Line:** Enabled

#### 4. **Top Products Matrix**
- **Visual Type:** Table/Matrix
- **Rows:** `top_products.product_name`
- **Values:** `top_products.total_quantity`, `top_products.total_revenue`

#### 5. **Order Status Donut Chart**
- **Visual Type:** Donut Chart
- **Legend:** Order Status (Pending, Completed, Cancelled)
- **Values:** Respective counts from `order_metrics`

### Customer Dashboard Visuals:

#### 1. **Loyalty Status Card**
- **Visual Type:** Card
- **Metric:** `loyalty_metrics.status`
- **Conditional Formatting:** Premium = Gold, Standard = Silver

#### 2. **Spending Pattern Line Chart**
- **Visual Type:** Line Chart
- **X-Axis:** `spending_patterns.monthly_spending_12m.month`
- **Y-Axis:** `spending_patterns.monthly_spending_12m.total_spent`

#### 3. **Favorite Products Bar Chart**
- **Visual Type:** Horizontal Bar Chart
- **Y-Axis:** `spending_patterns.favorite_products.product_name`
- **X-Axis:** `spending_patterns.favorite_products.times_purchased`

## 🔄 Data Refresh Configuration

### Automatic Refresh Setup:
1. **Publish to Power BI Service**
2. **Go to Dataset Settings**
3. **Configure Scheduled Refresh:**
   - **Frequency:** Daily at 6 AM
   - **Time Zone:** Your local timezone
   - **Credentials:** Use the API token from Django

### Real-time Updates:
For near real-time data, set refresh frequency to every 30 minutes during business hours.

## 🛡️ Security Considerations

### 1. **Token Management**
- Tokens don't expire automatically in this implementation
- Consider implementing token refresh for production
- Store tokens securely in Power BI credentials manager

### 2. **Access Control**
- Owner dashboard requires Owner role authentication
- Customer dashboard restricts access to customer data only
- Failed authentication returns 403 Forbidden

### 3. **CORS Configuration**
Add Power BI domains to CORS settings in Django:
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "https://app.powerbi.com",
    "https://msit.powerbi.com",
]
```

## 📊 Advanced Analytics Setup

### Customer Segmentation Analysis:
Create calculated columns in Power BI:

```dax
Customer Tier = 
IF(
    [order_analytics.total_orders] > 10,
    "Premium Customer",
    IF(
        [order_analytics.total_orders] > 5,
        "Regular Customer",
        "New Customer"
    )
)

Purchase Frequency = 
IF(
    [loyalty_metrics.member_since_days] > 0,
    [order_analytics.total_orders] / ([loyalty_metrics.member_since_days] / 30),
    0
)
```

### Inventory Optimization Metrics:
```dax
Stock Risk Level = 
SWITCH(
    TRUE(),
    [inventory_metrics.regular_products.stock_percentage] < 70, "High Risk",
    [inventory_metrics.regular_products.stock_percentage] < 85, "Medium Risk",
    "Low Risk"
)

Inventory Turnover = [order_metrics.total_revenue] / [inventory_metrics.combined_inventory_value]
```

## 🚀 Deployment Checklist

### Pre-Production:
- [ ] Test API endpoints with sample data
- [ ] Verify authentication tokens work correctly
- [ ] Check data refresh rates and performance
- [ ] Validate all metrics calculations
- [ ] Test Power BI report sharing permissions

### Production:
- [ ] Configure production API URLs
- [ ] Set up secure token storage
- [ ] Enable scheduled refresh
- [ ] Monitor API rate limits
- [ ] Set up alerting for failed refreshes

## 🔍 Troubleshooting

### Common Issues:

#### 1. **Authentication Failures**
```
Error: 401 Unauthorized
Solution: Verify token is included in Authorization header
Format: "Authorization: Token your_token_here"
```

#### 2. **Empty Data Response**
```
Error: No data returned
Solution: Check user permissions and role assignments
Owner endpoint requires Owner role
Customer endpoint requires Customer role
```

#### 3. **Slow Data Loading**
```
Issue: Power BI refresh takes too long
Solution: Implement pagination or data filtering
Add query parameters for date ranges
```

### Debugging Steps:
1. Test endpoints directly with Postman/cURL
2. Check Django logs for API errors
3. Verify database contains expected data
4. Validate Power BI Query syntax

## 📞 Support

For technical support:
- Check Django application logs
- Verify API endpoint responses
- Test authentication independently
- Review Power BI error messages

## 🎯 Next Steps

1. **Enhanced Metrics**: Add more KPIs based on business needs
2. **Real-time Streaming**: Implement SignalR for live updates
3. **Mobile Dashboards**: Create mobile-optimized Power BI reports
4. **Predictive Analytics**: Integrate ML forecasts into dashboards
5. **Automated Alerts**: Set up Power BI alerts for critical metrics

---

Your Django grocery store dashboards are now Power BI ready! 🚀📊