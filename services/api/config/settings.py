"""
Django settings for AURA365 Backend API.

Este archivo configura Django para trabajar con la base de datos de Supabase
y exponer una API REST completa usando Django REST Framework.
"""

from pathlib import Path

from celery.schedules import crontab
from decouple import config, Csv
from kombu import Queue

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())


# ==============================================================================
# APPLICATION DEFINITION
# ==============================================================================

INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'django_filters',
    'corsheaders',
    'drf_spectacular',

    # Local apps
    'users.apps.UsersConfig',
    'body.apps.BodyConfig',
    'holistic.apps.HolisticConfig',
    'papers.apps.PapersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS debe ir antes de CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================
# Configurado para conectar con PostgreSQL (Supabase)
#
# Puertos:
# - 54322: Supabase local (desarrollo)
# - 6543: Supabase Cloud Pooler (producción - RECOMENDADO)
# - 5432: Supabase Cloud directo (no recomendado, sin pooling)

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='postgres'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='54322'),
        # Connection pooling: 0 para dev/testing, 600 para producción
        # Railway/producción: configurar CONN_MAX_AGE=600 en env vars
        'CONN_MAX_AGE': int(config('CONN_MAX_AGE', default=0)),
        'OPTIONS': {
            # Opciones para PostgreSQL
            'options': '-c search_path=public,auth',
            'connect_timeout': 10,
        },
        'ATOMIC_REQUESTS': False,
        'TEST': {
            'NAME': 'test_postgres',
            'CHARSET': 'UTF8',
        }
    }
}


# ==============================================================================
# VECTOR DATABASE CONFIGURATION
# ==============================================================================
# Endpoint base del microservicio vectorial (proxy hacia Qdrant).
# Mantén este valor sincronizado con tu despliegue en OrbStack/producción.

VECTOR_DB_BASE_URL = config('VECTOR_DB_BASE_URL', default='http://localhost:8001').rstrip('/')


# ==============================================================================
# NUTRITION PLAN INGESTION SETTINGS
# ==============================================================================

# Nuevo microservicio de extracción de PDFs con Gemini
_DEFAULT_NUTRITION_INGEST_URL = "http://localhost:8002/ingest"
NUTRITION_PLAN_INGESTION_URL = config('NUTRITION_PLAN_INGESTION_URL', default=_DEFAULT_NUTRITION_INGEST_URL)
NUTRITION_PLAN_INGESTION_TOKEN = config('NUTRITION_PLAN_INGESTION_TOKEN', default=None)
NUTRITION_PLAN_INGESTION_TIMEOUT = config('NUTRITION_PLAN_INGESTION_TIMEOUT', default=120, cast=int)  # Increased for Gemini

NUTRITION_PLAN_CALLBACK_URL = config('NUTRITION_PLAN_CALLBACK_URL', default=None)
NUTRITION_PLAN_CALLBACK_TOKEN = config('NUTRITION_PLAN_CALLBACK_TOKEN', default='dev-callback-secret-token')

NUTRITION_PLAN_STORAGE_BUCKET = config('NUTRITION_PLAN_STORAGE_BUCKET', default=None)
NUTRITION_PLAN_STORAGE_PREFIX = config('NUTRITION_PLAN_STORAGE_PREFIX', default='nutrition-plans')
NUTRITION_PLAN_STORAGE_PUBLIC_URL = config('NUTRITION_PLAN_STORAGE_PUBLIC_URL', default=None)
NUTRITION_PLAN_STORAGE_TIMEOUT = config('NUTRITION_PLAN_STORAGE_TIMEOUT', default=15, cast=int)

NUTRITION_PLAN_MAX_UPLOAD_MB = config('NUTRITION_PLAN_MAX_UPLOAD_MB', default=10, cast=int)
NUTRITION_PLAN_ALLOWED_FILE_TYPES = config('NUTRITION_PLAN_ALLOWED_FILE_TYPES', default='application/pdf', cast=Csv())

# ==============================================================================
# HOLISTIC REPORT SERVICE
# ==============================================================================
HOLISTIC_REPORT_SERVICE_URL = config('HOLISTIC_REPORT_SERVICE_URL', default=None)
HOLISTIC_REPORT_SERVICE_TOKEN = config('HOLISTIC_REPORT_SERVICE_TOKEN', default=None)
HOLISTIC_REPORT_SERVICE_TIMEOUT = config('HOLISTIC_REPORT_SERVICE_TIMEOUT', default=45, cast=int)

# ==============================================================================
# SUPABASE ADMIN API CONFIGURATION
# ==============================================================================

