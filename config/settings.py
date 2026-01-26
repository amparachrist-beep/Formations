import os
from pathlib import Path
from decouple import config
import dj_database_url

# ==================== CONFIGURATION DE BASE ====================

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Hosts autorisés (Render fournit un domaine .onrender.com)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')
if 'RENDER_EXTERNAL_HOSTNAME' in os.environ:
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])

# ==================== APPLICATIONS ====================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps personnalisées
    'formation',

    # Apps tierces (optionnel)
    'whitenoise.runserver_nostatic',  # Pour mieux gérer les static files en dev
]

# ==================== MIDDLEWARE ====================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # IMPORTANT: doit être après SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==================== URLS ET WSGI ====================

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'

# ==================== TEMPLATES ====================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Si vous avez un dossier templates global
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'formation.context_processors.panier_count',
            ],
        },
    },
]

# ==================== BASE DE DONNÉES ====================

# Configuration de la base de données pour Render (PostgreSQL)
if 'DATABASE_URL' in os.environ:
    # PostgreSQL sur Render
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,  # Render nécessite SSL
        )
    }
elif not DEBUG:
    # En production sans DATABASE_URL explicite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='formations_db'),
            'USER': config('DB_USER', default='formations_user'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    # SQLite en développement local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ==================== VALIDATION DES MOTS DE PASSE ====================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==================== INTERNATIONALISATION ====================

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Brazzaville'
USE_I18N = True
USE_TZ = True

# ==================== FICHIERS STATIQUES ET MÉDIA ====================

# URL pour les fichiers statiques
STATIC_URL = '/static/'

# Emplacement où collecter les fichiers statiques pour la production
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Dossiers supplémentaires pour les fichiers statiques
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # Si vous avez un dossier static global
]

# Configuration de WhiteNoise pour les fichiers statiques
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuration pour les fichiers média
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Clé primaire par défaut
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== CONFIGURATION MONEROO ====================

MONEROO_API_KEY = config('MONEROO_API_KEY', default='')
MONEROO_MERCHANT_ID = config('MONEROO_MERCHANT_ID', default='')
MONEROO_API_URL = 'https://api.moneroo.io/v1/payments/initialize'

# ==================== CONFIGURATION WHATSAPP ====================

ADMIN_WHATSAPP = config('ADMIN_WHATSAPP', default='+242061814279')
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# ==================== SESSIONS ====================

SESSION_COOKIE_AGE = 86400  # 24 heures
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS uniquement en production
CSRF_COOKIE_SECURE = not DEBUG  # HTTPS uniquement en production

# ==================== CONFIGURATION EMAIL ====================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('EMAIL_FROM', default=EMAIL_HOST_USER)

# ==================== SÉCURITÉ PRODUCTION ====================

if not DEBUG:
    # Force HTTPS
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Cookies sécurisés
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Protection XSS
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # Clickjacking protection
    X_FRAME_OPTIONS = 'DENY'

    # HTTP Strict Transport Security
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Referrer Policy
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ==================== LOGGING ====================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# ==================== CONFIGURATIONS SPÉCIFIQUES RENDER ====================

# Configuration pour la limitation de mémoire sur Render (plan gratuit)
if 'RENDER' in os.environ:
    # Optimisation pour le plan gratuit
    import sys

    # Optimisation de la mémoire
    DATABASES['default']['CONN_MAX_AGE'] = 300  # 5 minutes

    # Configuration Gunicorn optimisée pour Render
    os.environ.setdefault('WEB_CONCURRENCY', '2')
    os.environ.setdefault('PYTHONWARNINGS', 'ignore')

# ==================== TESTS CONFIGURATION ====================

# Configuration pour les tests
TEST_RUNNER = 'django.test.runner.DiscoverRunner'