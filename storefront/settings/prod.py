from .common import *
import os
import dj_database_url

DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = ['hermes-prod-c391af873af7.herokuapp.com']

DATABASES = {
    'default': dj_database_url.config()
}