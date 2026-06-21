import os
from datetime import timedelta
from pathlib import Path

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


def env_obrigatoria(nome: str, *, permitir_vazio: bool = False) -> str:
    if nome not in os.environ:
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {nome}")
    valor = os.environ[nome]
    if not permitir_vazio and valor == "":
        raise RuntimeError(f"Variavel de ambiente obrigatoria vazia: {nome}")
    return valor


def env_int(nome: str) -> int:
    return int(env_obrigatoria(nome))


def env_float(nome: str) -> float:
    return float(env_obrigatoria(nome))


def env_bool(nome: str) -> bool:
    valor = env_obrigatoria(nome).lower()
    if valor not in {"true", "false"}:
        raise RuntimeError(f"Variavel {nome} deve ser True ou False.")
    return valor == "true"


def env_lista(nome: str) -> list[str]:
    valores = [
        item.strip() for item in env_obrigatoria(nome).split(",") if item.strip()
    ]
    if not valores:
        raise RuntimeError(f"Variavel {nome} deve conter ao menos um valor.")
    return valores


SECRET_KEY = env_obrigatoria("DJANGO_SECRET_KEY")
DEBUG = env_bool("DJANGO_DEBUG")
ALLOWED_HOSTS = env_lista("DJANGO_ALLOWED_HOSTS")

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

database_connect_timeout = env_int("DATABASE_CONNECT_TIMEOUT_SECONDS")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env_obrigatoria("DATABASE_NAME"),
        "USER": env_obrigatoria("DATABASE_USER"),
        "PASSWORD": env_obrigatoria("DATABASE_PASSWORD"),
        "HOST": env_obrigatoria("DATABASE_HOST"),
        "PORT": env_obrigatoria("DATABASE_PORT"),
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
TIME_ZONE = env_obrigatoria("TIME_ZONE")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

CORS_ALLOWED_ORIGINS = env_lista("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_lista("CSRF_TRUSTED_ORIGINS")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
PUBLIC_API_DOCS = env_bool("PUBLIC_API_DOCS")
API_DOCS_SERVER_URL = env_obrigatoria("API_DOCS_SERVER_URL")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "api.Usuario"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_THROTTLE_CLASSES": ("rest_framework.throttling.ScopedRateThrottle",),
    "DEFAULT_THROTTLE_RATES": {
        "auth_login": "100/min",
        "auth_refresh": "100/min",
        "biometria": "20/hour",
        "edge_attendance": "600/min",
    },
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
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_TOKEN_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env_int("JWT_REFRESH_TOKEN_DAYS")),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "AutoPonto API",
    "DESCRIPTION": "API de automacao de frequencia academica para o TCC AutoPonto.",
    "VERSION": "1.0.0",
    "SERVERS": [
        {
            "url": API_DOCS_SERVER_URL,
            "description": "Configured API docs server",
        },
    ],
    "SERVE_INCLUDE_SCHEMA": False,
}


INTERSCITY_ENABLED = env_bool("INTERSCITY_ENABLED")
INTERSCITY_BASE_URL = env_obrigatoria("INTERSCITY_BASE_URL").rstrip("/")
INTERSCITY_CATALOG_PATH = env_obrigatoria("INTERSCITY_CATALOG_PATH")
INTERSCITY_DISCOVERY_PATH = env_obrigatoria("INTERSCITY_DISCOVERY_PATH")
INTERSCITY_COLLECTOR_PATH = env_obrigatoria("INTERSCITY_COLLECTOR_PATH")
INTERSCITY_ADAPTOR_PATH = env_obrigatoria("INTERSCITY_ADAPTOR_PATH")
INTERSCITY_ACTUATOR_PATH = env_obrigatoria("INTERSCITY_ACTUATOR_PATH")
INTERSCITY_TIMEOUT_SECONDS = env_int("INTERSCITY_TIMEOUT_SECONDS")

FACE_DETECT_MODEL_PATH = env_obrigatoria("FACE_DETECT_MODEL_PATH", permitir_vazio=True)
FACE_RECOG_MODEL_PATH = env_obrigatoria("FACE_RECOG_MODEL_PATH", permitir_vazio=True)
FACE_SCORE_THRESHOLD = env_float("FACE_SCORE_THRESHOLD")
FACE_DUPLICATE_THRESHOLD = env_float("FACE_DUPLICATE_THRESHOLD")
FACE_MAX_CAPTURAS = env_int("FACE_MAX_CAPTURAS")
FACE_MAX_IMAGE_BYTES = env_int("FACE_MAX_IMAGE_BYTES")
FACE_MAX_IMAGE_PIXELS = env_int("FACE_MAX_IMAGE_PIXELS")

NODE_TOKEN_EXPIRATION_DAYS = env_int("NODE_TOKEN_EXPIRATION_DAYS")
EDGE_AUDIT_MAX_EVENTS = env_int("EDGE_AUDIT_MAX_EVENTS")

JWT_REFRESH_COOKIE_NAME = env_obrigatoria("JWT_REFRESH_COOKIE_NAME")
JWT_REFRESH_COOKIE_PATH = env_obrigatoria("JWT_REFRESH_COOKIE_PATH")
JWT_REFRESH_COOKIE_SECURE = env_bool("JWT_REFRESH_COOKIE_SECURE")
JWT_REFRESH_COOKIE_SAMESITE = env_obrigatoria("JWT_REFRESH_COOKIE_SAMESITE")
DATA_UPLOAD_MAX_MEMORY_SIZE = env_int("DATA_UPLOAD_MAX_MEMORY_SIZE")
