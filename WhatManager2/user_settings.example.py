import os

### WM2 SETTINGS
# You only need to set that if you'll be using the userscripts. Do not put a trailing slash
USERSCRIPT_WM_ROOT = 'http://hostname.com'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'what_manager2',  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',  # Set to empty string for default.
    }
}
# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['whatmanager']
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'
# Make this unique, and don't share it with anybody.
SECRET_KEY = b'KCcrN5XMd3hBSmw3T7RECwFwh'
DEBUG = True

### TRANSMISSION SETTINGS
# Set this to something reasonable that only you know.
TRANSMISSION_PASSWORD = '9dqQQ2WW'
# Where Transmission system files will go
TRANSMISSION_FILES_ROOT = '/mnt/tank/Torrent/transmission-daemon'
# Transmission's ipv4 bind address. Leave as is or changed to specific ip.
TRANSMISSION_BIND_HOST = '0.0.0.0'
# Set this to true to use systemd rather than Upstart for Transmission daemon instances
TRANSMISSION_USE_SYSTEMD = True
# You only need to set these if you are running transmission_files_sync
FILES_SYNC_HTTP_USERNAME = 'username'
FILES_SYNC_HTTP_PASSWORD = 'password'
FILES_SYNC_SSH = 'user@host.com'
FILES_SYNC_WM_ROOT = 'https://host.com/'

### TRANSCODER SETTINGS
# You only need to set these if you are running the transcoder
TRANSCODER_ADD_TORRENT_URL = 'http://localhost/json/add_torrent'
TRANSCODER_HTTP_USERNAME = 'http username'
TRANSCODER_HTTP_PASSWORD = 'http password'
TRANSCODER_TEMP_DIR = '/mnt/bulk/temp/whatup.celery.{0}'.format(os.getpid())
TRANSCODER_ERROR_OUTPUT = '/mnt/bulk/temp/what_error.html'
TRANSCODER_FORMATS = ['V0', '320']
# Transcoder Queue
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672/'
CELERY_RESULT_BACKEND = 'amqp://guest@localhost//'


### REDACTED SETTINGS
RED_USER_ID = 123456
RED_USERNAME = 'your RED username'
RED_PASSWORD = 'your RED password'
RED_API_KEY = 'your RED api key'
# How frequently your profile will be stored, in seconds
RED_PROFILE_SNAPSHOT_INTERVAL = 10 * 60
# What part of your disk is guaranteed left empty by WM
MIN_FREE_DISK_SPACE = 0.10
# Under what ratio queued torrents won't be downloaded.
MIN_RED_RATIO = 1.3
# Whether the frequent sync will make sure ReleaseInfo is there. Leave False.
SYNC_SYNCS_FILES = False
# You might set this to ssl.redacted.ch if RED has a long downtime, but ssl is up.
RED_CD_DOMAIN = 'redacted.ch'
RED_UPLOAD_URL = 'https://{0}/upload.php'.format(RED_CD_DOMAIN)
# Only for uploading
RED_ANNOUNCE = 'http://flacsfor.me/SET THIS TO YOUR ANNOUNCE/announce'
# Only if you're going to run wcd_pth_migration
WCD_PTH_SPECTRALS_HTML_PATH = '/path/to/target/folder/with/html/and/pngs'


### BIBLIOTIK SETTINGS
BIBLIOTIK_ANNOUNCE = 'https://bibliotik.me/announce.php?passkey=ee34567890abcdddfeb2888c2f1d1e6'
BIBLIOTIK_UPLOAD_URL = 'https://bibliotik.me/upload/ebooks'
BIBLIOTIK_GET_TORRENT_URL = 'https://bibliotik.me/torrents/{0}'
BIBLIOTIK_DOWNLOAD_TORRENT_URL = 'https://bibliotik.me/torrents/{0}/download'


### MYANONAMOUSE SETTINGS
MAM_USERNAME = 'your mam username'
MAM_PASSWORD = 'your mam password'
MAM_ROOT_URL = 'https://www.myanonamouse.net'
MAM_LOGIN_URL = '/takelogin.php'
MAM_GET_TORRENT_URL = '/t/{0}'


### PTPIMG SETTINGS
# You only need these if you are uploading books
PTPIMG_USERNAME = 'ptpimg username'
PTPIMG_PASSWORD = 'ptpimg password'


### QOBUZ / TIDAL SETTINGS
QOBUZ_USERNAME = 'd568138@gmail.com'
QOBUZ_PASSWORD = 'd568138@gmail.com'
PTPIMG_QOBUZ_ALBUM_ID = '0'
TIDAL_SESSION_ID = "tidal session id"
QILLER_ERROR_OUTPUT = '/mnt/bulk/temp/qiller_error.html'