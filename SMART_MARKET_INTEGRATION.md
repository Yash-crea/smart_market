# Smart Market Database Integration Guide

## Step 1: Update Database Credentials

Edit `grocerystore/settings.py` and update the DATABASES section with your MySQL credentials:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'smart_market',
        'USER': 'your_mysql_username',     # Replace with your actual username
        'PASSWORD': 'your_mysql_password', # Replace with your actual password
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}
```

## Step 2: Test the Connection

Run the test script to verify your database connection:

```bash
cd grocerystore
python test_mysql_connection.py
```

## Step 3: Generate Django Models

Once the connection works, generate models from your existing tables:

```bash
python manage.py inspectdb > smart_market_models.py
```

## Step 4: Integrate the Models

1. Review the generated `smart_market_models.py` file
2. Copy relevant models to `marche_smart/models.py`
3. Remove `managed = False` from model Meta classes if you want Django to manage them
4. Run `python manage.py makemigrations`
5. Run `python manage.py migrate --fake-initial`

## Step 5: Update Admin (Optional)

Register your new models in `marche_smart/admin.py` to manage them through Django admin.

## Troubleshooting

- **Access Denied Error**: Update USERNAME and PASSWORD in settings.py
- **Database Not Found**: Ensure 'smart_market' database exists in MySQL
- **Connection Refused**: Make sure MySQL server is running
- **Port Issues**: Verify MySQL is running on port 3306