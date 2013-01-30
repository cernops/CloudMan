from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from models import ResourceType
from django.db import transaction
from forms import ResourceTypeForm
from models import ZoneAllowedResourceType,TopLevelAllocationAllowedResourceType,ProjectAllocationAllowedResourceType
from models import GroupAllocationAllowedResourceType
from validator import *
import simplejson
from django.core import serializers
from getPrivileges import isSuperUser
from commonFunctions import addLog,getLog,getResourceTypeInfo,checkAttributeValues,addUpdateLog,printQuery
def checkNameIgnoreCase(resourceTypeName):
    nameExists = False
    if ResourceType.objects.filter(name__iexact=resourceTypeName).exists():
        nameExists = True
    return nameExists

def validateParameters1(rtName, resourceClass, hepspecs,memory, storage, bandwidth):
    errorMessage = ''
    if ( (rtName == None) or (rtName == '') ):
        errorMessage = 'Resource Type Name field cannot be blank. ';
    if ( (resourceClass == None) or (resourceClass == '') ):
        errorMessage = errorMessage + 'Resource Class field cannot be blank. ';
    errorMessage = errorMessage + checkAttributeValues(hepspec, memory, storage, bandwidth)
    return errorMessage

@transaction.commit_on_success
def addnew(request):
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    userIsSuperUser = isSuperUser(groupsList)
    ## Check if the User has cloudman resource manager privileges
    if not userIsSuperUser:
        message = "You don't have cloudman resource manager privileges. Hence you are not authorized to add new Resource Type";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)
    ## If the call is due to form submission, then get all the values and add the new resource type, else display the form
    if request.method == 'POST': 
        form = ResourceTypeForm(request.POST)
        if form.is_valid():
            redirectURL = '/cloudman/message/?msg=' 
            ## Get all the values of the form submitted through POST method 
            rtName = form.cleaned_data['name']
            resourceClass = form.cleaned_data['resource_class']
            hepspecs= form.cleaned_data['hepspecs']
            memory = form.cleaned_data['memory']
            storage = form.cleaned_data['storage']
            bandwidth = form.cleaned_data['bandwidth']
            comment = form.cleaned_data['comment']
            reqParam = False
            ## check if name exists
            nameExists = checkNameIgnoreCase(rtName)
            if nameExists:
                msgAlreadyExists = 'Resource Type ' + rtName + ' already exists. Hence Add Resource Type Operation Stopped'
                return HttpResponseRedirect(redirectURL + msgAlreadyExists)
            if hepspecs :
                hepspecs = round((float(hepspecs)), 3)
                reqParam = True
            if memory :
                memory = round((float(memory)), 3)
            if storage :
                storage = round((float(storage)), 3)
                reqParam = True
            if bandwidth :
                bandwidth = round((float(bandwidth)), 3)
            if (not reqParam):
                errorMsg = 'Either of CPU or Storage Capacity needs to be defined. Hence Add Resource Type Operation Stopped'
                return HttpResponseRedirect(redirectURL + errorMsg);
            rtObj = ResourceType(name=rtName, resource_class=resourceClass, hepspecs=hepspecs, memory=memory, storage=storage, bandwidth=bandwidth)
            rtObj.save()
            ## Return the success message and redirect to list template in 4 seconds
            rtObj = ResourceType.objects.get(name = rtName)
            if addLog(request,rtName,comment,rtObj,None,'resourcetype','add',True):
                transaction.commit()
                msgSuccess = 'New Resource Type ' + rtName  + ' added successfully'
            else:
                transaction.rollback()
                msgSuccess = 'Error in Adding Resource Type ' + rtName
            html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/resourcetype/list/\"></HEAD><body> %s.</body></html>" % msgSuccess
            return HttpResponse(html)
    else:
        form = ResourceTypeForm()
    return render_to_response('resourcetype/new.html',locals(),context_instance=RequestContext(request))

def listall(request):
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    userIsSuperUser = isSuperUser(groupsList)
    resourceTypesList = ResourceType.objects.all().order_by('name') 
    return render_to_response('resourcetype/listall.html',locals(),context_instance=RequestContext(request))    
    
