"""
Configurações do projeto SIGHA (Sistema Inteligente de Gestão de Horários Acadêmicos).

Este arquivo lê os parâmetros sensíveis (chave secreta, credenciais do banco)
a partir de variáveis de ambiente (.env), nunca hardcoded no código-fonte.
"""

from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Segurança básica
# ---------------------------------------------------------------------------
SECRET_KEY = config('DJANGO_SECRET_KEY', default='django-insecure-mude-esta-chave-em-producao')
DEBUG = config('DJANGO_DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Proteções adicionais (CSRF / XSS / Clickjacking / Cookies seguros)
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# Em produção (DEBUG=False) força HTTPS e cookies seguros.
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = config('DJANGO_SECURE_SSL_REDIRECT', default=False, cast=bool)

# Encerra a sessão do usuário após período de inatividade (segurança).
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=60 * 60 * 4, cast=int)  # 4 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ---------------------------------------------------------------------------
# Aplicações
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Terceiros
    'rest_framework',
    'django_ratelimit',

    # Apps do SIGHA (adicionados conforme cada módulo é concluído)
    'apps.usuarios',
    'apps.dashboard',
    'apps.professores',
    'apps.disciplinas',
    'apps.turmas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise: serve os arquivos estáticos (CSS/JS do próprio SIGHA)
    # diretamente pelo Gunicorn. Sem isso, em produção (docker-compose,
    # sem Nginx) o Bootstrap carrega do CDN mas o nosso theme.css/theme.js
    # retornam 404 e o layout do menu lateral/tema quebra.
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# ---------------------------------------------------------------------------
# Banco de dados — PostgreSQL (nunca planilhas, nunca SQLite em produção)
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='sigha'),
        'USER': config('DB_USER', default='sigha'),
        'PASSWORD': config('DB_PASSWORD', default='sigha'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,
    }
}

# ---------------------------------------------------------------------------
# Usuário customizado (Módulo 1 — Usuários)
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = 'usuarios.Usuario'

LOGIN_URL = 'usuarios:login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'usuarios:login'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Internacionalização
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Arquivos estáticos
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        # A versão com hash no nome do arquivo (theme.abcd123.css) exige que
        # "collectstatic" já tenha rodado (gera um manifesto). Em desenvolvimento
        # local (DEBUG=True, sem collectstatic) isso quebraria o runserver/testes,
        # então só usamos o hash em produção — exatamente o que o
        # docker-compose.yml já faz antes de subir o Gunicorn.
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
            if not DEBUG else
            'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Cache — usado pelo django-ratelimit (proteção de força bruta no login).
# Precisa ser um backend compartilhado com incremento atômico; por isso
# usamos Redis (serviço próprio no docker-compose.yml).
# ---------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://redis:6379/1'),
    }
}

# O django-ratelimit ainda não atualizou sua lista de backends "oficialmente
# suportados" para incluir o RedisCache nativo do Django (4+), mas ele usa o
# comando INCR do Redis por baixo dos panos, que é atômico. Falso positivo.
SILENCED_SYSTEM_CHECKS = ['django_ratelimit.W001']

# ---------------------------------------------------------------------------
# Django REST Framework (Módulo 12 — API, habilitado desde já)
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# ---------------------------------------------------------------------------
# Logging básico (Módulo 11 — Auditoria será expandido futuramente)
# ---------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
