# FILE: access_control/settings.py

from pathlib import Path
import os
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --- CORE SETTINGS (from .env file) ---
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=Csv())

# --- INSTALLED APPS ---
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_apscheduler',
    'crispy_forms',
    'crispy_tailwind',
    'users',
    'sites',
    'logs',
    'dashboard',
    'configuration'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'access_control.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
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

WSGI_APPLICATION = 'access_control.wsgi.application'

# --- DATABASE (from .env file) ---
DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL'))
}

# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# --- STATIC & MEDIA FILES ---
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# --- CUSTOM APP SETTINGS ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUser'
LOGIN_URL = '/users/login/'
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# --- SERVICE KEYS (from .env file) ---
FACE_SERVICE_URL = 'http://127.0.0.1:8001'
FACE_API_KEY = config('FACE_API_KEY')

# --- AUTOMATIC LOGOUT CONFIGURATION ---
SESSION_COOKIE_AGE = 900  # 15 minutes
SESSION_SAVE_EVERY_REQUEST = True

# --- EMAIL CONFIGURATION (from .env file) ---
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = config('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'sent_emails' 
DEFAULT_FROM_EMAIL = 'noreply@serveraccess.com'


# --- JAZZMIN ADMIN PANEL SETTINGS ---
JAZZMIN_SETTINGS = {
    "site_title": "Access Control Admin", "site_header": "Access Control", "site_brand": "Admin Panel",
    "site_logo": "https://upload.wikimedia.org/wikipedia/commons/9/97/Logo_PLN.png",
    "welcome_sign": "Welcome to the Access Control Admin Panel", "copyright": "Danantara Indonesia (PLN Group)",
    "topmenu_links": [{"name": "Home", "url": "admin:index"}, {"name": "View Site", "url": "/", "new_window": True}],
    "order_with_respect_to": ["users", "sites", "logs", "auth"],
    "icons": {
        "auth": "fas fa-users-cog", "users.CustomUser": "fas fa-user", "users.FaceChangeRequest": "fas fa-camera-rotate",
        "sites.ServerLocation": "fas fa-server", "logs.ServerRoomAccessLog": "fas fa-clipboard-list",
        "logs.ActivityCategory": "fas fa-tags", "logs.ActivitySubCategory": "fas fa-tag",
    },
    "theme": "litera", "dark_mode_theme": None,
}