@transaction.commit_on_success
def delete(request):
    rtName = request.REQUEST.get("name", "")
    redirectURL = '/cloudman/message/?msg='
    comment = request.REQUEST.get("comment", "deleting")
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    userIsSuperUser = isSuperUser(groupsList)
    ## Check - Logged in user has administrative privileges
    if not userIsSuperUser:
        message = "You don't have cloudman resource manager privileges. Hence you are not authorized to delete Resource Type " + rtName;
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)
    ## Get the Resource Type Object
    resourceTypeObject = None
    try:
        resourceTypeObject = ResourceType.objects.get(name=rtName)
    except ResourceType.DoesNotExist:
        failureMessage = "Resource Type with Name " + rtName + " could not be found"
        return HttpResponseRedirect(redirectURL+failureMessage)
    ## Before Deleting, check whether this resource type is used for zones, top level allocations, project allocations and group allocations
    zoneNames = ZoneAllowedResourceType.objects.filter(resource_type__name__iexact = rtName).values_list('zone__name', 'zone__region__name').order_by('zone__name')
    tpAllocNames = TopLevelAllocationAllowedResourceType.objects.filter(resource_type__name__iexact = rtName).values_list('top_level_allocation__name', flat=True).order_by('top_level_allocation__name')
    prAllocNames = ProjectAllocationAllowedResourceType.objects.filter(resource_type__name__iexact = rtName).values_list('project_allocation__name', flat=True).order_by('project_allocation__name')
    grAllocNames = GroupAllocationAllowedResourceType.objects.filter(resource_type__name__iexact = rtName).values_list('group_allocation__name', flat=True).order_by('group_allocation__name')
    ## if this resource type is used as specified above, then frame an errorMessage to alert the user
    finalMessage = ''
    zoneNamesList = list(zoneNames)
    tpAllocNamesList = list(tpAllocNames)
    prAllocNamesList = list(prAllocNames)
    grAllocNamesList = list(grAllocNames)
    if len(zoneNamesList) > 0:
        finalMessage = finalMessage + "Zone Names: "
        for i in (range(len(zoneNamesList))):
            if (i == (len(zoneNamesList)-1)):
                finalMessage = finalMessage + zoneNamesList[i][0] + "(Region: " + zoneNamesList[i][1] + ") "
            else:
                finalMessage = finalMessage + zoneNamesList[i][0] + "(Region: " + zoneNamesList[i][1] + "), "
        finalMessage = finalMessage + "<br/>"
    if len(tpAllocNamesList) > 0:
        finalMessage = finalMessage + "Top Level Allocation Names: " + (', '.join(tpAllocNamesList)) + "<br/>"
    if len(prAllocNamesList) > 0: 
        finalMessage = finalMessage + "Project Allocation Names: " + (', '.join(prAllocNamesList)) + "<br/>"
    if len(grAllocNamesList) > 0: 
        finalMessage = finalMessage + "Group Allocation Names: " + (', '.join(grAllocNamesList)) + "<br/>"
    if not finalMessage == '':
        finalMessage = "Resource Type with Name " + rtName + " Could not be deleted because it is being used in " + "<br/>" + finalMessage
        html = "<html><body> %s</body></html>" % finalMessage
        return HttpResponse(html)
    ## if this resource type is not used anywhere, then delete it and return a success message to the user
    status = addLog(request,rtName,comment,resourceTypeObject,None,'resourcetype','delete',False)   
    resourceTypeObject.delete()
    if status:
        message = "Resource Type with Name " + rtName + " deleted successfully "
        transaction.commit()
    else:
        transaction.rollback()
        message = "Error in deleting Resource Type with Name " + rtName     
    html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/resourcetype/list/\"></HEAD><body> %s.</body></html>" % message
    return HttpResponse(html)

def getdetails(request):    
    resourceTypeName = request.REQUEST.get("name", "")
    resourceTypeInfo = None
    redirectURL = '/cloudman/message/?msg='
    ## Get the Resource Type Object with the given name
    try:
        resourceTypeInfo = ResourceType.objects.get(name=resourceTypeName)
    except ResourceType.DoesNotExist:
        errorMessage = 'Resource Type with Name ' + resourceTypeName + ' does not exists'
        return HttpResponseRedirect(redirectURL + errorMessage)
    ## Get all the Zones which are allowed to have this resource type
    zoneNames = ZoneAllowedResourceType.objects.filter(resource_type__name__iexact = resourceTypeName).values_list('zone__name', 'zone__region__name').order_by('zone__name')
    zoneNamesList = list(zoneNames)
    ## Get the Top Level Allocation Names who has this resource type in its allowed category
    tpAllocNames = TopLevelAllocationAllowedResourceType.objects.filter(resource_type__name__iexact = resourceTypeName).values_list('top_level_allocation__name', flat=True).order_by('top_level_allocation__name')
    ## Get the Project Allocation Names whos ha this resource type in its allowed category
    prAllocNames = ProjectAllocationAllowedResourceType.objects.filter(resource_type__name__iexact = resourceTypeName).values_list('project_allocation__name', flat=True).order_by('project_allocation__name')
    ## Get the Group Allocation Names who has this resource type in its allowed category
    grAllocNames = GroupAllocationAllowedResourceType.objects.filter(resource_type__name__iexact = resourceTypeName).values_list('group_allocation__name', flat=True).order_by('group_allocation__name')
    object_id = resourceTypeInfo.id
    changeLogList = getLog('resourcetype',resourceTypeName,object_id,None)
    return render_to_response('resourcetype/getdetails.html',locals(),context_instance=RequestContext(request))

