from pathlib import Path
import os

# --------------------------------------------------
# BASE DIRECTORY
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------
# SECURITY
# --------------------------------------------------
SECRET_KEY = 'django-insecure-hms-core-secure-key'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# --------------------------------------------------
# APPLICATIONS
# --------------------------------------------------
INSTALLED_APPS = [
    'accounts', # Custom user app first
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
    'allauth.socialaccount.providers.google',
    'django_extensions',

    # Hospital system apps
    'patients',
    'doctors',
    'cashier',
    'manager',
    'labs.apps.LabsConfig',
    'nurses',
    'appointments',
    'pharmacy',
]

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'manager.middleware.MaintenanceModeMiddleware',
]

ROOT_URLCONF = 'hospital.urls'

# --------------------------------------------------
# TEMPLATES
# --------------------------------------------------
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

# --------------------------------------------------
# DATABASE
# --------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --------------------------------------------------
# AUTHENTICATION CONFIGURATION
# --------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Simple login/logout URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

# --- ALLAUTH 65.0+ FIXES (Removes Warnings) ---
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
# This replaces ACCOUNT_EMAIL_REQUIRED and ACCOUNT_USERNAME_REQUIRED
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none' 
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
ACCOUNT_LOGOUT_REDIRECT_URL = 'home'

ACCOUNT_LOGOUT_ON_GET = True


# --------------------------------------------------
# STATIC & MEDIA
# --------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------
# EMAIL CONFIGURATION
# --------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'nyaw4027@gmail.com'
# Use your 16-character Google App Password here
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your-actual-app-password')
DEFAULT_FROM_EMAIL = 'HMS Core Support <nyaw4027@gmail.com>'