"""
Django settings for tesis project.

Generated by 'django-admin startproject' using Django 1.11.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ')yp24--99+$n%9&4+@4q=rzkpwcc9*db9$!5hsc-1kv0g+*c27'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['192.168.1.110', 
                 '200.16.19.25', 
                 'lac.efn.uncor.edu',
                 '127.0.0.1', 
                 'localhost']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    

    # Para el manejo de formularios Django con Bootsrap 4.
    'bootstrap4',

    # Aplicaciones propias creadas, es necesario registrarlas aca.
    'events',
    'users',
    'devices',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Middleware propio creado, es necesario registrarlo aca.
    'users.middleware.PreventConcurrentLoginsMiddleware',
    'users.middleware.PreventUserActionOutOfTimeZone'
]

ROOT_URLCONF = 'tesis.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django_settings_export.settings_export',
            ],
        },
    },
    
]

WSGI_APPLICATION = 'tesis.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases


# En caso de usar un Mongo remoto y querer tener un Mongo local para respaldo, descomentar la siguiente linea "DATABASE_ROUTERS", y agregar
# "backup" en DATABASES. 
# 
# Tener en cuenta lo siguiente:
# - Al momento de levantar el servicio web mediante python manage.py runserver , la base de datos por "default" TIENE que estar levantada y ser accesible.
#   Luego de poder conectarse por primera vez, en caso de que se caiga la conexión, se establecerá la conexión con la de backup.
# - La base establecida por "default" será la primera a la que se querrá acceder. El rounter dbRouter intenterá escribir o leer de esa base, y en caso de falla
#   se comunicará con la de backup.

DATABASE_ROUTERS = ['tesis.dbRouter.dbRouter']
DATABASES = {
        'backup': {
            'ENGINE': 'djongo',
            'ENFORCE_SCHEMA': False,
            'NAME': 'djongo',
            'HOST': 'mongodb://djongo:dj0ng0@24.232.132.26:27015/?authMechanism=DEFAULT&authSource=djongo',
        },
        'default': {
            'ENGINE': 'djongo',
            'ENFORCE_SCHEMA': False,
            'NAME': 'backup-djongo',
            'HOST': 'mongodb://127.0.0.1:27017'
        }
    #         'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'db.sqlite31'),
    # }
    }

FILES_API_BASE_URL = os.getenv('FILES_API_BASE_URL', 'https://192.168.1.110/api/v1/files/')
API_BASE_URL = os.getenv('API_BASE_URL', 'https://192.168.1.110/api/v1')
API_USUARIO  = os.getenv('API_USUARIO', 'usuario-api')
API_PASSWORD = os.getenv('API_PASSWORD', 'password-api')
API_CERT_PATH = os.getenv('API_CERT_PATH', '/home/agustin/tesis/nginx-config-files/RootCA.pem')
SETTINGS_EXPORT = [
   'FILES_API_BASE_URL',
   'API_BASE_URL',
   'API_USUARIO',
   'API_PASSWORD',
   'API_CERT_PATH'
]

# Auth

AUTH_USER_MODEL = 'users.User'

# LOGIN_REDIRECT_URL = 'devices:home'
LOGIN_REDIRECT_URL = 'devices:home'
LOGIN_URL = 'users:login'
LOGOUT_REDIRECT_URL = 'users:login'


# Sessions
# Se especifica que se eliminen las sesiones del usuario una vez que el mismo
# cierra el explorador.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Email
# se utiliza el servidor smtp de google, conexion segura con
# ssl y la cuenta de gmail creada para la placa.

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = 'accesolac@gmail.com'
# EMAIL_HOST_PASSWORD = 'raspberry'
EMAIL_HOST_PASSWORD ='qqpshylxrwvyuvju'
EMAIL_USE_SSL = True

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'es-ar'

TIME_ZONE = 'America/Argentina/Cordoba'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

# Para agregar directorios de archivos estaticos.
# En este caso se agrega un directorio al proyecto raiz.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}

from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}