@transaction.commit_on_success
def update(request):
    rtName = request.REQUEST.get("name", "")
    redirectURL = '/cloudman/message/?msg='
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    userIsSuperUser = isSuperUser(groupsList)
    ## Check - Logged in user has administrative privileges
    if not userIsSuperUser:
        message = "You don't have cloudman resource manager privileges. Hence you are not authorized to update Resource Type " + rtName;
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)
    ## Get the Resource Type Object
    resourceTypeObject = None
    try:
        resourceTypeObject = ResourceType.objects.get(name=rtName)
    except ResourceType.DoesNotExist:
        failureMessage = "Resource Type with Name " + rtName + " could not be found"
        return HttpResponseRedirect(redirectURL+failureMessage)
    oldRTInfo = getResourceTypeInfo(resourceTypeObject)
    ## if this is a form submission, then do the update or else display the form for update
    if request.method == 'POST':
        ## Existing values
        currName = resourceTypeObject.name
        currResourceClass = resourceTypeObject.resource_class
        currHepSpecs = resourceTypeObject.hepspecs
        currMemory = resourceTypeObject.memory
        currStorage = resourceTypeObject.storage
        currBandwidth = resourceTypeObject.bandwidth
        ## Get the new values
        newName = request.POST['name']
        newResourceClass = request.POST['resource_class']
        newHepSpecs = request.POST['hepspecs']
        newMemory = request.POST['memory']
        newStorage = request.POST['storage']
        newBandwidth = request.POST['bandwidth']
        comment  = request.POST['comment']
        try:
            validate_name(newName)
            validate_name(newResourceClass)
            validate_float(newHepSpecs)
            validate_float(newMemory)
            validate_float(newStorage)
            validate_float(newBandwidth)
            validate_comment(comment)
        except ValidationError as e:
            message ='Edit Resource Type Form  '+', '.join(e.messages)
            html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/resourcetype/list/\"></HEAD><body> %s.</body></html>" % message
            return HttpResponse(html)
        ## If resource parameters are changed, then validate them
        errorMsg = checkAttributeValues(newHepSpecs, newMemory, newStorage, newBandwidth)
        if (errorMsg != ''):
            return HttpResponseRedirect(redirectURL + errorMsg)
        ## convert empty values for the following fields into None i.e NULL and if not empty, then round off to 3 decimals 
        if (newHepSpecs == ''):
            newHepSpecs = None
        else:
            newHepSpecs = round((float(newHepSpecs)), 3)
        if (newMemory == ''):
            newMemory = None
        else:
            newMemory = round((float(newMemory)), 3)
        if (newStorage == ''):
            newStorage = None
        else:
            newStorage = round((float(newStorage)), 3)
        if (newBandwidth == ''):
            newBandwidth = None
        else:
            newBandwidth = round((float(newBandwidth)), 3)
        ## Check atleast one parameter is changed from its existing value
        if ( (currName == newName) and (currResourceClass == newResourceClass) and (currHepSpecs== newHepSpecs) and (currMemory == newMemory) and (currStorage == newStorage) and (currBandwidth == newBandwidth) ):
            message = 'No New Value provided for any field to perform Edit Operation. Hence Edit Resource Type ' + rtName + ' aborted'
            return HttpResponseRedirect(redirectURL + message)
        ## If name is changed, then validate it and if success, then assign the new name to the object
        if (currName != newName):
            if (newName == ''):
                errorMsg = 'Name field cannot be left blank. So Edit Resource Type operation stopped'
                return HttpResponseRedirect(redirectURL + errorMsg)
            nameExists = checkNameIgnoreCase(newName)
            if nameExists:
                msgAlreadyExists = 'Resource Type ' + newName + ' already exists. Hence Edit Resource Type Operation Stopped'
                return HttpResponseRedirect(redirectURL + msgAlreadyExists);
            resourceTypeObject.name = newName
        ## check the remaining parameters and if changed, then assign to the object
        if (currResourceClass != newResourceClass):
            resourceTypeObject.resource_class = newResourceClass
        if (currHepSpecs != newHepSpecs):
            resourceTypeObject.hepspecs = newHepSpecs
        if (currMemory != newMemory):
            resourceTypeObject.memory = newMemory
        if (currStorage != newStorage):
            resourceTypeObject.storage = newStorage
        if (currBandwidth != newBandwidth):
            resourceTypeObject.bandwidth = newBandwidth
        ## update the object and return the success message to the user
        resourceTypeObject.save()
        newRTInfo = getResourceTypeInfo(resourceTypeObject)
        objectId = resourceTypeObject.id 
        if addUpdateLog(request,newName,objectId,comment,oldRTInfo,newRTInfo,'resourcetype',True):
            message = 'Resource Type ' + rtName + ' Successfully Updated'
            transaction.commit()
        else:
            transaction.rollback()
            message = 'Error in Updating Resource Type ' + rtName
        html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/resourcetype/list/\"></HEAD><body> %s.</body></html>" % message
        return HttpResponse(html)
    ## if it is not form submission, then call the template to display the update form 
    else:
        form = ResourceTypeForm()
        #resourceTypeList=list(resourceTypeObject)
        #json_object=simplejson.dumps(resourceTypeObject)
        return render_to_response('resourcetype/update.html',locals(),context_instance=RequestContext(request))

