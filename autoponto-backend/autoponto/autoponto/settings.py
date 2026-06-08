import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent.parent


def carregar_env_raiz() -> None:
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return

    for linha in env_path.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave:
            os.environ.setdefault(chave, valor)


carregar_env_raiz()

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
    "corsheaders",
    "django_filters",
    "rest_framework",
    "drf_spectacular",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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

database_url = os.getenv("DATABASE_URL", "")
database_connect_timeout = int(os.getenv("DATABASE_CONNECT_TIMEOUT_SECONDS", "5"))

if database_url:
    parsed_database = urlparse(database_url)
    if not parsed_database.scheme.startswith("postgres"):
        raise RuntimeError("DATABASE_URL deve usar PostgreSQL neste projeto.")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed_database.path.lstrip("/"),
            "USER": unquote(parsed_database.username or ""),
            "PASSWORD": unquote(parsed_database.password or ""),
            "HOST": parsed_database.hostname or "",
            "PORT": str(parsed_database.port or ""),
            "OPTIONS": {"connect_timeout": database_connect_timeout},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DATABASE_NAME", "autoponto"),
            "USER": os.getenv("DATABASE_USER", "autoponto"),
            "PASSWORD": os.getenv("DATABASE_PASSWORD", "autoponto"),
            "HOST": os.getenv("DATABASE_HOST", "localhost"),
            "PORT": os.getenv("DATABASE_PORT", "5432"),
            "OPTIONS": {"connect_timeout": database_connect_timeout},
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
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

CORS_ALLOWED_ORIGINS = [
    origem.strip()
    for origem in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",")
    if origem.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origem.strip()
    for origem in os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",")
    if origem.strip()
]

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
INTERSCITY_BASE_URL = os.getenv("INTERSCITY_BASE_URL", "https://cidadesinteligentes.lsdi.ufma.br/interscity_lh").rstrip("/")
INTERSCITY_CATALOG_URL = os.getenv("INTERSCITY_CATALOG_URL", f"{INTERSCITY_BASE_URL}/catalog").rstrip("/")
INTERSCITY_ADAPTOR_URL = os.getenv("INTERSCITY_ADAPTOR_URL", f"{INTERSCITY_BASE_URL}/adaptor").rstrip("/")
INTERSCITY_COLLECTOR_URL = os.getenv("INTERSCITY_COLLECTOR_URL", f"{INTERSCITY_BASE_URL}/collector").rstrip("/")
INTERSCITY_DISCOVERY_URL = os.getenv("INTERSCITY_DISCOVERY_URL", f"{INTERSCITY_BASE_URL}/discovery").rstrip("/")
INTERSCITY_ACTUATOR_URL = os.getenv("INTERSCITY_ACTUATOR_URL", f"{INTERSCITY_BASE_URL}/actuator").rstrip("/")
INTERSCITY_TIMEOUT_SECONDS = int(os.getenv("INTERSCITY_TIMEOUT_SECONDS", "5"))

FACE_DETECT_MODEL_PATH = os.getenv("FACE_DETECT_MODEL_PATH", "")
FACE_RECOG_MODEL_PATH = os.getenv("FACE_RECOG_MODEL_PATH", "")
FACE_SCORE_THRESHOLD = float(os.getenv("FACE_SCORE_THRESHOLD", "0.85"))
FACE_DUPLICATE_THRESHOLD = float(os.getenv("FACE_DUPLICATE_THRESHOLD", "0.92"))
