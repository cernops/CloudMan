import os
import sys

sys.path.append('/var/www')
sys.path.append('/var/www/cloudman')

os.environ['DJANGO_SETTINGS_MODULE'] = 'cloudman.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


