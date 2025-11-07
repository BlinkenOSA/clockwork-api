import os
from clockwork_api.settings import BASE_DIR

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
DEBUG = False
ALLOWED_HOSTS = []

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'public', 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'public', 'media')

CORS_ORIGIN_WHITELIST = []

USE_TZ = False

DATE_EXTENSIONS_DATE_INPUT_FORMATS = "Y-m-d"
DATE_EXTENSIONS_MONTH_INPUT_FORMATS = "Y-m"
DATE_EXTENSIONS_YEAR_INPUT_FORMATS = "Y"

DATE_EXTENSIONS_OUTPUT_FORMAT_DAY_MONTH_YEAR = "Y-m-d"
DATE_EXTENSIONS_OUTPUT_FORMAT_MONTH_YEAR = "Y-m"
DATE_EXTENSIONS_OUTPUT_FORMAT_YEAR = "Y"

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
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

SIMPLE_JWT = {
   'AUTH_HEADER_TYPES': ('Bearer',),
}

DJOSER = {
    'SERIALIZERS': {
        'current_user': 'accounts.serializers.CurrentUserSerializer',
    },
}

SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Bearer',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False
}

CELERY_BROKER_URL = "redis://localhost:6379"
CELERY_RESULT_BACKEND = "redis://localhost:6379"
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Brussels'