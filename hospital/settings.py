import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv

# --------------------------------------------------
# 1. BASE DIRECTORY & ENV LOADING
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Loading .env with a specific path to avoid parse warnings
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# --------------------------------------------------
# 2. SECURITY
# --------------------------------------------------
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Allow local dev and the Railway production domain
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.railway.app']

# Fixed CSRF for Railway production
CSRF_TRUSTED_ORIGINS = [
    'https://hospital.up.railway.app',
    'https://*.railway.app',
]

# --------------------------------------------------
# 3. APPLICATIONS (Fixed allauth registration)
# --------------------------------------------------
INSTALLED_APPS = [
    'accounts', # Your custom user app
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

# --------------------------------------------------
# 4. MIDDLEWARE
# --------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # 2nd place for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'hospital.urls'

# --------------------------------------------------
# 5. TEMPLATES (Fixed admin.E403)
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
# 6. DATABASE (Auto-detect PostgreSQL vs SQLite)
# --------------------------------------------------
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
    )
}

# --------------------------------------------------
# 7. STATIC & MEDIA / AWS S3
# --------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

if not DEBUG:
    # AWS S3 for Media, WhiteNoise for Static
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# --------------------------------------------------
# 8. AUTHENTICATION & MISC
# --------------------------------------------------
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