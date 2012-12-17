from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
urlpatterns = patterns('',
     (r'^delete/$','cloudman.cloudman.egroupQueries.delete'),
)