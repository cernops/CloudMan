from django.conf.urls.defaults import *
from cloudman.settings import MEDIA_ROOT
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
urlpatterns = patterns('',
     (r'^changeloglist/$','cloudman.cloudman.logQueries.listChangeLog'),
     (r'^issuelist/$','cloudman.cloudman.logQueries.issuepanel'),
     (r'^logpanel/$','cloudman.cloudman.logQueries.logpanel'),
     (r'^issuepanel/$','cloudman.cloudman.logQueries.issuepanel'),
)

