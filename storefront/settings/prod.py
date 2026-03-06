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

USE_S3 = os.environ['USE_S3']

if USE_S3:
    INSTALLED_APPS += ['storages']
    
    # NEW FORMAT for Django 4.2+
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": os.environ.get('AWS_ACCESS_KEY_ID'),
                "secret_key": os.environ.get('AWS_SECRET_ACCESS_KEY'),
                "bucket_name": os.environ.get('AWS_STORAGE_BUCKET_NAME'),
                "region_name": "us-east-2", # Match your Ohio bucket
            },
        },
        # ADD THIS SECTION TO FIX THE ERROR
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# 2. AWS Credentials
# AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
# AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
# AWS_S3_REGION_NAME = 'us-east-2'

# 3. Security & URL Settings
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_VERIFY = True

# 4. Tell Django to use S3 for Media Files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# 5. Optional: Use S3 for Static Files too (CSS/JS)
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'