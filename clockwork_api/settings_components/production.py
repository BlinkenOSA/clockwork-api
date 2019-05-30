import os
from clockwork_api.settings import BASE_DIR

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
DEBUG = False
ALLOWED_HOSTS = []

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'public')

MEDIA_URL = '/media/'

CORS_ORIGIN_ALLOW_ALL = True

USE_TZ = False
