from django.conf.urls.defaults import *

from cloudman.settings import MEDIA_ROOT
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^list/$','cloudman.cloudman.groupAllocationQueries.listall'),
    (r'^add/$','cloudman.cloudman.groupAllocationQueries.addnew'),
    (r'^update/$','cloudman.cloudman.groupAllocationQueries.update'),
    (r'^delete/$','cloudman.cloudman.groupAllocationQueries.delete'),
    (r'^deletemultiple/$','cloudman.cloudman.groupAllocationQueries.deleteMultiple'),
    (r'^getdetails/$','cloudman.cloudman.groupAllocationQueries.getdetails'),
    (r'^getresourceinfo/$','cloudman.cloudman.groupAllocationQueries.getresourceinfo'),
    (r'^grpallocingroup/$','cloudman.cloudman.groupAllocationQueries.getGroupAllocInGroupAllocation'),
    #(r'^getallowedresourcetypes/$','cloudman.cloudman.groupAllocationQueries.getallowedresourcetypes'),
)
