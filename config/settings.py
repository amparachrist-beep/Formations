import os
from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== CONFIGURATION DE BASE ====================
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# Hosts autorisés
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

if 'RENDER_EXTERNAL_HOSTNAME' in os.environ:
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])

# ==================== CLOUDINARY CONFIGURATION ====================
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default='djudlfwcr'),
    'API_KEY': config('CLOUDINARY_API_KEY', default='695364454293442'),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}

# Utiliser l'URL Cloudinary complète si disponible
CLOUDINARY_URL = config('CLOUDINARY_URL', default='')
if CLOUDINARY_URL:
    os.environ['CLOUDINARY_URL'] = CLOUDINARY_URL

# ==================== BASE DE DONNÉES ====================
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.strip():
    # Render PostgreSQL en production
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # SQLite en développement local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ==================== APPLICATIONS ====================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Cloudinary Apps
    'cloudinary_storage',
    'cloudinary',

    # Votre app
    'formation',
]

# ==================== STORAGE CONFIGURATION ====================
# Cloudinary pour les fichiers média (images uploadées)
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# WhiteNoise pour les fichiers statiques (CSS, JS)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = [
    BASE_DIR / "formation" / "static",
]

# Configuration media
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==================== MIDDLEWARE ====================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# ==================== TEMPLATES ====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'formation.context_processors.panier_count',
                'django.template.context_processors.media',
            ],
        },
    },
]

# ==================== PAIEMENT MOBILE MONEY ====================
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Numéros WhatsApp par opérateur
PAIEMENT_OPERATEURS = {
    'airtel': {
        'nom': 'Airtel Money',
        'numero_display': '05 334 40 85',
        'numero_whatsapp': '242053344085',
        'couleur': '#E8192C',
        'emoji': '🔴',
    },
    'mtn': {
        'nom': 'Mobile Money (MTN)',
        'numero_display': '06 181 42 79',
        'numero_whatsapp': '242061814279',
        'couleur': '#FFCC00',
        'emoji': '🟡',
    },
    'orange': {
        'nom': 'Orange Money',
        'numero_display': '+221 78 178 33 02',
        'numero_whatsapp': '221781783302',
        'couleur': '#FF6600',
        'emoji': '🟠',
    },
}

# ==================== EMAIL ====================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER')

# ==================== WHATSAPP ====================
ADMIN_WHATSAPP = config('ADMIN_WHATSAPP', default='+242061814279')

# ==================== SÉCURITÉ PRODUCTION ====================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# ==================== INTERNATIONALISATION ====================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Brazzaville'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== LOGGING ====================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'propagate': True,
        },
        'formation': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ==================== ADMINS (pour notifications d'erreur) ====================
ADMINS = [('Franck NKOU AMPA', 'nkouampafranck49@gmail.com')]

# ==================== SENEPAY ====================
SENEPAY_API_KEY = config('SENEPAY_API_KEY')
SENEPAY_API_SECRET = config('SENEPAY_API_SECRET')

# Note : SITE_URL est déjà défini plus haut dans le fichier (ligne ~90),
# pas besoin de le redéfinir ici — ça écrasait silencieusement la version
# avec le fallback Railway.

# ==================== GOOGLE DRIVE (OAuth) ====================
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET')
GOOGLE_REFRESH_TOKEN = config('GOOGLE_REFRESH_TOKEN')