SUPABASE_API_URL = config('SUPABASE_API_URL', default='http://127.0.0.1:54321')
SUPABASE_SERVICE_ROLE_KEY = config('SUPABASE_SERVICE_ROLE_KEY', default=None)
SUPABASE_ADMIN_TIMEOUT = config('SUPABASE_ADMIN_TIMEOUT', default=10, cast=int)


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = 'es-mx'  # Configurado para español mexicano

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True

USE_TZ = True  # Siempre usar timestamps con zona horaria


# ==============================================================================
# STATIC FILES
# ==============================================================================

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ==============================================================================
# DEFAULT SETTINGS
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================================================================
# DJANGO REST FRAMEWORK CONFIGURATION
# ==============================================================================

REST_FRAMEWORK = {
    # Renderizadores por defecto
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    
    # Parser por defecto
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    
    # Autenticación (por ahora básica, se puede expandir con JWT)
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.SupabaseJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    
    # Permisos por defecto
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    
    # Paginación
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    
    # Filtros
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    
    # Schema para documentación automática
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    # Formato de fecha/hora
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S.%fZ',
    'DATE_FORMAT': '%Y-%m-%d',
    'TIME_FORMAT': '%H:%M:%S',
}


# ==============================================================================
# DRF-SPECTACULAR SETTINGS (OpenAPI/Swagger)
# ==============================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'AURA365 Backend API',
    'DESCRIPTION': 'API REST para AURA365 - Sistema de gestión de usuarios y servicios',
    'VERSION': config('API_VERSION', default='v1'),
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
}


# CORS CONFIGURATION
CORS_ALLOW_ALL_ORIGINS = True  # DEBUG: Permitir todo
CORS_ALLOW_CREDENTIALS = True
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + [
    'authorization',
    'x-csrftoken',
    'x-requested-with',
]

# ==============================================================================
# HOLISTIC SERVICE SETTINGS
# ==============================================================================
HOLISTIC_AGENT_SERVICE_URL = config(
    'HOLISTIC_AGENT_SERVICE_URL',
    default='http://localhost:8100/api/holistic/v1/run',
)
HOLISTIC_AGENT_SERVICE_TOKEN = config('HOLISTIC_AGENT_SERVICE_TOKEN', default=None)
HOLISTIC_AGENT_REQUEST_TIMEOUT = config('HOLISTIC_AGENT_REQUEST_TIMEOUT', default=120, cast=int)
HOLISTIC_AGENT_RETRY_DELAY = config('HOLISTIC_AGENT_RETRY_DELAY', default=2, cast=int)


# ==============================================================================
# CELERY CONFIGURATION
# ==============================================================================

CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_TIME_LIMIT = config('CELERY_TASK_TIME_LIMIT', default=600, cast=int)
CELERY_TASK_SOFT_TIME_LIMIT = config('CELERY_TASK_SOFT_TIME_LIMIT', default=540, cast=int)
CELERY_TASK_DEFAULT_QUEUE = config('CELERY_TASK_DEFAULT_QUEUE', default='api_default')
CELERY_TASK_QUEUES = (
    Queue('api_default', routing_key='api_default'),
    Queue('holistic_snapshots', routing_key='holistic.snapshots'),
)

CELERY_TASK_ROUTES = {
    'holistic.generate_user_context_snapshots_periodic': {'queue': 'holistic_snapshots'},
    'holistic.generate_user_context_snapshot_for_user': {'queue': 'holistic_snapshots'},
    'holistic.vectorize_pending_snapshots': {'queue': 'holistic_snapshots'},
}

CELERY_BEAT_SCHEDULE = {
    'holistic-generate-user-context-snapshots-daily': {
        'task': 'holistic.generate_user_context_snapshots_periodic',
        'schedule': crontab(hour=3, minute=0),  # Ejecuta diario 03:00 UTC
        'options': {
            'queue': 'holistic_snapshots',
        },
    },
}

CELERY_IMPORTS = (
    'holistic.tasks',
)


# ==============================================================================
# AWS S3 CONFIGURATION
# ==============================================================================
# Configuración para almacenamiento de artículos científicos en AWS S3

AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default=None)
AWS_S3_REGION = config('AWS_S3_REGION', default='us-east-1')
AWS_S3_BUCKET_NAME = config('AWS_S3_BUCKET_NAME', default='aura360-clinical-papers')

# URL presignada expira en 15 minutos por defecto
AWS_S3_PRESIGNED_URL_EXPIRATION = config('AWS_S3_PRESIGNED_URL_EXPIRATION', default=900, cast=int)
