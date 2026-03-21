web: cd grocerystore && python manage.py migrate --noinput && gunicorn grocerystore.wsgi:application --bind 0.0.0.0:${PORT:-8000} --timeout 120 --workers 1
