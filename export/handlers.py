from piston.handler import AnonymousBaseHandler, BaseHandler
from emitters import MyXMLEmitter
from export import getAllAllocationByTopLevel,getAllAllocationByProject
from piston.utils import rc, throttle
from piston.emitters import Emitter, XMLEmitter
from django.utils.encoding import smart_unicode
from django.utils.xmlutils import SimplerXMLGenerator
from piston.utils import validate
from django import forms


Emitter.register('xml', MyXMLEmitter, 'text/xml; charset=utf-8')
#Mimer.register(lambda *a: None, ('text/xml',))

class AllocationByTopHandler(BaseHandler):
    allowed_methods = ('GET',)
    def read(self, request):
        alloc_list={'ALLOCATION': [{'TOP_LEVEL_ALLOCATION':{'NAME':'top1','GROUP':'group1','GROUP_ALLOCATION':[{'tmp1':{'NAME':'top2','GROUP':'group2'}},{'tmp1':{'NAME':'top2','GROUP':'group2'}}]} },
                                          {'TOP_LEVEL_ALLOCATION':{'NAME':'top2','GROUP':'group2','GROUP_ALLOCATION':{'NAME':'top2','GROUP':'group2'}} },
                                          {'TOP_LEVEL_ALLOCATION':{'NAME':'top2','GROUP':'group2','GROUP_ALLOCATION':{'NAME':'top2','GROUP':'group2'}} },
                                         ]
                          }
        resolvegroup = request.REQUEST.get('resolvegroup','')
        alloc_list =  getAllAllocationByTopLevel(resolvegroup)
        return alloc_list
    
class AllocationByProjectHandler(BaseHandler):
    allowed_methods = ('GET',)
    def read(self, request):
        alloc_list={'ALLOCATION': [{'TOP_LEVEL_ALLOCATION':{'NAME':'top1','GROUP':'group1','GROUP_ALLOCATION':[{'tmp1':{'NAME':'top2','GROUP':'group2'}}]} },
                                          {'TOP_LEVEL_ALLOCATION':{'NAME':'top2','GROUP':'group2','GROUP_ALLOCATION':{'NAME':'top2','GROUP':'group2'}} },
                                         ]
                          }        
        resolvegroup = request.REQUEST.get('resolvegroup','')
        alloc_list =  getAllAllocationByProject(resolvegroup)
        return alloc_list
