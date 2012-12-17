from django.conf.urls.defaults import *

from cloudman.settings import MEDIA_ROOT
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
     (r'^list/$','cloudman.cloudman.projectQueries.listall'),
     (r'^add/$','cloudman.cloudman.projectQueries.addnew'),
     (r'^update/$','cloudman.cloudman.projectQueries.update'),
     (r'^delete/$','cloudman.cloudman.projectQueries.delete'),
     (r'^deletemultiple/$','cloudman.cloudman.projectQueries.deleteMultiple'),
     (r'^getdetails/$','cloudman.cloudman.projectQueries.getdetails'),
	 (r'^getattrinfo/$','cloudman.cloudman.projectQueries.getAttrInfo'),
)
