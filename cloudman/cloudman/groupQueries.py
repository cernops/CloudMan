from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext, loader, Context
from django.shortcuts import render_to_response
from django.db import transaction
from django.conf import settings
from models import Groups
from models import Egroups
from models import TopLevelAllocation
from models import ProjectAllocation
from models import GroupAllocation
from forms import GroupsForm
from validator import *
import simplejson
from getPrivileges import isSuperUser
from ldapSearch import checkEGroup
from django.db.models import Q
from commonFunctions import *
import copy

def checkNameIgnoreCase(groupName):
    groupExists = False
    if Groups.objects.filter(name__iexact=groupName).exists():
        groupExists = True
    return groupExists

def isAdminOfAnyGroup(adminGroups):
    userIsAdmin = False
    if len(adminGroups) < 1:
       return userIsAdmin
    qset = Q(admin_group__exact=adminGroups[0])
    if len(adminGroups) > 1:
       for group in adminGroups[1:]:
         qset = qset | Q(admin_group__exact=group)
    if (Groups.objects.filter(qset)).exists():
        userIsAdmin = True
    return userIsAdmin

def isAdminForGroup(groupName, groupList):
    userIsAdminOfGroup = False
    if len(groupList) < 1:
       return userIsAdminOfGroup
    try:
       #groupAdmin = Groups.objects.get(name=groupName).values_list('admin_group__name')
       groupObj = Groups.objects.get(name=groupName)
       adminGroupName = groupObj.admin_group	   	
       if adminGroupName in groupList:
          userIsAdminOfGroup = True
       else:
          userIsAdminOfGroup = False
    except Groups.DoesNotExist:
       return userIsAdminOfGroup
    return userIsAdminOfGroup



def isUserAllowedToUpdateOrDeleteGroup(groupName,groupsList):
    userIsSuperUser = isSuperUser(groupsList)
    if userIsSuperUser:
        return True
    else:
        userIsAdmin = isAdminForGroup(groupName, groupsList)
        return userIsAdmin

@transaction.commit_on_success
def addnew(request):
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    ## Check the user has cloudman resource manager privileges
    userIsSuperUser = isSuperUser(groupsList)  
    '''if not userIsSuperUser:
          message = "You don't have cloudman resource manager privileges. Hence you are not authorized to add new Group";
          html = "<html><body> %s.</body></html>" % message
          return HttpResponse(html)
    '''
    ## if the request is through form submission, then add the group or else return a new form 
    if request.method == 'POST':
        ## Validate the form by checking whether all the required values are provided or not
        form = GroupsForm(request.POST)
        if form.is_valid():
            redirectURL = '/cloudman/message/?msg='
            name = form.cleaned_data['name']
            groupExists = checkNameIgnoreCase(name)
            if groupExists:
                msgAlreadyExists = 'Group ' + name + ' already exists. Hence Add Group Operation Failed'
                return HttpResponseRedirect(redirectURL + msgAlreadyExists);
            description = form.cleaned_data['description']
            admin_group = form.cleaned_data['admin_group']
            comment = form.cleaned_data['comment']
            ## check first whether the admin_group exists in the local egroup table
            ## if not, then in the remote egroup database through ldap. If exists here, then add to the local table 
            egroup = None
            try:
                egroup = Egroups.objects.get(name=admin_group)
            except Egroups.DoesNotExist:
                if not (checkEGroup(admin_group)):
                    errorMessage = 'Admin E-Group Entered ' + admin_group + ' does not exists'
                    return HttpResponseRedirect(redirectURL + errorMessage)
                else:
                    egroup = Egroups(name=admin_group)
                    egroup.save()
            ## Create the group and return a success message to the user
            groupObj = Groups(name=name, description=description, admin_group=egroup)
            groupObj.save()
            groupObj = Groups.objects.get(name=name)
            if addLog(request,name,comment,groupObj,None,'group','add',True):                
                msgSuccess = 'New group ' + name  + ' added successfully'
            else:
                transaction.rollback()
                msgSuccess = 'Error in creating group ' + name              
            html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/group/list/\"></HEAD><body> %s.</body></html>" % msgSuccess
            return HttpResponse(html)
    else:
        form = GroupsForm()    
    return render_to_response('group/addnew.html',locals(),context_instance=RequestContext(request))

