from django.conf.urls.defaults import *
import settings
urlpatterns = patterns('',
    (r'^resourcetype/', include('cloudman.url.resourcetype_urls')),
    (r'^region/', include('cloudman.url.region_urls')),
    (r'^zone/', include('cloudman.url.zone_urls')),
    (r'^group/', include('cloudman.url.group_urls')),
    (r'^project/', include('cloudman.url.project_urls')),
    (r'^toplevelallocation/', include('cloudman.url.toplevelallocation_urls')),
    (r'^projectallocation/', include('cloudman.url.projectallocation_urls')),
    (r'^groupallocation/', include('cloudman.url.groupallocation_urls')),
    (r'^log/', include('cloudman.url.log_urls')),
    (r'^egroup/', include('cloudman.url.egroup_urls')),
    (r'^message/$','cloudman.cloudman.views.message'),
    (r'^$', 'cloudman.cloudman.views.home'),
    (r'^homepanel$', 'cloudman.cloudman.views.homepanel'),
    (r'^homepagedata/$', 'cloudman.cloudman.views.homepagedata'),
)
urlpatterns += patterns('',
    (r'^cloudman/resourcetype/', include('url.resourcetype_urls')),
    (r'^cloudman/region/', include('url.region_urls')),
    (r'^cloudman/zone/', include('cloudman.url.zone_urls')),
    (r'^cloudman/group/', include('cloudman.url.group_urls')),
    (r'^cloudman/project/', include('cloudman.url.project_urls')),
    (r'^cloudman/toplevelallocation/', include('cloudman.url.toplevelallocation_urls')),
    (r'^cloudman/projectallocation/', include('cloudman.url.projectallocation_urls')),
    (r'^cloudman/groupallocation/', include('cloudman.url.groupallocation_urls')),
    (r'^cloudman/log/', include('cloudman.url.log_urls')),
    (r'^cloudman/egroup/', include('cloudman.url.egroup_urls')),
    (r'^cloudman/message/$','cloudman.cloudman.views.message'),
    (r'^$', 'cloudman.cloudman.views.home'),
    (r'^cloudman/homepanel$', 'cloudman.cloudman.views.homepanel'),
    (r'^cloudman/homepagedata/$', 'cloudman.cloudman.views.homepagedata'),
)

if settings.DEBUG:
        urlpatterns += patterns('',(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes':True}),
)
