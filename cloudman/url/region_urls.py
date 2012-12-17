from django.conf.urls.defaults import *

from cloudman.settings import MEDIA_ROOT
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^add/$','cloudman.cloudman.regionQueries.addnew'),
    (r'^list/$','cloudman.cloudman.regionQueries.listall'),
    (r'^update/$','cloudman.cloudman.regionQueries.update'),
    (r'^delete/$','cloudman.cloudman.regionQueries.delete'),
    (r'^getdetails/$','cloudman.cloudman.regionQueries.getdetails'),
    (r'^getstats/$','cloudman.cloudman.regionQueries.getstats'),
    (r'^listonlynames/$','cloudman.cloudman.regionQueries.listonlynames'),
    (r'^regionallzoneinfo/$','cloudman.cloudman.regionQueries.regionAllZoneInfo'),

    #(r'^gethepspecpiechart$','cloudman.cloudman.regionQueries.getRegionHepSpecsPieChart'),
    #(r'^getzonehepspecpiechart$','cloudman.cloudman.regionQueries.getZoneHepSpecsPieChart'),
    #(r'^getallregionhepspecspiechart$','cloudman.cloudman.regionQueries.getAllRegionHepSpecsPieChart'),
)
