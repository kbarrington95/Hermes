release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn storefront.wsgi
worker: celery -A storefront worker --loglevel=info --concurrency=1 --max-tasks-per-child=10

