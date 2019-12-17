import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# What part of your disk is guaranteed left empty by WM
MIN_FREE_DISK_SPACE = os.getenv('MIN_FREE_DISK_SPACE', 0.10)

### WM2 SETTINGS
# You only need to set that if you'll be using the userscripts. Do not put a trailing slash
USERSCRIPT_WM_ROOT = os.getenv('WM_HOSTNAME')

### TRANSMISSION SETTINGS
# Set this to something reasonable that only you know.
TRANSMISSION_PASSWORD = os.getenv('TRANSMISSION_PASSWORD', '')
# Where Transmission system files will go
TRANSMISSION_FILES_ROOT = os.path.join(MEDIA_ROOT, 'transmission')
# Transmission's ipv4 bind address. Leave as is or changed to specific ip.
TRANSMISSION_BIND_HOST = '0.0.0.0'
# Set this to true to use systemd rather than Upstart for Transmission daemon instances
TRANSMISSION_USE_SYSTEMD = False
# You only need to set these if you are running transmission_files_sync
FILES_SYNC_HTTP_USERNAME = 'username'
FILES_SYNC_HTTP_PASSWORD = 'password'
FILES_SYNC_SSH = 'user@host.com'
FILES_SYNC_WM_ROOT = 'https://host.com/'

### TRANSCODER SETTINGS
# You only need to set these if you are running the transcoder
TRANSCODER_ADD_TORRENT_URL = 'http://localhost/json/add_torrent'
TRANSCODER_HTTP_USERNAME = os.getenv('WM_USER')
TRANSCODER_HTTP_PASSWORD = os.getenv('WM_PASSWORD')
TRANSCODER_TEMP_DIR = os.path.join(MEDIA_ROOT, 'temp/transcoder/whatup.celery.{0}'.format(os.getpid()))
TRANSCODER_ERROR_OUTPUT = os.path.join(MEDIA_ROOT, 'logs/transcode_error.html')
TRANSCODER_FORMATS = ['V0', '320']
# Transcoder Queue
CELERY_BROKER_URL = 'amqp://guest:guest@whatmanager2_rabbitmq_1:5672/'
CELERY_RESULT_BACKEND = 'amqp://guest@whatmanager2_rabbitmq_1//'

### QOBUZ / TIDAL SETTINGS
QILLER_ERROR_OUTPUT = os.path.join(MEDIA_ROOT, 'logs/qiller_error.html')

### REDACTED SETTINGS
# Only if you're going to run wcd_pth_migration
WCD_PTH_SPECTRALS_HTML_PATH = os.path.join(MEDIA_ROOT, 'temp/spectrals')

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['localhost', 'django', os.getenv('WM_HOSTNAME')]

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.getenv('SECRET_KEY', '5hZ7fpjeRTeLzgRsRhT9').encode()

DEBUG = os.getenv('DEBUG', True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'whatmanager',  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'root',
        'PASSWORD': os.getenv('MYSQL_ROOT_PASSWORD'),
        'HOST': 'whatmanager2_db_1',
        # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '3306',  # Set to empty string for default.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')

# Used permissions
# home_view_logentry - Viewing logs
# home_add_whattorrent - Adding torrents
# home_view_whattorrent - Viewing torrents
# what_transcode.add_transcoderequest - Adding transcode requests
# home.run_checks = Running checks
# home.view_transinstance_stats - Realtime stats viewing
# what_queue.view_queueitem - Viewing the queue
# what_queue.add_queueitem - Add to the queue
# what_profile.view_whatusersnapshot - Viewing the user profile
# home.download_whattorrent - Downloading torrent zips


# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = 'static'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Login URL
LOGIN_URL = '/user/login'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #os.path.join(BASE_DIR, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(os.path.dirname(__file__), '..', 'templates').replace('\\', '/')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'WhatManager2.context_processors.context_processor',
            ],
        },
    },
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'WhatManager2.middleware.HttpBasicAuthMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'WhatManager2.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'WhatManager2.wsgi.application'

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Library apps
    'bootstrapform',
    # WhatManager2 apps
    'WhatManager2',
    'login',
    'home',
    'what_json',
    'download',
    'what_queue',
    'what_profile',
    'what_transcode',
    'books',
    'bibliotik',
    'bibliotik_json',
    'what_meta',
    'whatify',
    'qobuz2',
    'myanonamouse',
]

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

DATETIME_FORMAT = 'Y-m-d H:i:s'

# CACHES = {
# 'default': {
# 'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
# 'LOCATION': 'wm-cache'
# }
# }
