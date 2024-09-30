import os
from .jazzmin import JAZZMIN_SETTINGS
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

KCB_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA7Sv51YgaKxYYjaxMdkuo
qFNKBM6E8EzZxwQF4sjhkRvuHtmPsS5p+tHAwH4oZzdgFj3SIa16WASKOa+dXPae
MWiimJg8pe76ReYdFOmvVxx2zu3HaXHWKyEbT9oFjLFc2teLbb6IX0IwDM3WOYcT
2fGYdy+LB6xE+zngVFXdWRokGYl3zcv0i6svI9SAFFzzpSaITjnH8zkje2aVQ2XK
AxdwTg86i9CDRbrkrkvgZqqu6mmYsC5/DwpB7H1nWMKXKsBorZlp1tY4GNhsiN5A
Dp695cFYGrolkh4tbyLlBm7Vk9dGDN78OaGx2tmA9UySeqMZ9VmSIJK1qrLSmGUa
OQIDAQAB
-----END PUBLIC KEY-----"""
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-_gusuuu(ao-ryaww3y8l528s&4gkgyfet)88aq4fq!hxdp2=!3'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # QR codes
    'qrcodes.apps.QrcodesConfig',
    # school app
    'schooldocuments.apps.SchooldocumentsConfig',
    # end app
    'studentpage.apps.StudentpageConfig',
    'teacherpage.apps.TeacherpageConfig',
    'attendancepage.apps.AttendancepageConfig',
    'account.apps.AccountConfig',
    'files.apps.FilesConfig',
    'audio.apps.AudioConfig',
    'video.apps.VideoConfig',
    'exambank.apps.ExamBankConfig',
    'payments.apps.PaymentsConfig',
    'academics.apps.AcademicsConfig',
    'invoices.apps.InvoicesConfig',
    'reports.apps.ReportsConfig',
    'adminresume.apps.AdminresumeConfig',

    'django.contrib.humanize',
    'import_export',
    'crispy_forms',
    'crispy_bootstrap5',


]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'studentsystem.urls'

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
                'teacherpage.context_processors.add_teacher_to_context',
                'files.context_processors.add_pdfmenschen_to_context',

            ],
        },
    },
]

WSGI_APPLICATION = 'studentsystem.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

################################################################
# Maongodb for storing resume data
# from mongoengine import connect

# MONGODB_NAME = 'local'
# MONGODB_HOST = 'localhost'
# MONGODB_PORT = 27017

# # Connect to MongoDB
# connect(MONGODB_NAME, host=MONGODB_HOST, port=MONGODB_PORT)
# ################################################################



# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

JAZZMIN_SETTINGS = JAZZMIN_SETTINGS

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.dreamhost.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'student-pass-reset.noreply@germaninstitute.co.ke'
EMAIL_HOST_PASSWORD = 'w&X36Z37fVdn5F3%2@fM'
DEFAULT_FROM_EMAIL = 'Forgotten Password Verification <student-pass-reset.noreply@germaninstitute.co.ke>'
SERVER_EMAIL = 'student-pass-reset.noreply@germaninstitute.co.ke'
EMAIL_TIMEOUT = 30  # in seconds

# Optional: Configure email subject prefix for easier identification
EMAIL_SUBJECT_PREFIX = '[Forgotten Password Verification] '

# Optional: Set admin email addresses to receive error notifications
ADMINS = [('Admin Name', 'student-pass-reset.noreply@germaninstitute.co.ke')]


# QR codes
# In settings.py
BASE_URL = 'http://127.0.0.1:8000'  # QR code link

# custom backend authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'qrcodes.custom_auth.QRScannerAuthBackend',
]

