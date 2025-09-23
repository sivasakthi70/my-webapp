import os
import warnings
import base64
import json
from pathlib import Path
from dotenv import load_dotenv

# =======================
# Base Directory
# =======================
BASE_DIR = Path(__file__).resolve().parent.parent

# =======================
# Load Environment Variables
# =======================
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    warnings.warn(f"⚠️ Missing .env file at {dotenv_path} — using default values for development.")

# =======================
# Security
# =======================
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key')
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

# =======================
# API Keys
# =======================
def decode_ors_key(key):
    """If ORS key looks Base64-encoded JSON, decode it to plain key."""
    try:
        decoded = base64.b64decode(key).decode("utf-8")
        data = json.loads(decoded)
        if isinstance(data, dict) and "org" in data:
            return data["org"]
    except Exception:
        pass
    return key

ORS_API_KEY = decode_ors_key(os.getenv('ORS_API_KEY', ''))
AGRO_API_KEY = os.getenv('AGRO_API_KEY')
OPENAQ_API_KEY = os.getenv('OPENAQ_API_KEY')

if not ORS_API_KEY:
    warnings.warn("❌ ORS_API_KEY missing — route planning may not work.")
if not AGRO_API_KEY:
    warnings.warn("⚠️ AGRO_API_KEY missing — crop data features may not work.")
if not OPENAQ_API_KEY:
    warnings.warn("⚠️ OPENAQ_API_KEY missing — air quality features may not work.")

# =======================
# Installed Apps
# =======================
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Custom apps
    'routeplanner',
    'adminpanel',   # ✅ added custom admin panel app

    # UI
    'crispy_forms',
    'crispy_bootstrap5',
]


# =======================
# Middleware
# =======================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =======================
# URL & WSGI
# =======================
ROOT_URLCONF = 'greenroute.urls'
WSGI_APPLICATION = 'greenroute.wsgi.application'

# =======================
# Templates
# =======================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],   # ✅ Project-level templates folder
        'APP_DIRS': True,                   # ✅ Looks inside each app's /templates/
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# =======================
# Database
# =======================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# settings.py
DEFAULT_GREEN_COVER = 50.0

# =======================
# Password Validation
# =======================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =======================
# Internationalization
# =======================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# =======================
# Static & Media
# =======================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =======================
# Authentication Settings
# =======================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'login'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# =======================
# Crispy Forms
# =======================
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# =======================
# Default Auto Field
# =======================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =======================
# Logging
# =======================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}



