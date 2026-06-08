import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-q27bpsxxo#5r^6mf2f*nri!6(j+8r0=)wnfyhut7@gs=&ldq5d",
)
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "rest_framework",
    "drf_spectacular",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "autoponto.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "autoponto.wsgi.application"

database_engine = os.getenv("DATABASE_ENGINE", "django.db.backends.sqlite3")
database_name = os.getenv("DATABASE_NAME", "db.sqlite3")

DATABASES = {
    "default": {
        "ENGINE": database_engine,
        "NAME": str(BASE_DIR / database_name) if database_engine == "django.db.backends.sqlite3" else database_name,
        "USER": os.getenv("DATABASE_USER", ""),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", ""),
        "HOST": os.getenv("DATABASE_HOST", ""),
        "PORT": os.getenv("DATABASE_PORT", ""),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = os.getenv("TIME_ZONE", "America/Sao_Paulo")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "api.Usuario"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "api.authentication.EdgeNodeTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_DAYS", "1"))),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "AutoPonto API",
    "DESCRIPTION": "API de automação de frequência acadêmica para o TCC AutoPonto.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

EDGE_SYNC_DAYS_BACK = int(os.getenv("EDGE_SYNC_DAYS_BACK", "1"))
EDGE_SYNC_DAYS_FORWARD = int(os.getenv("EDGE_SYNC_DAYS_FORWARD", "7"))

INTERSCITY_ENABLED = os.getenv("INTERSCITY_ENABLED", "False").lower() == "true"
INTERSCITY_CATALOG_URL = os.getenv("INTERSCITY_CATALOG_URL", "").rstrip("/")
INTERSCITY_ADAPTOR_URL = os.getenv("INTERSCITY_ADAPTOR_URL", "").rstrip("/")
INTERSCITY_COLLECTOR_URL = os.getenv("INTERSCITY_COLLECTOR_URL", "").rstrip("/")
INTERSCITY_DISCOVERY_URL = os.getenv("INTERSCITY_DISCOVERY_URL", "").rstrip("/")
INTERSCITY_ACTUATOR_URL = os.getenv("INTERSCITY_ACTUATOR_URL", "").rstrip("/")
INTERSCITY_TIMEOUT_SECONDS = int(os.getenv("INTERSCITY_TIMEOUT_SECONDS", "5"))

FACE_DETECT_MODEL_PATH = os.getenv("FACE_DETECT_MODEL_PATH", "")
FACE_RECOG_MODEL_PATH = os.getenv("FACE_RECOG_MODEL_PATH", "")
FACE_SCORE_THRESHOLD = float(os.getenv("FACE_SCORE_THRESHOLD", "0.85"))
