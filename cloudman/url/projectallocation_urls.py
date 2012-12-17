from django.conf.urls.defaults import *

from cloudman.settings import MEDIA_ROOT
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^list/$','cloudman.cloudman.projectAllocationQueries.listall'),
    (r'^add/$','cloudman.cloudman.projectAllocationQueries.addnew'),
    (r'^update/$','cloudman.cloudman.projectAllocationQueries.update'),
    (r'^delete/$','cloudman.cloudman.projectAllocationQueries.delete'),
    (r'^deletemultiple/$','cloudman.cloudman.projectAllocationQueries.deleteMultiple'),
    (r'^getdetails/$','cloudman.cloudman.projectAllocationQueries.getdetails'),
    (r'^getdepth/$','cloudman.cloudman.projectAllocationQueries.getdepth'),
    (r'^gethepspecstats$','cloudman.cloudman.projectAllocationQueries.gethepspecstats'),
    (r'^getresourceinfo/$','cloudman.cloudman.projectAllocationQueries.getresourceinfo'),
	(r'^getattrinfo/$','cloudman.cloudman.projectAllocationQueries.getAttrInfo'),
    (r'^grpallocinproject/$','cloudman.cloudman.projectAllocationQueries.getGroupAllocInProjectAllocation'),
    #(r'^getallowedresourcetypes/$','cloudman.cloudman.projectAllocationQueries.getallowedresourcetypes'),
    #(r'^gettphepspecpiechart$','cloudman.cloudman.projectAllocationQueries.gettphepspecspiechart'),
    #(r'^getprhepspecpiechart$','cloudman.cloudman.projectAllocationQueries.getprhepspecspiechart'),
)
