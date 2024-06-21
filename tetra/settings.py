
from pathlib import Path
import environ

import warnings

# Suppress Cosmos DB warning
warnings.filterwarnings("ignore", message="You appear to be connected to a CosmosDB cluster")

# Initialise environment variables
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-nqxv%ix1)*#b2&=-0lr@ew%#d+w!zoe%w5%62t9g-gh+z97^w7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG =  bool(env('DEBUG'))

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'agenda',
    'abonos',
    'gastos',
    'tetra',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'environ'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ALLOWED_HOSTS = ['localhost', '127.0.0.1','<MY_IP>','<IP>']

CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    'http://*.127.0.0.1',
    'http://<IP>',
    'http://<MY_IP>'
]

CSRF_TRUSTED_ORIGINS = ['http://*.127.0.0.1', "http://localhost",'http://<MY_IP>', 'http://<IP>']

CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = ['Authorization', 'Content-Type']
CORS_ALLOW_CREDENTIALS = True


ROOT_URLCONF = 'tetra.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'tetra.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases


CONNECTION_STRING = env('CONNECTION_STRING')

DB = {
    'PASS' : env('DB_PASS'),
    'HOST' : env('DB_HOST'),
    'USER' : env('DB_USER'),
    'PORT': int(env('DB_PORT')),
    'NAME': env('DB_NAME')
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
