from django.conf.urls.defaults import *

from cloudman.settings import MEDIA_ROOT
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^list/$','cloudman.cloudman.topLevelAllocationQueries.listall'),
    (r'^add/$','cloudman.cloudman.topLevelAllocationQueries.addnew'),
    (r'^update/$','cloudman.cloudman.topLevelAllocationQueries.update'),
    (r'^delete/$','cloudman.cloudman.topLevelAllocationQueries.delete'),
    (r'^deletemultiple/$','cloudman.cloudman.topLevelAllocationQueries.deleteMultiple'),
    (r'^getdetails/$','cloudman.cloudman.topLevelAllocationQueries.getdetails'),

    (r'^gethepspecstats/$','cloudman.cloudman.topLevelAllocationQueries.gethepspecstats'),
    (r'^getresourceinfo/$','cloudman.cloudman.topLevelAllocationQueries.getresourceinfo'),
    (r'^getzonelist/$','cloudman.cloudman.topLevelAllocationQueries.getzonelist'),
    (r'^getzoneresourceinfo/$','cloudman.cloudman.topLevelAllocationQueries.getzoneresourceinfo'),
    (r'^listonlynames/$','cloudman.cloudman.topLevelAllocationQueries.listonlynames'),
    (r'^prjallocintop/$','cloudman.cloudman.topLevelAllocationQueries.getProjectAllocInTopLevelAllocation'),

    #(r'^getregionshepspecpiechart$','cloudman.cloudman.topLevelAllocationQueries.getregionshepspecspiechart'),
    #(r'^getzoneshepspecpiechart$','cloudman.cloudman.topLevelAllocationQueries.getzoneshepspecspiechart'),
    #(r'^gethepspecpiechart$','cloudman.cloudman.topLevelAllocationQueries.gethepspecspiechart'),
    #(r'^gettopallochepspecpiechart$','cloudman.cloudman.topLevelAllocationQueries.getTopAllocHepSpecPieChart'),
)