@transaction.commit_on_success
def deleteMultiple(request):
    groupNameList = request.REQUEST.get("name_list", "")
    comment = request.REQUEST.get("comment", "deleting")
    printArray = []
    title = "Delete multiple Groups message"
    groupNameArray = groupNameList.split("%%")
    for groupName in groupNameArray:
        ## Get the Group Object
        groupObject = None
        try:
            groupObject = Groups.objects.get(name = groupName)
        except Groups.DoesNotExist:
            printArray.append("Group with Name " + groupName + " could not be found")
            continue
        ## Check whether this group has any allocations namely top level, project and group allocations
        tpAllocNames = TopLevelAllocation.objects.filter(group__name__iexact = groupName).values_list('name', flat=True).order_by('name')
        prAllocNames = ProjectAllocation.objects.filter(group__name__iexact = groupName).values_list('name', flat=True).order_by('name')
        grAllocNames = GroupAllocation.objects.filter(group__name__iexact = groupName).values_list('name', flat=True).order_by('name')

        ## If yes, prepare an alert message and return to user
        tpAllocNamesList = list(tpAllocNames)
        prAllocNamesList = list(prAllocNames)
        grAllocNamesList = list(grAllocNames)
        finalMessage = ''
        if len(tpAllocNamesList) > 0:
            finalMessage = finalMessage + "Top Level Allocation Names: " + (', '.join(tpAllocNamesList)) + " "
        if len(prAllocNamesList) > 0:
            finalMessage = finalMessage + "Project Allocation Names: " + (', '.join(prAllocNamesList)) + " "
        if len(grAllocNamesList) > 0:
            finalMessage = finalMessage + "Group Allocation Names: " + (', '.join(grAllocNamesList)) + " "
        if not finalMessage == '':
            finalMessage = "Group with Name " + groupName + " Could not be deleted because it is being used in " + " " + finalMessage
            printArray.append(finalMessage)
        else:
            ## If there are no allocations for this group, then delete it and return a success message to the user       
            oldGroupObj = copy.copy(groupObject)    
            groupObject.delete()
            addLog(request,groupName,comment,oldGroupObj,None,'group','delete',False)  
            printArray.append("Group with Name " + groupName + " deleted successfully ")
    return render_to_response('base/deleteMultipleMsg.html',locals(),context_instance=RequestContext(request))



def listall(request):
    deleteDict = {}
    groups = request.META.get('ADFS_GROUP','')
    egroupsList = groups.split(';') ;
    groupsList = Groups.objects.all().order_by('name')
    showMultiDeleteOption = False
    numManaged=0
    for grpObj in groupsList:
        deleteItem = isUserAllowedToUpdateOrDeleteGroup(grpObj.name,egroupsList)
        if deleteItem:
            showMultiDeleteOption = True
            numManaged  +=1
        deleteDict[grpObj.name] = deleteItem 

    return render_to_response('group/listall.html',locals(),context_instance=RequestContext(request))

@transaction.commit_manually
def delete(request):
    groupName = request.REQUEST.get("name", "")
    comment = request.REQUEST.get("comment", "deleting")
    redirectURL = '/cloudman/message/?msg='
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    ## Allow only if the user has either cloudman resource manager privileges
    ## or user has membership of the administrative egroup selected for this group
    if not isUserAllowedToUpdateOrDeleteGroup(groupName,groupsList):
        message = "You neither have membership of administrative group of Group " + groupName + " nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to Delete Group";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)
   ## Get the Group Object
    groupObject = None
    try:
       groupObject = Groups.objects.get(name=groupName)
    except Groups.DoesNotExist:
       failureMessage = "Group with Name " + groupName + " could not be found"
       return HttpResponseRedirect(redirectURL+failureMessage)

    ## Check whether this group has any allocations namely top level, project and group allocations
    tpAllocNames = TopLevelAllocation.objects.filter(group__name__iexact = groupName).values_list('name', flat=True).order_by('name')
    prAllocNames = ProjectAllocation.objects.filter(group__name__iexact = groupName).values_list('name', flat=True).order_by('name')
    grAllocNames = GroupAllocation.objects.filter(group__name__iexact = groupName).values_list('name', flat=True).order_by('name')

    ## If yes, prepare an alert message and return to user 
    finalMessage = ''
    tpAllocNamesList = list(tpAllocNames)
    prAllocNamesList = list(prAllocNames)
    grAllocNamesList = list(grAllocNames)
    if len(tpAllocNamesList) > 0:
       finalMessage = finalMessage + "Top Level Allocation Names: " + (', '.join(tpAllocNamesList)) + "<br/>"
    if len(prAllocNamesList) > 0:
       finalMessage = finalMessage + "Project Allocation Names: " + (', '.join(prAllocNamesList)) + "<br/>"
    if len(grAllocNamesList) > 0:
       finalMessage = finalMessage + "Group Allocation Names: " + (', '.join(grAllocNamesList)) + "<br/>"
    if not finalMessage == '':
       finalMessage = "Group with Name " + groupName + " Could not be deleted because it is being used in " + "<br/>" + finalMessage
       html = "<html><body> %s</body></html>" % finalMessage
       return HttpResponse(html)
    ## If there are no allocations for this group, then delete it and return a success message to the user
    oldGroupObj = copy.copy(groupObject)    
    status = addLog(request,groupName,comment,oldGroupObj,None,'group','delete',False)           
    #delete after writing the LOgs
    groupObject.delete()
    if status:
        transaction.commit()
        message = "Group with Name " + groupName + " deleted successfully "
    else:
        transaction.rollback()
        message = "Error in deleteing Group with Name " + groupName
    
    html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/group/list/\"></HEAD><body> %s.</body></html>" % message
    return HttpResponse(html)
    

