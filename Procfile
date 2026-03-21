web: cd grocerystore && python manage.py migrate --noinput && gunicorn grocerystore.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --workers 1
