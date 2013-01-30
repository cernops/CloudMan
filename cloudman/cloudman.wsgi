import os
import sys

sys.path.append('/usr/apache')
sys.path.append('/usr/apache/cloudman')

os.environ['DJANGO_SETTINGS_MODULE'] = 'cloudman.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()