def getdetails(request):
    groupName = request.REQUEST.get("name", "")
    redirectURL = '/cloudman/message/?msg='

    ## Get the Group Object
    groupInfo = None
    try:
       groupInfo = Groups.objects.get(name=groupName)
    except Groups.DoesNotExist:
       errorMessage = 'Group with Name ' + groupName + ' does not exists'
       return HttpResponseRedirect(redirectURL + errorMessage)

    ## get the top level, project and group allocation names for which this group has been used
    tpAllocNames = TopLevelAllocation.objects.filter(group__name__iexact = groupName).values_list('name', flat=True).order_by('name')
    prAllocNames = ProjectAllocation.objects.filter(group__name__iexact = groupName).values_list('name', flat=True).order_by('name')
    grAllocNames = GroupAllocation.objects.filter(group__name__iexact = groupName).values_list('name', flat=True).order_by('name')
    object_id = groupInfo.id
    changeLogList = getLog('group',groupName,object_id,None)
    return render_to_response('group/getdetails.html',locals(),context_instance=RequestContext(request))

@transaction.commit_on_success
def update(request):
    groupName = request.REQUEST.get("name", "")
    redirectURL = '/cloudman/message/?msg='
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    ## Allow only if the user has either cloudman resource manager privileges
    ## or user has membership of the administrative egroup selected for this group
    if not isUserAllowedToUpdateOrDeleteGroup(groupName,groupsList):
        message = "You neither have membership of administrative group of Group " + groupName + " nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to Edit Group";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)	
    ## Get the Group Object
    groupObject = None
    try:
        groupObject = Groups.objects.get(name=groupName)
    except Groups.DoesNotExist:
        failureMessage = "Group with Name " + groupName + " could not be found"
        return HttpResponseRedirect(redirectURL+failureMessage)
    oldGroupInfo = getGroupInfo(groupObject)
    ## if the request is through form submission then update the fields, or else return to present an form for update
    if request.method == 'POST':
        ## Existing values
        currName = groupObject.name
        currDescription = groupObject.description
        currAdmin_group = groupObject.admin_group
        ## New Values
        newName = request.REQUEST.get("newname", "")
        newDescription = request.REQUEST.get("description", "")
        newAdmin_group = request.REQUEST.get("admin_group", "")
        comment = request.REQUEST.get("comment", "")
        try:
            validate_name(newName)
            validate_descr(newDescription)
            validate_name(newAdmin_group)
            validate_comment(comment)
        except ValidationError as e:
            message ='Edit Group Form  '+', '.join(e.messages)
            html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/group/list/\"></HEAD><body> %s.</body></html>" % message
            return HttpResponse(html)
        ## update is allowed if atleast one field value has been changed
        if ( (currName == newName) and (currDescription == newDescription) and (currAdmin_group == newAdmin_group) ):
            message = 'No New Value provided for any field to perform Edit Operation. Hence Edit Group ' + groupName + ' aborted'
            return HttpResponseRedirect(redirectURL + message)
        ## if name has been changed, validate it and assign the new value 
        if (currName != newName):
            if (newName == ''):
                errorMsg = 'Group name field cannot be left blank. So Edit Group operation stopped'
                return HttpResponseRedirect(redirectURL + errorMsg)
            groupExists = checkNameIgnoreCase(newName)
            if groupExists:
                msgAlreadyExists = 'Group ' + newName + ' already exists. Hence Edit Group Operation Stopped'
                return HttpResponseRedirect(redirectURL + msgAlreadyExists);
            groupObject.name = newName
        ## if description has been changed, then assign the new value
        if (currDescription != newDescription):
            groupObject.description = newDescription
        ## if administrative egroup has been changed, first check its existence and then assign it if exists.
        egroup = None
        if (currAdmin_group != newAdmin_group):
            if (newAdmin_group == ''):
                errorMsg = 'Admin E-Group field cannot be left blank. So Edit Group operation stopped'
                return HttpResponseRedirect(redirectURL + errorMsg)
            try:
                egroup = Egroups.objects.get(name=newAdmin_group)
            except Egroups.DoesNotExist:
                if not (checkEGroup(newAdmin_group)):
                    errorMessage = 'Selected Admin E-Group ' + newAdmin_group + ' does not exists'
                    return HttpResponseRedirect(redirectURL + errorMessage)
                egroup = Egroups(name=newAdmin_group)
                egroup.save()
            groupObject.admin_group = egroup
        ## Finally, save the changes and return a success message to the user
        groupObject.save()              
        newGroupInfo = getGroupInfo(groupObject)
        objectId = groupObject.id 
        addUpdateLog(request,newName,objectId,comment,oldGroupInfo,newGroupInfo,'group',True)
        message = 'Group ' + groupName + ' Successfully Updated'
        html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/group/list/\"></HEAD><body> %s.</body></html>" % message
        return HttpResponse(html)
    return render_to_response('group/update.html',locals(),context_instance=RequestContext(request))


def getEgroupListNameContainJSON(request):
    mimetype = 'application/javascript'
    namecontain = request.REQUEST.get("namecontain", "")
    try:
        egroupList = getEgroupListNameContain(namecontain)
        data = []
        for egroup in egroupList:
            data.append({'label':egroup})    
    except Exception:
        printStackTrace()
    print data
    jsondata = simplejson.dumps({'egroup':data})
    return HttpResponse(jsondata,mimetype)    


