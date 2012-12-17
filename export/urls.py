from django.conf.urls.defaults import *
from piston.resource import Resource
from handlers import AllocationByTopHandler,AllocationByProjectHandler
import settings

alloc_by_top = Resource(AllocationByTopHandler)
alloc_by_project = Resource(AllocationByProjectHandler)

urlpatterns = patterns('',
   url(r'^allocationbytop$', alloc_by_top , { 'emitter_format': 'xml' }),
   url(r'^allocationbytop(\.(?P<emitter_format>.+))$', alloc_by_top),
   url(r'^allocationbyproject$', alloc_by_project,{ 'emitter_format': 'xml' } ),
   url(r'^allocationbyproject(\.(?P<emitter_format>.+))$', alloc_by_project),
)
