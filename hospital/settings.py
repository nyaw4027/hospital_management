import os
from pathlib import Path
from dotenv import load_dotenv

# 1. BASE DIRECTORY & ENV LOADING
BASE_DIR = Path(__file__).resolve().parent.parent

# Load local .env file if it exists
load_dotenv(BASE_DIR / ".env")

# 2. SECURITY
# For local use, we provide a fallback string if SECRET_KEY isn't in .env
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-development-key')

# CRITICAL: Set to True to see EXACT errors instead of "Server Error (500)"
DEBUG = True

# Empty list allows 'localhost' and '127.0.0.1' automatically when DEBUG is True
ALLOWED_HOSTS = []

# 3. APPLICATIONS
INSTALLED_APPS = [
    'accounts', 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third-party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    #'allauth.socialaccount.providers.google',
    'django_extensions',
    'storages',
    'crispy_forms',
    'crispy_bootstrap5',

    # Hospital system apps
    'patients',
    'doctors',
    'cashier',
    'manager',
    'labs.apps.LabsConfig',
    'nurses',
    'appointments',
    'pharmacy',
    'inpatient',
]

# 4. MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'hospital.urls'

# 5. TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'manager.context_processors.hospital_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'hospital.wsgi.application'

# 6. DATABASE (Switched to Local SQLite)
# This removes the "Connection Refused" error because it doesn't need a Postgres server
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 7. STATIC & MEDIA (Local File System)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Local storage only (removes AWS S3 dependency)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 8. AUTHENTICATION & MISC
AUTH_USER_MODEL = 'accounts.User'
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"