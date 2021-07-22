import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'padword',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'padword',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '5432',                      # Set to empty string for default.
    }
}

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'shidixtenerife@gmail.com'
EMAIL_HOST_PASSWORD = 'shShidix2005'
EMAIL_PORT = 587

