# Django settings for cloudman project.
import os.path
from ConfigParser import ConfigParser, NoSectionError
from django.core.exceptions import ImproperlyConfigured

# Set up some useful paths for later
from os import path as os_path

#APP_PATH = os_path.abspath(os_path.split(__file__)[0])

#PROJECT_PATH = os_path.abspath(os_path.join(APP_PATH,'..','..'))

config = ConfigParser()
read_files = config.read(['/etc/cloudman/config'])

DEBUG = True 
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('CERN-IT-PES & BARC Computer Division', 'cloudman-support@barc.gov.in'),
)

#MANAGERS = ADMINS
if not read_files:
    raise ImproperlyConfigured("Could not read config file : %s"%config_file)

try:
    USER = config.get('database', 'USER')
    PASSWORD = config.get('database', 'PASSWORD')
    HOST = config.get('database', 'HOST')
    PORT = config.get('database', 'PORT')
    ENGINE = config.get('database', 'ENGINE')
    NAME = config.get('database', 'NAME')
    KSI2K = config.get('conversion','KSI2K')
    VCPU = config.get('conversion','VCPU')
    MPERF = config.get('conversion','MPERF')
    DEFAULT_CPU_UNIT = config.get('unit','DEFAULT_CPU_UNIT')
    DEFAULT_STORAGE_UNIT = config.get('unit','DEFAULT_STORAGE_UNIT')
    CPU_UNIT_NAME = eval(config.get("unit","CPU_UNIT_NAME"),{},{})
    CPU_UNIT_CONVERSION_FACTOR = eval(config.get("unit","CPU_UNIT_CONVERSION_FACTOR"),{},{})
    STORAGE_UNIT_NAME = eval(config.get("unit","STORAGE_UNIT_NAME"),{},{})
    STORAGE_UNIT_CONVERSION_FACTOR = eval(config.get("unit","STORAGE_UNIT_CONVERSION_FACTOR"),{},{})
    SUPER_USER_GROUPS = eval(config.get("admin","SUPER_USER_GROUPS"),{},{})
    LDAP_SERVER = config.get('ldap', 'LDAP_SERVER')
    LDAP_BASE = config.get('ldap', 'LDAP_BASE')
    GROUP_ALLOC_DEPTH = config.get('group_allocation', 'GROUP_ALLOC_DEPTH')
except NoSectionError, e:
    raise ImproperlyConfigured(e)

DATABASES = {
    'default': {
        'ENGINE': ENGINE, # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': NAME,                      # Or path to database file if using sqlite3.
        'USER': USER,                      # Not used with sqlite3.
        'PASSWORD': PASSWORD,                  # Not used with sqlite3.
        'HOST': HOST,                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': PORT,                      # Set to empty string for default. Not used with sqlite3.
    }
}

#SUPER_USER_GROUPS = eval(config.get("admin","SUPER_USER_GROUPS"),{},{})

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = None 

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
#MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media') 

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
#MEDIA_URL = '/cloudman/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".

#ADMIN_MEDIA_PREFIX = '/cloudman/media_admin/'
#INTERNAL_IPS = ('127.0.0.1','128.142.139.61',)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '8884ub7jvwd=avb%=4+@%wk9=zy+d9ua!+&pkp#fd34)+3cab-'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)


ROOT_URLCONF = 'export.urls'

#TEMPLATE_DIRS = (
#    '/var/www/cloudman/templates',
#)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.markup',
    'export',
    'debug_toolbar',    
)
