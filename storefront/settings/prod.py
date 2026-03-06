from .common import *
import os
import dj_database_url

DEBUG = False
SILKY_MAX_RECORDED_REQUESTS = 10**3  # Limit to 1,000 requests
SILKY_MAX_RECORDED_REQUESTS_CHECK_PERCENT = 10

SECRET_KEY = os.environ['SECRET_KEY']

ASSEMBLY_AI_API_KEY = os.environ['ASSEMBLY_AI_API_KEY']

GEMINI_API_KEY = os.environ['GEMINI_API_KEY']

ALLOWED_HOSTS = ['hermes-prod-c391af873af7.herokuapp.com']

DATABASES = {
    'default': dj_database_url.config()
}

REDISCLOUD_URL = os.environ['REDISCLOUD_URL']

CELERY_BROKER_URL = REDISCLOUD_URL

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDISCLOUD_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

EMAIL_HOST = os.environ['MAILGUN_SMTP_SERVER']
EMAIL_HOST_USER = os.environ['MAILGUN_SMTP_LOGIN']
EMAIL_HOST_PASSWORD = os.environ['MAILGUN_SMTP_PASSWORD']
EMAIL_PORT = os.environ['MAILGUN_SMTP_PORT']