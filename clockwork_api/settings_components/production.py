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

DATE_EXTENSIONS_OUTPUT_FORMAT_DAY_MONTH_YEAR = "Y-m-d"
DATE_EXTENSIONS_OUTPUT_FORMAT_MONTH_YEAR = "Y-m"
DATE_EXTENSIONS_OUTPUT_FORMAT_YEAR = "Y"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer'
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10,
}