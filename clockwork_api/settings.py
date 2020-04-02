from split_settings.tools import optional, include

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

include(
    'settings_components/application.py',
    'settings_components/database.py',
    'settings_components/rest_framework.py',
    'settings_components/production.py',
    optional('settings_components/local.py')
)