from django.conf.urls.defaults import *

from cloudman.settings import MEDIA_ROOT
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
     (r'^add/$','cloudman.cloudman.zoneQueries.addnew'),
     (r'^list/$','cloudman.cloudman.zoneQueries.listall'),
     (r'^update/$','cloudman.cloudman.zoneQueries.update'),
     (r'^delete/$','cloudman.cloudman.zoneQueries.delete'),
     (r'^getdetails/$','cloudman.cloudman.zoneQueries.getdetails'),
     (r'^getallocations/$','cloudman.cloudman.zoneQueries.getallocationsinfo'),

     #(r'^gethepspecpiechart$','cloudman.cloudman.zoneQueries.getZoneHepSpecsPieChart'),
     #(r'^allowedresourcetypes/$', 'cloudman.cloudman.zoneQueries.allowedresourcetypes'),
)
