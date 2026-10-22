"""Настройки модуля администратора программного комплекса управления диспансером."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR.parent / 'frontend' / 'dist'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-only-secret-key-change-me')
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'accounts',
    'directory',
    'schedule',
    'appointments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
        'DIRS': [FRONTEND_DIST],
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

# По умолчанию используется PostgreSQL; для быстрого запуска без сервера БД
# можно задать DB_ENGINE=sqlite.
if os.environ.get('DB_ENGINE', 'postgresql') == 'sqlite':
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'medadmin'),
            'USER': os.environ.get('DB_USER', 'medadmin'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'medadmin'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Irkutsk'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/assets/'
STATICFILES_DIRS = [FRONTEND_DIST / 'assets'] if (FRONTEND_DIST / 'assets').exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['accounts.permissions.IsAdministrator'],
}

# Правила аутентификации (подраздел 1.6, требование 3.2)
LOGIN_MAX_ATTEMPTS = 3
LOGIN_LOCK_MINUTES = 15

# Адрес модуля ведения приёма, куда перенаправляется врач после входа
DOCTOR_MODULE_URL = os.environ.get('DOCTOR_MODULE_URL', '/doctor/')

# SMS-шлюз: console – вывод в журнал (разработка), http – отправка во внешний шлюз
SMS_BACKEND = os.environ.get('SMS_BACKEND', 'console')
SMS_GATEWAY_URL = os.environ.get('SMS_GATEWAY_URL', '')
SMS_GATEWAY_TOKEN = os.environ.get('SMS_GATEWAY_TOKEN', '')
SMS_SENDER = os.environ.get('SMS_SENDER', 'Dispanser')
# телефон регистратуры, который указывается в каждом SMS-уведомлении
REGISTRY_PHONE = os.environ.get('REGISTRY_PHONE', '+7 (3952) 00-00-00')
