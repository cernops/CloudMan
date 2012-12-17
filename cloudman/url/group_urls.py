from django.conf.urls.defaults import *

from cloudman.settings import MEDIA_ROOT
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
     (r'^list/$','cloudman.cloudman.groupQueries.listall'),
     (r'^update/$','cloudman.cloudman.groupQueries.update'),
     (r'^add/$','cloudman.cloudman.groupQueries.addnew'),
     (r'^delete/$','cloudman.cloudman.groupQueries.delete'),
     (r'^deletemultiple/$','cloudman.cloudman.groupQueries.deleteMultiple'),
     (r'^getdetails/$','cloudman.cloudman.groupQueries.getdetails'),
     (r'^getegrouplist/$','cloudman.cloudman.groupQueries.getEgroupListNameContainJSON'),
)
