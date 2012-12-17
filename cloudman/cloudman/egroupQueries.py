from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext, loader, Context
from django.shortcuts import render_to_response
from django.conf import settings
from models import Groups
from models import Egroups
from getPrivileges import isSuperUser
from ldapSearch import checkEGroup
from django.db.models import Q
from commonFunctions import *
import copy


def delete(request):
    egroup = request.REQUEST.get("name", "")
    comment = request.REQUEST.get("comment", "Egroup deleted in CLOUDMAN")
    #redirectURL = '/cloudman/message/?msg='
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';')
    ## delete egroup from cloudman only if he has cloudman resource manager privileges
    userIsSuperUser = isSuperUser(groupsList)
    if not userIsSuperUser:
        message = "You does't possess Cloudman Resource Manager Privileges. Hence you are not authorized to delete egroup "%egroup
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)
    # check if any zone/project/group has this egroup
    grpList = Groups.objects.filter(admin_group=egroup).values_list('name',flat=True)
    prjList = Project.objects.filter(admin_group=egroup).values_list('name',flat=True)
    regionList = Region.objects.filter(admin_group=egroup).values_list('name',flat=True)
    if  grpList or  prjList or regionList:
        finalMessage = "Egroup with Name " + egroup + " Could not be deleted because it is being used in Some Group/Project/Region" + "<br/>" 
        html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/log/issuelist/\"></HEAD><body> %s.</body></html>" % finalMessage
    else:
        try:
            Egroups.objects.get(name=egroup).delete()               
            addEgroupLog(request,egroup,'egroup','deleteCLOUDMAN',comment,False)
            ## return a success message to the user
            message = "Egroup with Name " + egroup + " deleted successfully in CLOUDMAN"
            html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/log/issuelist/\"></HEAD><body> %s.</body></html>" % message
        except Exception:
            printStackTrace()
            message = "Erssssror while deleting Egroup  " + egroup  
            html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/log/issuelist/\"></HEAD><body> %s.</body></html>" % message
            
    return HttpResponse(html)
