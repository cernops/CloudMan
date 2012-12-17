from django.conf.urls.defaults import *

from cloudman.settings import MEDIA_ROOT
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
     (r'^add/$','cloudman.cloudman.resourceTypeQueries.addnew'),
     (r'^list/$','cloudman.cloudman.resourceTypeQueries.listall'),
     (r'^update/$','cloudman.cloudman.resourceTypeQueries.update'),
     (r'^delete/$','cloudman.cloudman.resourceTypeQueries.delete'),
     (r'^getdetails/$','cloudman.cloudman.resourceTypeQueries.getdetails'),
)
