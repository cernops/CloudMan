from cloudman.models import *
from django.template import RequestContext, loader, Context
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings


def roles123(request):
    title = "Welcome"
    return render_to_response('roleManage.html',locals(),context_instance=RequestContext(request))
