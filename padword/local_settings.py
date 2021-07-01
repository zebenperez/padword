ALLOWED_HOSTS = ['*']

DATABASES = { 
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'padword-ms-configuration', 
        'USER': 'padword',
        'PASSWORD': 'padword',
        'HOST': 'db-cfg',   
        'PORT': '3306', # Set to empty string for default.
    }   ,
    'guest': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'padword-ms-guests', 
        'USER': 'padword',
        'PASSWORD': 'padword',
        'HOST': 'db-cfg',   
        'PORT': '3306', # Set to empty string for default.
    }   
}

