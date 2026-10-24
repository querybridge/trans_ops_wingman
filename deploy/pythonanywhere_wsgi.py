# Paste into the PythonAnywhere WSGI configuration file
# (Web tab -> "WSGI configuration file"), replacing everything in it.
# Replace YOUR_USERNAME with your PythonAnywhere username.

import os
import sys

PROJECT_DIR = "/home/querybridge/yzer_demo"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# config/settings.py loads PROJECT_DIR/.env itself, so no secrets belong in this file.
from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
