from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext, loader, Context
from django.shortcuts import render_to_response
from django.conf import settings
from models import GroupAllocation
from django.db import transaction
from models import GroupAllocationMetadata
from models import GroupAllocationAllowedResourceType
from forms import GroupAllocationForm
from models import Groups
from templatetags.filters import displayNone 
from models import TopLevelAllocation
from models import ProjectAllocation
from models import ResourceType
from getCount import getGroupsCount
from getCount import getProjectAllocationsCount
from projectAllocationQueries import isAdminOfAnyProjectAllocation
from projectAllocationQueries import isAdminOfProjectAllocation
from getPrivileges import isSuperUser
from django.db.models import Q
from validator import *
import getConfig
import django
from logQueries import printStackTrace
from matplotlib import font_manager as fm
import simplejson
from commonFunctions import *
from groupQueries import isAdminForGroup
from groupQueries import isAdminOfAnyGroup
from projectAllocationQueries import getstats as prallocgetstats
from settings import GROUP_ALLOC_DEPTH
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import copy

def delUpdateAllowed(groupsList,grpAllocObj):
    try:
        prjAllocName = grpAllocObj.project_allocation.name
    except Exception:
        prjAllocName = ''
    try:
        grpAllocName = grpAllocObj.parent_group_allocation.name
    except Exception:
        grpAllocName = ''    

    if isSuperUser(groupsList):
        return True
    else:
        if isAdminOfProjectAllocation(groupsList,prjAllocName) or isAdminOfGroupAllocation(groupsList,grpAllocName):
            return True
        else:
            return False


def isAdminOfGroupAllocation(adminGroups, grpAllocName):
    if isSuperUser(adminGroups):
        return True
    if len(adminGroups) < 1:
        return False
    try:
        grAllocObject = GroupAllocation.objects.get(name=grpAllocName)
        grAllocGroup = grAllocObject.group.admin_group
        if grAllocGroup  in adminGroups:
            return True
        prjAllocName =''
        if grAllocObject.project_allocation:
            prjAllocName =  grAllocObject.project_allocation.name
        grpAllocName =''
        if grAllocObject.parent_group_allocation:
            grpAllocName =  grAllocObject.parent_group_allocation.name
        else:
            return isAdminOfProjectAllocation(adminGroups,prjAllocName) or isAdminOfGroupAllocation(adminGroups,grpAllocName)
    except Exception:
        return False

'''def isAdminOfGroupAllocation(adminGroups, grpAllocName):
    userIsAdmin = False
    if len(adminGroups) < 1:
        return userIsAdmin
    try:
        grAllocObject = GroupAllocation.objects.get(name=grpAllocName)
        grAllocGroup = grAllocObject.group.admin_group
        for oneGroup in adminGroups:
            if oneGroup == grAllocGroup:
                userIsAdmin = True
                break
    except Exception:
        userIsAdmin = False
    return userIsAdmin
'''
def isAdminOfAnyGroupAllocation(adminGroups):
    userIsAdmin = False
    if len(adminGroups) < 1:
        return userIsAdmin
    qset = Q(group__admin_group__exact=adminGroups[0])
    if len(adminGroups) > 1:
        for group in adminGroups[1:]:
            qset = qset | Q(group__admin_group__exact=group)
    if (GroupAllocation.objects.filter(qset)).exists():
        userIsAdmin = True
    return userIsAdmin

def checkNameIgnoreCase(allocName):
    allocNameExists = False
    if GroupAllocation.objects.filter(name__iexact=allocName).exists():
        allocNameExists = True
    return allocNameExists

@transaction.commit_on_success
def addnew(request):
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';')
    egroupList = groups.split(';') ;
    ## Group allocation is possible, if the following things are available
    ## atleast one group
    ## atleast one project allocation
    groupsCount = getGroupsCount()
    if groupsCount <= 0:
        message = "No Groups Defined. First create Groups and then try to define Group Allocation";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)
    projectAllocationsCount = getProjectAllocationsCount()
    if projectAllocationsCount <= 0:
        message = "No Project Allocations Defined. First create Project Level Allocations and then try to define Group Allocation";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)
    ## If the request is through form submission, then try to create the allocation
    ## or else return a form for creating new group allocation
    if request.method == 'POST':
        attr_name_array = request.POST.getlist('attribute_name');
        attr_value_array = request.POST.getlist('attribute_value');
        #Create dictionary of attr_name and attr_value with attr_name:attr_value as key:value pairs
        attr_list = createDictFromList(attr_name_array,attr_value_array)
        redirectURL = '/cloudman/message/?msg='
        ## check the specified name uniquess for group allocation
        allocName = request.REQUEST.get("name", "")
        ## Get the remaining fields input values
        groupName = request.REQUEST.get("group", "")
        projectAllocationName = request.REQUEST.get("project_allocation", "")
        parentGroupAllocationName = request.REQUEST.get("parent_group_allocation", "")
        hepspec = request.REQUEST.get("hepspecs", "")
        memory = request.REQUEST.get("memory", "")
        storage = request.REQUEST.get("storage", "")
        bandwidth = request.REQUEST.get("bandwidth", "")
        selAllocResourceTypes = request.REQUEST.getlist("selresourcetype")
        comment = request.REQUEST.get("comment", "")
        try:
            validate_name(allocName)
            validate_name(groupName)
            validate_name(projectAllocationName)
            validate_name(parentGroupAllocationName)
            validate_float(hepspec)
            validate_float(memory)
            validate_float(storage)
            validate_float(bandwidth)
            validate_comment(comment)
            validate_attr(attr_list)
        except ValidationError as e:
            msg = 'Add Group Allocation Form  '+', '.join(e.messages)
            html = "<html><head><meta HTTP-EQUIV=\"REFRESH\" content=\"5; url=/cloudman/groupallocation/list/\"></head><body> %s.</body></html>" % msg
            return HttpResponse(html)

        allocNameExists = checkNameIgnoreCase(allocName)
        if allocNameExists:
            msgAlreadyExists = 'Allocation Name ' + allocName + ' already exists. Hence New Group Allocation Creation Stopped'
            return HttpResponseRedirect(redirectURL + msgAlreadyExists)
        ## allocation is allowed only if user has
        ## either cloudman resource manager privileges
        ## or 
        ## membership of admin group of selected group and 
        ## membership of admin group of project allocation or parent group allocation (whichever is selected)
        userIsSuperUser = isSuperUser(groupsList)
        if not userIsSuperUser:
#            if not (isAdminForGroup(groupName, groupsList)):
#                message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Group of the Group " + groupName + ". Hence you are not authorized to create Group Allocation";
#                html = "<html><body> %s.</body></html>" % message
#                return HttpResponse(html)
            if parentGroupAllocationName == '':
                if not (isAdminOfProjectAllocation(groupsList, projectAllocationName)):
                    message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Group of the Project for which the Project Allocation " + projectAllocationName + " is created . Hence you are not authorized to create Group Allocation";
                    html = "<html><body> %s.</body></html>" % message
                    return HttpResponse(html)
            else:
                if not (isAdminOfGroupAllocation(groupsList, parentGroupAllocationName)):
                    message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Groups of the Group for which the Parent Group Allocation " + parentGroupAllocationName + " is created. Hence you are not authorized to create Group Allocation";
                    html = "<html><body> %s.</body></html>" % message
                    return HttpResponse(html)

        ## validate the resource parameters values
        errorMessage = checkAttributeValues(hepspec, memory, storage, bandwidth)
        if (errorMessage != ''):
            return HttpResponseRedirect(redirectURL + errorMessage)

        if hepspec == '':
            hepspec = None
        else:
            hepspec = round((float(hepspec)), 3)
        if memory == '':
            memory = None
        else:
            memory = round((float(memory)), 3)
        if storage == '':
            storage = None
        else:
            storage = round((float(storage)), 3)
        if bandwidth == '':
            bandwidth = None
        else:
            bandwidth = round((float(bandwidth)), 3)
        ## Get the Group Object
        groupObject = None
        try:
            groupObject = Groups.objects.get(name=groupName)
        except Groups.DoesNotExist:
            errorMessage = 'Groups Name ' + groupName + ' does not exists'
            return HttpResponseRedirect(redirectURL + errorMessage)

        projectAllocationObject = None
        parentGroupAllocationObject = None   
        ## Get the project allocation and parent group allocation (whichever is selected)
        if parentGroupAllocationName == '':
            try: 
                projectAllocationObject = ProjectAllocation.objects.get(name=projectAllocationName)
            except TopLevelAllocation.DoesNotExist:
                errorMessage = 'Project Allocation Name ' + projectAllocationName + ' does not exists'
                return HttpResponseRedirect(redirectURL + errorMessage)
        else:
            try:
                parentGroupAllocationObject = GroupAllocation.objects.get(name=parentGroupAllocationName)
            except GroupAllocation.DoesNotExist:
                errorMessage = 'Parent Group Allocation Name ' + parentGroupAllocationName + ' does not exists'
                return HttpResponseRedirect(redirectURL + errorMessage)
 
        level = int(groupAllocLevel(projectAllocationObject,parentGroupAllocationObject))        
        if  level <= 0:
            errorMessage = 'You are exceeding the Defined depth for the Allowed Group Allocation Level under The Project' 
            transaction.rollback()
            return HttpResponseRedirect(redirectURL + errorMessage)
        ## initialize three dict, one each for total, free and used fraction resource parameter values
        ## get these values from the selected project allocation or parent group allocation
        totResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
        freeResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
        usedFraction = {'hepspec': 0, 'memory': 0, 'storage': 0, 'bandwidth': 0 } 

        if parentGroupAllocationName == '':
            ## get the resource information of the selected project allocation
            errorMessage = prallocgetstats(projectAllocationName, totResources, freeResources, usedFraction)
            if errorMessage != '':
                return HttpResponseRedirect(redirectURL + errorMessage)
        else:
            ## get the resource information of the selected parent group allocation
            errorMessage = getstats(parentGroupAllocationName, totResources, freeResources, usedFraction)
            if errorMessage != '':
                return HttpResponseRedirect(redirectURL + errorMessage)
          
        ## check whether the selected resource parameter values are available in the selected
        ## project allocation or parent group allocation
        if (hepspec > freeResources['hepspec']):
            message = "The Requested Hepspec value is greater than the available Hepspec"
            return HttpResponseRedirect(redirectURL + message)

        if (memory > freeResources['memory']):
            message = "The Requested Memory value is greater than the available Memory"
            return HttpResponseRedirect(redirectURL + message)

        if (storage > freeResources['storage']):
            message = "The Requested Storage value is greater than the available Storage"
            return HttpResponseRedirect(redirectURL + message)

        if (bandwidth > freeResources['bandwidth']):
            message = "The Requested Bandwidth value is greater than the available Bandwidth"
            return HttpResponseRedirect(redirectURL + message)

        #Make Sure no attribute_name or attribute_value is empty
        ##Check if all the attribute name are distinct for this first convert all the attribute name to uppercase and 
        ## After converting to uppercase check for duplicate in the array
        if checkForEmptyStrInList(attr_name_array):
            errorMessage = 'Attribute Name Cannot be Empty. Hence Add Group Allocation Operation Stopped'
            return HttpResponseRedirect(redirectURL + errorMessage)
        if checkForEmptyStrInList(attr_value_array):
            errorMessage = 'Attribute Value Cannot be Empty. Hence Add Group Allocation Operation Stopped'
            return HttpResponseRedirect(redirectURL + errorMessage)
        ##Check if all the attribute name are distinct for this first convert all the attribute name to uppercase and 
        ## After converting to uppercase check for duplicate in the array
        new_attr_name_array = [x.upper() for x in attr_name_array];
        if len(new_attr_name_array) != len( set(new_attr_name_array) ):
            errorMessage = 'Duplicate values for the Attribute Name. Hence Add Group Allocation Operation Stopped'
            return HttpResponseRedirect(redirectURL + errorMessage)

        ## create the group allocation with all the input values
        finalMessage = ''
        try:
            gralloc = GroupAllocation(name = allocName, group = groupObject, project_allocation = projectAllocationObject, parent_group_allocation = parentGroupAllocationObject, hepspec = hepspec, memory = memory, storage = storage, bandwidth = bandwidth)
            gralloc.save()
            alloc=GroupAllocation.objects.get(name=allocName)
            for attr_name,attr_value  in attr_list.items():
                gralloc_metadata = GroupAllocationMetadata(attribute = attr_name,value = attr_value,group_allocation = alloc)
                gralloc_metadata.save()


        except Exception, err:
            finalMessage = "Error in Creating Group Allocation , reason : %s" % str(err)
            transaction.rollback()
            html = "<html><body> %s.</body></html>" % finalMessage
            return HttpResponse(html)

        if parentGroupAllocationName == '':            
            finalMessage = "Group Allocation Created Successfully with Name %s using Project Allocation %s for Group %s with %s Hepspec, %s Memory, %s Storage, %s Bandwidth " % (allocName, projectAllocationName, groupName, (str(hepspec)), (str(memory)), (str(storage)), (str(bandwidth)))
        else:
            finalMessage = "Group Allocation Created Successfully with Name %s using Parent Group Allocation %s for Group %s with %s Hepspec, %s Memory, %s Storage, %s Bandwidth " % (allocName, parentGroupAllocationName, groupName, (str(hepspec)), (str(memory)), (str(storage)), (str(bandwidth)))
        finalMessage += "<br/><br/>"; 

        ## create the group allocation allowed resource types
        gralloc = None
        try:
            gralloc = GroupAllocation.objects.get(name = allocName)
            finalMessage += " Assigning Allowed Resource Types to Allocation : <br/>"
            for i in range(len(selAllocResourceTypes)):
                selResourceType = selAllocResourceTypes[i]
                finalMessage += " Resource Type Name: " + selResourceType + "<br/>"
                resourceTypeRecord = ResourceType.objects.get(name = selResourceType)
                allowedResourceType = GroupAllocationAllowedResourceType(group_allocation = gralloc, resource_type = resourceTypeRecord)
                allowedResourceType.save()
        except Exception, err:
            finalMessage += "Exception arised while Assigning Allowed Resources Types for the Group Allocation, reason : %s " %str(err)
            finalMessage += "<br/> Hence Group Allocation Creation Stopped Here (and also record cleared completely)."
            gralloc.delete()
            transaction.rollback()
            html = "<html><body> %s.</body></html>" % finalMessage
            return HttpResponse(html)

        ##Add the LOg
        oldgroupAllocObj = GroupAllocation.objects.get(name = allocName)
        if not addLog(request,allocName,comment,oldgroupAllocObj,None,'groupallocation','add',True):
            transaction.rollback()
        ## finally, return a successful message to the user
        finalMessage += "<br/> Group Allocation Creation Successfully Completed";
        html = "<html><head><meta HTTP-EQUIV=\"REFRESH\" content=\"5; url=/cloudman/groupallocation/list/\"></head><body> %s.</body></html>" % finalMessage
        return HttpResponse(html)

    ## form post request if condition ends here - start of else block
    else:
        ## form is displayed if user has
        ## either cloudman resource manager privileges
        ## or 
        ## membership of admin group of any group and 
        ## membership of admin group of any project allocation or any parent group allocation
        userIsSuperUser = isSuperUser(groupsList)
        if not userIsSuperUser:
#            if not (isAdminOfAnyGroup(groupsList)):
#                message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Group of any Group. Hence you are not authorized to create Group Allocation";
#                html = "<html><body> %s.</body></html>" % message
#                return HttpResponse(html)
            userIsProjectAdmin = isAdminOfAnyProjectAllocation(groupsList)
            userIsGroupAdmin = isAdminOfAnyGroupAllocation(groupsList)
            if not (userIsProjectAdmin or userIsGroupAdmin):
                message = "You neither have cloudman resource manager privileges nor membership of any Group for which a Project Allocation is defined or membership of any Group or which a Group Allocation is defined. Hence you are not authorized to create Group Allocation";
                html = "<html><body> %s.</body></html>" % message
                return HttpResponse(html)
        ##Get all the details for preparing a form to be displayed 
        prAllocNames = []
        grAllocNames = []
        if userIsSuperUser: 
            prAllocNames = ProjectAllocation.objects.values_list('name', flat=True)
            grAllocObjList = GroupAllocation.objects.all()
            grAllocNames =[]
            for grAllocObj in grAllocObjList:
                level = int(groupAllocLevel(grAllocObj.project_allocation,grAllocObj.parent_group_allocation)) - 1
                if level >0:
                    grAllocNames.append(grAllocObj.name) 
        else:
            projectQset = Q(project__admin_group__exact=groupsList[0])
            groupQset = Q(group__admin_group__exact=groupsList[0])
            if len(groupsList) > 1:
                for group in groupsList[1:]:
                    projectQset = projectQset | Q(project__admin_group__exact=group)
                    groupQset = groupQset | Q(group__admin_group__exact=group)
            #prAllocNames = ProjectAllocation.objects.filter(projectQset).values_list('name', flat=True)
            prAllocNames = ProjectAllocation.objects.filter(groupQset|projectQset).values_list('name', flat=True)
            #grAllocNames = GroupAllocation.objects.filter(groupQset).values_list('name', flat=True)
            grAllocNamesList = GroupAllocation.objects.values_list('name', flat=True)
            grAllocNames = []
            for allocName in grAllocNamesList:
                if isAdminOfGroupAllocation(groupsList, allocName):
                    grAllocNames.append(allocName) 
        
        grNames = Groups.objects.values_list('name', flat=True)
        ## return to the template for rendering the form
        return render_to_response('groupallocation/addnew.html',locals(),context_instance=RequestContext(request))

def listall(request):
    groupsAllocationList = GroupAllocation.objects.select_related('group','parent_group_allocation','project_allocation').all().order_by('name')
    deleteDict = {}
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    showMultiDeleteOption = False
    numManaged=0
    for grpAllocObj in groupsAllocationList:
        deleteItem = delUpdateAllowed(groupsList,grpAllocObj)
        if deleteItem:
            showMultiDeleteOption = True
            numManaged +=1
        deleteDict[grpAllocObj.name] = deleteItem 

    return render_to_response('groupallocation/listall.html',locals(),context_instance=RequestContext(request))

def getresourceinfo(request):
        redirectURL = '/cloudman/message/?msg='

    ## if the request is through ajax, then dump the data in JSON format
    #if request.is_ajax():
        format = 'json'
        mimetype = 'application/javascript'
        groupAllocationName = request.REQUEST.get("name", "")
     
        ## initialize three dict, one each for total, free and used fraction resource parameter values
        totResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
        freeResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
        usedFraction = {'hepspec': 0, 'memory': 0, 'storage': 0, 'bandwidth': 0 }

        ## call this function to calculate the above defined values
        errorMessage = getstats(groupAllocationName, totResources, freeResources, usedFraction)
        if errorMessage != '':
           nulldata = []
           data = simplejson.dumps(nulldata)
           return HttpResponse(data,mimetype)

        ## frame an object with all the resource parameter info for this group allocation
        ## the information include, what is total available, how much is free and percentage of already allocated
        groupAllocationInfo = [{"pk": groupAllocationName, "model": "cloudman.groupallocationinfo", "fields": {"tothepspecs": totResources['hepspec'], "totmemory": totResources['memory'], "totstorage": totResources['storage'], "totbandwidth": totResources['bandwidth']}}, {"model": "cloudman.groupallocationfreeinfo", "fields": {"hepspecsfree": freeResources['hepspec'], "memoryfree": freeResources['memory'], "storagefree": freeResources['storage'], "bandwidthfree": freeResources['bandwidth']}}, {"model": "cloudman.groupallocationusedinfoper", "fields":{"hepspecsfraction": usedFraction['hepspec'], "memoryfraction": usedFraction['memory'], "storagefraction": usedFraction['storage'], "bandwidthfraction": usedFraction['bandwidth']}}]

       ## Get the allowed resource types for this group allocation
        groupAllocationResourceTypeObjects = GroupAllocationAllowedResourceType.objects.filter(group_allocation__name=groupAllocationName)
        groupAllocationResourceTypeList = list(groupAllocationResourceTypeObjects)
        resourceTypeIds = []
        resourceTypeObjects = None
        for oneRow in groupAllocationResourceTypeObjects:
            resourceTypeIds.append(oneRow.resource_type.id)
        if len(resourceTypeIds) > 0:
           resourceTypeObjects = ResourceType.objects.filter(id__in=resourceTypeIds)

        for oneRT in resourceTypeObjects:
            groupAllocationInfo.append({"pk": oneRT.id, "model": "cloudman.resourcetype", "fields": {"name": oneRT.name, "resource_class": oneRT.resource_class, "hepspecs": oneRT.hepspecs, "memory": oneRT.memory, "storage": oneRT.storage, "bandwidth": oneRT.bandwidth}})

        ## finally dump the data into json and return 
        data = simplejson.dumps(groupAllocationInfo)
        return HttpResponse(data,mimetype)
    # If you want to prevent non AJAX calls
    #else:
    #    return HttpResponse(status=400)

def getstats(grAllocName, totResources, freeResources, usedFraction):
    errorMessage = ''
    ## Get the Group Allocation Object
    groupAllocationObject = None
    try:
       groupAllocationObject = GroupAllocation.objects.get(name=grAllocName)
    except GroupAllocation.DoesNotExist:
       errorMessage = 'Group Allocation Name ' + grAllocName + ' does not exists'
       return errorMessage

    ## Assign the resource parameter values to separate variables
    totHepSpecs = groupAllocationObject.hepspec
    totMemory = groupAllocationObject.memory
    totStorage = groupAllocationObject.storage
    totBandwidth = groupAllocationObject.bandwidth
    totResources['hepspec'] = totHepSpecs
    totResources['memory'] = totMemory
    totResources['storage'] = totStorage
    totResources['bandwidth'] = totBandwidth

    ## Get all the group allocations whose parent is this group allocation
    groupAllocationObjects = GroupAllocation.objects.filter(parent_group_allocation__name = grAllocName)

    ## Find how much of this group allocation is already allocated. Start with none is allocated
    hepSpecsFree = totHepSpecs
    memoryFree = totMemory
    storageFree = totStorage
    bandwidthFree = totBandwidth

    for oneGroup in groupAllocationObjects:
       hepspec = oneGroup.hepspec
       memory = oneGroup.memory
       storage = oneGroup.storage
       bandwidth = oneGroup.bandwidth

       if (hepspec != None):
          hepSpecsFree = hepSpecsFree - hepspec

       if (memory != None):
           memoryFree = memoryFree - memory

       if (storage != None):
           storageFree = storageFree - storage

       if (bandwidth != None):
           bandwidthFree = bandwidthFree - bandwidth

    freeResources['hepspec'] = hepSpecsFree
    freeResources['memory'] = memoryFree
    freeResources['storage'] = storageFree
    freeResources['bandwidth'] = bandwidthFree
    
    ## Calculate percentage of each resource parameter already allocated, initialize them to 0 first
    hepSpecsFraction = 0
    memoryFraction = 0
    storageFraction = 0
    bandwidthFraction = 0

    if totHepSpecs != None:
        if totHepSpecs > 0:
            hepSpecsFraction = round((((totHepSpecs - hepSpecsFree)/totHepSpecs) * 100), 3)

    if totMemory != None:
        if totMemory > 0:
            memoryFraction = round((((totMemory - memoryFree)/totMemory) * 100), 3)

    if totStorage != None:
        if totStorage > 0:
            storageFraction = round((((totStorage - storageFree)/totStorage) * 100), 3)

    if totBandwidth != None:
        if totBandwidth > 0:
            bandwidthFraction = round((((totBandwidth - bandwidthFree)/totBandwidth) * 100), 3)

    usedFraction['hepspec'] = hepSpecsFraction
    usedFraction['memory'] = memoryFraction
    usedFraction['storage'] = storageFraction
    usedFraction['bandwidth'] = bandwidthFraction

    return errorMessage

@transaction.commit_on_success
def delete(request):
    grAllocName = request.REQUEST.get("name", "")
    comment = request.REQUEST.get("comment", "deleting")
    redirectURL = '/cloudman/message/?msg='
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    ## Get the Group Allocation Object
    grAllocObject = None
    try:
        grAllocObject = GroupAllocation.objects.get(name=grAllocName)
    except GroupAllocation.DoesNotExist:
        failureMessage = "Group Allocation with Name " + grAllocName + " could not be found"
        return HttpResponseRedirect(redirectURL+failureMessage)
    ## update is allowed only if the user has either
    ## cloudman resource manager privileges
    ## or has membership of the admin group of the group for which this allocation is done
    if not delUpdateAllowed(groupsList,grAllocObject):
        message = "Neither cloudman resource manager privileges nor membership of the Administrative E-Group of the Group " + grAllocObject.group.name + " for the Project allocation or parent group allocation for this Group Allocation. Hence not authorized to delete Group Allocation";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)
        
#    userIsSuperUser = isSuperUser(groupsList)
#    if not userIsSuperUser:
#        if not (isAdminForGroup(grAllocObject.group.name, groupsList)):
#            message = "Neither cloudman resource manager privileges nor membership of the Administrative E-Group of the Group " + grAllocObject.group.name + " for which this Group Allocation is assigned. Hence not authorized to delete Group Allocation";
#            html = "<html><body> %s.</body></html>" % message
#            return HttpResponse(html)

    ## check if any group allocations have been defined using this allocation as its parent
    grAllocNames = GroupAllocation.objects.filter(parent_group_allocation__name__iexact = grAllocName).values_list('name', flat=True).order_by('name')

    ## if yes, then alert the user and stop the delete operation 
    finalMessage = ''
    grAllocNamesList = list(grAllocNames)
    if len(grAllocNamesList) > 0:
        finalMessage = finalMessage + "Group Allocation Names: " + (', '.join(grAllocNamesList)) + "<br/>"
    if not finalMessage == '':
        finalMessage = "Group Allocation with Name " + grAllocName + " Could not be deleted because it is being used as Parent Group in " + "<br/>" + finalMessage
        html = "<html><body> %s</body></html>" % finalMessage
        transaction.rollback()
        return HttpResponse(html)

    #Add the Log
    oldGroupAllocObj = grAllocObject
    addLog(request,grAllocName,comment,oldGroupAllocObj,None,'groupallocation','delete',False)
    ## if no allocations, then first delete the allowed resource types and then the allocation itself
    GroupAllocationAllowedResourceType.objects.filter(group_allocation__name__iexact = grAllocName).delete()
    grAllocObject.delete()
    ## return a success message to the user
    message = "Group Allocation with Name " + grAllocName + " deleted successfully "
    html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/groupallocation/list/\"></HEAD><body> %s.</body></html>" % message
    return HttpResponse(html)

@transaction.commit_on_success
def deleteMultiple(request):
    grAllocNameList = request.REQUEST.get("name_list", "")
    comment = request.REQUEST.get("comment", "deleting")
    printArray = []	
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    title = "Delete multiple Group Allocation message"
    grAllocNameArray = grAllocNameList.split("%%")
    for grAllocName in grAllocNameArray:
        ## Get the Group Allocation Object
        grAllocObject = None
        try:
            grAllocObject = GroupAllocation.objects.get(name=grAllocName)
        except GroupAllocation.DoesNotExist:
            printArray.append( "Group Allocation with Name " + grAllocName + " could not be found")
            continue
        ## delete is allowed only if the user has either
        ## cloudman resource manager privileges
        ## or has membership of the admin group of the group for which this allocation is done
        if not delUpdateAllowed(groupsList,grAllocObject):
                message = "Neither cloudman resource manager privileges nor membership of the Administrative E-Group of the Group " + grAllocObject.group.name + "for the ProjectAllocation or ParentGroupAllocation for this Group Allocation. Hence not authorized to delete Group Allocation";
                printArray.append(message)
                continue

#        userIsSuperUser = isSuperUser(groupsList)
#        if not userIsSuperUser:
#            if not (isAdminForGroup(grAllocObject.group.name, groupsList)):
#                message = "Neither cloudman resource manager privileges nor membership of the Administrative E-Group of the Group " + grAllocObject.group.name + " for which this Group Allocation is assigned. Hence not authorized to delete Group Allocation";
#                printArray.append(message)
#                continue
        ## check if any group allocations have been defined using this allocation as its parent
        grAllocNames = GroupAllocation.objects.filter(parent_group_allocation__name__iexact = grAllocName).values_list('name', flat=True).order_by('name')
        ## if yes, then alert the user and stop the delete operation
        finalMessage = ''
        grAllocNamesList = list(grAllocNames)
        if len(grAllocNamesList) > 0:
            finalMessage = finalMessage + "Group Allocation Names: " + (', '.join(grAllocNamesList)) + "  "
        if not finalMessage == '':
            finalMessage = "Group Allocation with Name " + grAllocName + " Could not be deleted because it is being used as Parent Group in " + "  " + finalMessage
            printArray.append(finalMessage)
        else:
            #write the Log
            addLog(request,grAllocName,comment,grAllocObject,None,'groupallocation','delete',False)
            ## if no allocations, then first delete the allowed resource types and then the allocation itself
            GroupAllocationAllowedResourceType.objects.filter(group_allocation__name__iexact = grAllocName).delete()
            grAllocObject.delete()
            printArray.append("Group Allocation with Name " + grAllocName + " deleted successfully ")
    return render_to_response('base/deleteMultipleMsg.html',locals(),context_instance=RequestContext(request))


def getdetails(request):
    redirectURL = '/cloudman/message/?msg='
    allocName = request.REQUEST.get("name", "")
    ## Get the Group Allocation Object
    allocInfo = None
    try:
        allocInfo = GroupAllocation.objects.select_related('project_allocation','group','parent_group_allocation').get(name=allocName)
    except GroupAllocation.DoesNotExist:
        errorMessage = 'Group Allocation with Name ' + allocName + ' does not exists'
        return HttpResponseRedirect(redirectURL + errorMessage)
    ##Get all the group allocation metadata for this 
    grAllocMetadata = GroupAllocationMetadata.objects.filter(group_allocation__name__iexact = allocName).values('attribute','value').order_by('attribute')
    ## Get the allowed resource types of this allocation
    allowedResourceTypesList = GroupAllocationAllowedResourceType.objects.select_related('resource_type').filter(group_allocation = allocInfo).order_by('resource_type__name')
    ## Get all the group allocations done using this allocation as its parent
    groupAllocationsInfo = GroupAllocation.objects.select_related('group').filter(parent_group_allocation__name=allocName).order_by('name')
    object_id = allocInfo.id
    changeLogList = getLog('groupallocation',allocName,object_id,None)
    return render_to_response('groupallocation/getdetails.html',locals(),context_instance=RequestContext(request))

@transaction.commit_on_success
def update(request):
    grAllocName = request.REQUEST.get("name", "")
    redirectURL = '/cloudman/message/?msg='
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;

    ## Get the Group Allocation Object 
    grAllocObject = None
    try:
        grAllocObject = GroupAllocation.objects.get(name=grAllocName)
    except GroupAllocation.DoesNotExist:
        failureMessage = "Group Allocation with Name " + grAllocName + " could not be found"
        return HttpResponseRedirect(redirectURL+failureMessage)
    ##Get all the group allocation metadata for this 
    oldgrpAllocInfo = getGroupAllocationInfo(grAllocObject)
    Metadata = GroupAllocationMetadata.objects.filter(group_allocation__name__iexact = grAllocName).values('attribute','value').order_by('attribute')
    old_attr_list = {}
    for oneRow in Metadata:
        attribute = oneRow['attribute']
        value = oneRow['value']
        old_attr_list[attribute] = value

    ## update is allowed only if the user has either
    ## cloudman resource manager privileges
    ## or has membership of the admin group of the group for which this allocation is done
    if not delUpdateAllowed(groupsList,grAllocObject):
        message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Group of the Group " + grAllocObject.group.name + "for the Project Allocation or ParentGroupAllocation for this Group Allocation. Hence you are not authorized to update Group Allocation";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)

#    userIsSuperUser = isSuperUser(groupsList)
#    if not userIsSuperUser:
#        if not (isAdminForGroup(grAllocObject.group.name, groupsList)):
#            message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Group of the Group " + grAllocObject.group.name + " for which this Group Allocation is assigned. Hence you are not authorized to update Group Allocation";
#            html = "<html><body> %s.</body></html>" % message
#            return HttpResponse(html)
    ## Get the allowed resource types of this group allocation 
    grAllocRTList = GroupAllocationAllowedResourceType.objects.filter(group_allocation__name=grAllocName).values_list('resource_type__name', flat=True)
    ## if the request is through POST form submission, then try to update by assinging the changed values
    ## else prepare an update form and return 
    if request.method == 'POST':
        ## Existing values
        currName = grAllocObject.name
        currHepSpec = grAllocObject.hepspec
        currMemory = grAllocObject.memory
        currStorage = grAllocObject.storage
        currBandwidth = grAllocObject.bandwidth
        oldgrAllocObject = copy.copy(grAllocObject)
        ## New Values
        newName = request.REQUEST.get("newname", "")
        newHepSpec = request.REQUEST.get("hepspec", "")
        newMemory = request.REQUEST.get("memory", "")
        newStorage = request.REQUEST.get("storage", "")
        newBandwidth = request.REQUEST.get("bandwidth", "")
        newRTList = request.REQUEST.getlist("grallocallowedrt")
        comment = request.REQUEST.get("comment","")
        scale = request.REQUEST.get("scale")
        storagescale = request.REQUEST.get("storagescale")
        ## New values for Project metadata
        new_attr_name_list = request.POST.getlist('attribute_name');
        new_attr_value_list = request.POST.getlist('attribute_value');
        #Create dictionary of attr_name and attr_value with attr_name:attr_value as key:value pairs
        attr_list = createDictFromList(new_attr_name_list,new_attr_value_list)
        try:
            validate_name(newName)
            validate_float(newHepSpec)
            validate_float(newMemory)
            validate_float(newStorage)
            validate_float(newBandwidth)
            validate_comment(comment)
            validate_attr(attr_list)
        except ValidationError as e:
            msg = 'Edit Group Allocation Form  '+', '.join(e.messages)
            html = "<html><head><meta HTTP-EQUIV=\"REFRESH\" content=\"5; url=/cloudman/groupallocation/list/\"></head><body> %s.</body></html>" % msg
            return HttpResponse(html)
        ## validate the new resource parameter values
        errorMsg = checkAttributeValues(newHepSpec, newMemory, newStorage, newBandwidth)
        if (errorMsg != ''):
            return HttpResponseRedirect(redirectURL + errorMsg)
        ## check whether any existing resource type is de-selected or any new one selected
        rtNotChanged = True;
        for newRt in newRTList:
            if not newRt in grAllocRTList:
                rtNotChanged = False
        for oldRt in grAllocRTList:
            if not oldRt in newRTList:
                rtNotChanged = False
        ## if the value is an empty string, assign NULL or else round off to 3 decimal digits 
        if (newHepSpec == ''):
            newHepSpec = None
        else:
            newHepSpec = round((float(newHepSpec)), 3)
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
        ## check whether atleast one field is changed
        if ( (currName == newName) and (currHepSpec == newHepSpec) and (currMemory == newMemory) and (currStorage == newStorage) and (currBandwidth == newBandwidth) and (rtNotChanged) ):
            if checkForDictionaryEquality(attr_list,old_attr_list):
                message = 'No New Value provided for any field to perform Edit Operation. Hence Edit Group Allocation ' + grAllocName + ' aborted'
                return HttpResponseRedirect(redirectURL + message)

        ## if name is changed, validate it and then assign the new name
        if (currName != newName):
            if (newName == ''):
                errorMsg = 'Name name field cannot be left blank. So Edit Group Allocation operation stopped'
                return HttpResponseRedirect(redirectURL + errorMsg)
            nameExists = checkNameIgnoreCase(newName)
            if nameExists:
                msgAlreadyExists = 'Group Allocation ' + newName + ' already exists. Hence Edit Group Allocation Operation Stopped'
                return HttpResponseRedirect(redirectURL + msgAlreadyExists);
            grAllocObject.name = newName

        #Make Sure no attribute_name or attribute_value is empty
        if checkForEmptyStrInList(new_attr_name_list):
            errorMessage = 'Attribute Name Cannot be Empty. Hence Update Group Allocation Stopped'
            return HttpResponseRedirect(redirectURL + errorMessage)
        if checkForEmptyStrInList(new_attr_value_list):
            errorMessage = 'Attribute Value Cannot be Empty. Hence Update Group Allocation Stopped'
            return HttpResponseRedirect(redirectURL + errorMessage)
        ##Make Sure that all the attribute_name are distinct
        if checkForDuplicateStrInList(new_attr_name_list):
            errorMessage = 'Duplicate values for the Attribute Name. Hence Update Group Allocation Stopped'
            return HttpResponseRedirect(redirectURL + errorMessage)

        ## if any of the resource parameter values changed
        if ( (currHepSpec != newHepSpec) or (currMemory != newMemory) or (currStorage != newStorage) or (currBandwidth != newBandwidth) ):
           ## initialize three dict, one each for total, free and used fraction resource parameter values
           ## get these values from the selected project allocation or parent group allocation
           totResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
           freeResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
           usedFraction = {'hepspec': 0, 'memory': 0, 'storage': 0, 'bandwidth': 0 }

           parentStr = ''
           if (grAllocObject.project_allocation):
              parentStr = ' Project Allocation ' + grAllocObject.project_allocation.name
           else:
              parentStr = ' Parent Group Allocation ' + grAllocObject.parent_group_allocation.name

           if (grAllocObject.project_allocation):
              ## get the resource information of the selected project allocation
              errorMessage = prallocgetstats(grAllocObject.project_allocation.name, totResources, freeResources, usedFraction)
              if errorMessage != '':
                 return HttpResponseRedirect(redirectURL + errorMessage)
           else:
              ## get the resource information of the selected parent group allocation
              errorMessage = getstats(grAllocObject.parent_group_allocation.name, totResources, freeResources, usedFraction)
              if errorMessage != '':
                 return HttpResponseRedirect(redirectURL + errorMessage)

           ## calculate how much of project allocated resoures are used for group allocations
           grUsedResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}          
           calGroupUsedResources(grUsedResources, currName)

           ## check whether any changes to the exist resource values can be met using the project or parent group allocation
           ## Also, check these changes had any effect on the other group allocations which has used this as their parent
           errorMessage = ''
           if (currHepSpec != newHepSpec):
              if newHepSpec == None:
                 if (grUsedResources['hepspec'] > 0):
                    errorMessage = errorMessage + 'Setting the Hepspec UNDEFINED is not possible as there exists alloted Hepspec for other Group allocations using this allocation as Parent '
              else:
                 if currHepSpec == None:
                    if totResources['hepspec'] == None:
                       errorMessage = errorMessage + 'The requested Hepspec ' + str(newHepSpec) + ' cannot be fulfilled as Hepspec is UNDEFINED for ' +  parentStr
                    else:
                       if ( freeResources['hepspec'] < newHepSpec ):
                           errorMessage = errorMessage + 'The requested Hepspec ' + str(newHepSpec) + ' is more than the free Hepspec available from ' +  parentStr
                 else: 
                    if ( (freeResources['hepspec'] + currHepSpec) < newHepSpec ):
                       errorMessage = errorMessage + 'The requested Hepspec ' + str(newHepSpec) + ' is more than the free Hepspec available from ' +  parentStr
                 if ((scale is None) and (newHepSpec < grUsedResources['hepspec'])):
                    errorMessage = errorMessage + 'The requested Hepspec ' + str(newHepSpec) + ' is less than the already alloted Hepspec for other Group Allocations using this allocation as Parent '

           if (currMemory != newMemory):
              if newMemory == None:
                 if (grUsedResources['memory'] > 0):
                    errorMessage = errorMessage + 'Setting the Memory UNDEFINED is not possible as there exists alloted Memory for other Group allocations using this allocation as Parent '
              else:
                 if currMemory == None:
                    if totResources['memory'] == None:
                       errorMessage = errorMessage + 'The requested Memory ' + str(newMemory) + ' cannot be fulfilled as Memory is UNDEFINED for ' +  parentStr
                    else:
                       if ( freeResources['memory'] < newMemory ):
                           errorMessage = errorMessage + 'The requested Memory ' + str(newMemory) + ' is more than the free Memory available from ' +  parentStr
                 else:
                    if ( (freeResources['memory'] + currMemory) < newMemory ):
                       errorMessage = errorMessage + 'The requested Memory ' + str(newMemory) + ' is more than the free Memory available from ' +  parentStr
                 if (newMemory < grUsedResources['memory']):
                    errorMessage = errorMessage + 'The requested Memory ' + str(newMemory) + ' is less than the already alloted Memory for other Group Allocations using this allocation as Parent '

           if (currStorage != newStorage):
              if newStorage == None:
                 if (grUsedResources['storage'] > 0):
                    errorMessage = errorMessage + 'Setting the Storage UNDEFINED is not possible as there exists alloted Storage for other Group allocations using this allocation as Parent '
              else:
                 if currStorage == None:
                    if totResources['storage'] == None:
                       errorMessage = errorMessage + 'The requested Storage ' + str(newStorage) + ' cannot be fulfilled as Storage is UNDEFINED for ' +  parentStr
                    else:
                       if ( freeResources['storage'] < newStorage ):
                          errorMessage = errorMessage + 'The requested Storage ' + str(newStorage) + ' is more than the free Storage available from ' +  parentStr
                 else:
                    if ( (freeResources['storage'] + currStorage) < newStorage ):
                       errorMessage = errorMessage + 'The requested Storage ' + str(newStorage) + ' is more than the free Storage available from ' +  parentStr
                 if ((storagescale is None)) and (newStorage < grUsedResources['storage']):
                    errorMessage = errorMessage + 'The requested Storage ' + str(newStorage) + ' is less than the already alloted Storage for other Group allocations using this allocation as Parent '

           if (currBandwidth != newBandwidth):
              if newBandwidth == None:
                 if (grUsedResources['bandwidth'] > 0):
                    errorMessage = errorMessage + 'Setting the Bandwidth UNDEFINED is not possible as there exists alloted Bandwidth for other Group allocations using this allocation as Parent '
              else:
                 if currBandwidth == None:
                    if totResources['bandwidth'] == None:
                       errorMessage = errorMessage + 'The requested Bandwidth ' + str(newBandwidth) + ' cannot be fulfilled as Bandwidth is UNDEFINED for ' +  parentStr
                    else:
                       if ( freeResources['bandwidth'] < newBandwidth ):
                          errorMessage = errorMessage + 'The requested Bandwidth ' + str(newBandwidth) + ' is more than the free Bandwidth available from ' +  parentStr
                 else:
                    if ( (freeResources['bandwidth'] + currBandwidth) < newBandwidth ):
                       errorMessage = errorMessage + 'The requested Bandwidth ' + str(newBandwidth) + ' is more than the free Bandwidth available from ' +  parentStr
                 if (newBandwidth < grUsedResources['bandwidth']):
                    errorMessage = errorMessage + 'The requested Bandwidth ' + str(newBandwidth) + ' is less than the already alloted Bandwidth for other Group allocations using this allocation as Parent '

           if errorMessage != '':
               errorMessage = errorMessage + ' Hence Edit Group Allocation Operation Stopped'
               return HttpResponseRedirect(redirectURL + errorMessage)

           ## assign the new values to the project allocation
           ## if any of the resource values becomes NULL, then to keep the consistency, make all group allocations
           ## resource value UNDEFINED i.e NULL for that parameter
           if (currHepSpec != newHepSpec):
               if newHepSpec == None:
                  GroupAllocation.objects.filter(parent_group_allocation__name = currName).update(hepspec=None)
               grAllocObject.hepspec = newHepSpec

           if (currMemory != newMemory):
               if newMemory == None:
                  GroupAllocation.objects.filter(parent_group_allocation__name = currName).update(memory=None)
               grAllocObject.memory = newMemory

           if (currStorage != newStorage):
               if newStorage == None:
                  GroupAllocation.objects.filter(parent_group_allocation__name = currName).update(storage=None)
               grAllocObject.storage = newStorage

           if (currBandwidth != newBandwidth):
               if newBandwidth == None:
                  GroupAllocation.objects.filter(parent_group_allocation__name = currName).update(bandwidth=None)
               grAllocObject.bandwidth = newBandwidth

        ## save all the changes
        if scale is not None:
            scalefactor = getScaleFactor(newHepSpec,currHepSpec)
            scaleSubGroupAllocationHepSpec(currName,scalefactor,scale=True)    
        if storagescale is not None:
            scalefactor = getScaleFactor(newStorage,currStorage)
            scaleSubGroupAllocationStorage(currName,scalefactor,scale=True)    
        grAllocObject.save()
        try:
            GroupAllocationMetadata.objects.filter(group_allocation = grAllocObject).delete() 
            for attr_name,attr_value  in attr_list.items():
                gralloc_metadata = GroupAllocationMetadata(attribute = attr_name,value = attr_value,group_allocation = grAllocObject)
                gralloc_metadata.save()
        except Exception :
            transaction.rollback()
            printStackTrace()

        ## if the allowed resource type list is changed, then add newly selected or delete the un-selected ones
        errorMessage = ''
        if not rtNotChanged:
           for newRt in newRTList:
             if not newRt in grAllocRTList:
                try:
                   rtObject = ResourceType.objects.get(name=newRt)
                   grrt = GroupAllocationAllowedResourceType(group_allocation=grAllocObject, resource_type=rtObject)
                   grrt.save()
                except ResourceType.DoesNotExist:
                   transaction.rollback()
                   errorMessage = errorMessage + 'No Record Found for Resource Type ' + newRt + '. Hence Group Allocation Allowed Resource Types Edit Failed. '

           for oldRt in grAllocRTList:
             if not oldRt in newRTList:
                try:                   
                   grrt = GroupAllocationAllowedResourceType.objects.get(resource_type__name=oldRt, group_allocation__name=grAllocName)
                   grrt.delete()
                except GroupAllocationAllowedResourceType.DoesNotExist:
                   transaction.rollback()
                   errorMessage = errorMessage + 'No Record Found for Group Allocation Allowed Resource Type ' + oldRt + '. Hence Group Allocation Allowed Resource Types Edit Failed. '

        #Write The Log
        newgrpAllocInfo = getGroupAllocationInfo(grAllocObject)
        objectId = grAllocObject.id
        addUpdateLog(request,newName,objectId,comment,oldgrpAllocInfo,newgrpAllocInfo,'groupallocation',True)        
        ## finally, return a successful message to the user
        message = 'Group Allocation ' + grAllocName + ' Successfully Updated'
        html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/groupallocation/list/\"></HEAD><body> %s <br/> %s</body></html>" % (message, errorMessage)
        transaction.commit()
        return HttpResponse(html)

    totalHepSpec = None
    totalMemory = None
    totalStorage = None
    totalBandwidth = None
    hepSpecPer = None
    memoryPer = None
    storagePer = None
    bandwidthPer = None

    if (grAllocObject.project_allocation):
       totalHepSpec = grAllocObject.project_allocation.hepspec
       totalMemory = grAllocObject.project_allocation.memory
       totalStorage = grAllocObject.project_allocation.storage
       totalBandwidth = grAllocObject.project_allocation.bandwidth
       if (grAllocObject.hepspec != None ):
          if (grAllocObject.hepspec > 0):
             hepSpecPer = round(((grAllocObject.hepspec/grAllocObject.project_allocation.hepspec) * 100), 3)
          else:
             hepSpecPer = 0
       if (grAllocObject.memory != None ):
          if (grAllocObject.memory > 0):
              memoryPer = round(((grAllocObject.memory/grAllocObject.project_allocation.memory) * 100), 3)
          else:
              memoryPer = 0
       if (grAllocObject.storage != None ):
          if (grAllocObject.storage > 0) :
             storagePer = round(((grAllocObject.storage/grAllocObject.project_allocation.storage) * 100), 3)
          else:
             storagePer = 0
       if (grAllocObject.bandwidth != None ):
          if (grAllocObject.bandwidth > 0):
             bandwidthPer = round(((grAllocObject.bandwidth/grAllocObject.top_level_allocation.bandwidth) * 100), 3)
          else:
             bandwidthPer = 0
    else:
       totalHepSpec = grAllocObject.parent_group_allocation.hepspec
       totalMemory = grAllocObject.parent_group_allocation.memory
       totalStorage = grAllocObject.parent_group_allocation.storage
       totalBandwidth = grAllocObject.parent_group_allocation.bandwidth
       if (grAllocObject.hepspec != None ):
          if (grAllocObject.hepspec > 0):
             hepSpecPer = round(((grAllocObject.hepspec/grAllocObject.parent_group_allocation.hepspec) * 100), 3)
          else:
             hepSpecPer = 0
       if (grAllocObject.memory != None ):
          if (grAllocObject.memory > 0):
              memoryPer = round(((grAllocObject.memory/grAllocObject.parent_group_allocation.memory) * 100), 3)
          else:
              memoryPer = 0
       if (grAllocObject.storage != None ):
          if (grAllocObject.storage > 0) :
             storagePer = round(((grAllocObject.storage/grAllocObject.parent_group_allocation.storage) * 100), 3)
          else:
             storagePer = 0
       if (grAllocObject.bandwidth != None ):
          if (grAllocObject.bandwidth > 0):
             bandwidthPer = round(((grAllocObject.bandwidth/grAllocObject.parent_group_allocation.bandwidth) * 100), 3)
          else:
             bandwidthPer = 0
    
    ## return to present the update form
    return render_to_response('groupallocation/update.html',locals(),context_instance=RequestContext(request))

def calGroupUsedResources(grUsedResources, currName):
    ## calculate how much of project allocated resources are already allocated to groups
    usedHepSpec = 0
    usedMemory = 0
    usedStorage = 0
    usedBandwidth = 0

    allGrAllocObjects = GroupAllocation.objects.filter(parent_group_allocation__name = currName)
    for oneObject in allGrAllocObjects:
        if (oneObject.hepspec != None):
           usedHepSpec = usedHepSpec + oneObject.hepspec
        if (oneObject.memory != None):
           usedMemory = usedMemory + oneObject.memory
        if (oneObject.storage != None):
           usedStorage = usedStorage + oneObject.storage
        if (oneObject.bandwidth != None):
           usedBandwidth = usedBandwidth + oneObject.bandwidth

    grUsedResources['hepspec'] = round(usedHepSpec, 3)
    grUsedResources['memory'] = round(usedMemory, 3)
    grUsedResources['storage'] = round(usedStorage, 3)
    grUsedResources['bandwidth'] = round(usedBandwidth, 3)


## The following functions are not being used as of now
def getallowedresourcetypes(request):
    #if request.is_ajax():
       allocName = request.REQUEST.get("groupallocationname", "")
       format = 'json'
       mimetype = 'application/javascript'

       rtInfo = []
       groupAllocationResourceTypeObjects = GroupAllocationAllowedResourceType.objects.filter(group_allocation__name=allocName)
       groupAllocationResourceTypeList = list(groupAllocationResourceTypeObjects)
       resourceTypeIds = []
       resourceTypeObjects = None
       for oneRow in groupAllocationResourceTypeObjects:
           resourceTypeIds.append(oneRow.resource_type.id)
       if len(resourceTypeIds) > 0:
          resourceTypeObjects = ResourceType.objects.filter(id__in=resourceTypeIds)

       for oneRT in resourceTypeObjects:
           rtInfo.append({"pk": oneRT.id, "model": "cloudman.groupallocationallowedresourcetype", "fields": {"name": oneRT.name, "resource_class": oneRT.resource_class, "hepspecs": oneRT.hepspecs, "memory": oneRT.memory, "storage": oneRT.storage, "bandwidth": oneRT.bandwidth}})

       data = simplejson.dumps(rtInfo)
       return HttpResponse(data,mimetype)
    #else:
    #   return HttpResponse(status=400)

def updateAllocationHierarchy(currName, grAllocObject, newHepSpec, newMemory, newStorage, newBandwidth):
    allGrAllocObjects = GroupAllocation.objects.filter(parent_group_allocation__name = currName)
    oldHepSpec = grAllocObject.hepspec
    oldMemory = grAllocObject.memory
    oldStorage = grAllocObject.storage
    oldBandwidth = grAllocObject.bandwidth
    for oneObject in allGrAllocObjects:
        if oneObject.hepspec_fraction != None:
           if oneObject.hepspec_fraction == 0:
              if newHepSpec == None:
                 oneObject.hepspec_fraction = None
           else:
              currHepSpec = round(((oneObject.hepspec_fraction * oldHepSpec)/100), 3)
              oneObject.hepspec_fraction = round(((currHepSpec/newHepSpec) * 100), 3)
        if oneObject.memory_fraction != None:
           if oneObject.memory_fraction == 0:
              if newMemory == None:
                 oneObject.memory_fraction = None
           else:
              currMemory = round(((oneObject.memory_fraction * oldMemory)/100), 3)
              oneObject.memory_fraction = round(((currMemory/newMemory) * 100), 3)
        if oneObject.storage_fraction != None:
           if oneObject.storage_fraction == 0:
              if newStorage == None:
                 oneObject.storage_fraction = None
           else:
              currStorage = round(((oneObject.storage_fraction * oldStorage)/100), 3)
              oneObject.storage_fraction = round(((currStorage/newStorage) * 100), 3)
        if oneObject.bandwidth_fraction != None:
           if oneObject.bandwidth_fraction == 0:
              if newBandwidth == None:
                 oneObject.bandwidth_fraction = None
           else:
              currBandwidth = round(((oneObject.bandwidth_fraction * oldBandwidth)/100), 3)
              oneObject.bandwidth_fraction = round(((currBandwidth/newBandwidth) * 100), 3)
        oneObject.save()


def getGroupAllocInGroupAllocation(request):
    mimetype = 'application/javascript'
    grpAllocName = request.REQUEST.get("name", "")
    try:
        grpAllocList = GroupAllocation.objects.filter(parent_group_allocation__name = grpAllocName).order_by('name')
        groupAllocationInfo = []
        for grpAlloc in grpAllocList:
            name  =  grpAlloc.name
            group = grpAlloc.group.name
            hepspec = displayNone(grpAlloc.hepspec)
            memory = displayNone(grpAlloc.memory)
            storage = displayNone(grpAlloc.storage)
            bandwidth = displayNone(grpAlloc.bandwidth)
            groupAllocationInfo.append({'name':name,'group':group,'hepspec':hepspec,'memory':memory,
                                          'storage':storage,'bandwidth':bandwidth})    
    except Exception:
        printStackTrace()
    data = simplejson.dumps(groupAllocationInfo)
    return HttpResponse(data,mimetype)    

def calParentTotResources(parentTotalResources, grAllocObject):
    totHepSpec = None
    totMemory = None
    totStorage = None
    totBandwidth = None
    if (grAllocObject.project_allocation):
        ## This means the group has been allocated resources directly from the project
        if (grAllocObject.project_allocation.hepspec_fraction != None):
           totHepSpec = ( grAllocObject.project_allocation.hepspec_fraction * grAllocObject.project_allocation.top_level_allocation.hepspec)/100
        if (grAllocObject.project_allocation.memory_fraction != None):
           totMemory = ( grAllocObject.project_allocation.memory_fraction * grAllocObject.project_allocation.top_level_allocation.memory )/100
        if (grAllocObject.project_allocation.storage_fraction != None):
           totStorage = ( grAllocObject.project_allocation.storage_fraction * grAllocObject.project_allocation.top_level_allocation.storage )/100
        if (grAllocObject.project_allocation.bandwidth_fraction != None):
           totBandwidth = ( grAllocObject.project_allocation.bandwidth_fraction * grAllocObject.project_allocation.top_level_allocation.bandwidth )/100
    else:
        ## This means a hierarchy has been formed, where this group is assigned resources from another group (which might have been allocated resources from another group etc..)
        hepSpecsFractionList = []
        memoryFractionList = []
        storageFractionList = []
        bandwidthFractionList = []
        while True:
           newGroupAllocationName = grAllocObject.parent_group_allocation.name
           groupAllocationObject = None
           try:
               groupAllocationObject = GroupAllocation.objects.get(name=newGroupAllocationName)
           except GroupAllocation.DoesNotExist:
               errorMessage = 'Group Allocation Name ' + newGroupAllocationName + ' does not exists'
               return errorMessage
           if (groupAllocationObject.project_allocation):
               break;
        if groupAllocationObject.hepspec_fraction != None:
           totHepSpec = ( groupAllocationObject.hepspec_fraction * (((groupAllocationObject.project_allocation.hepspec_fraction) * (groupAllocationObject.project_allocation.top_level_allocation.hepspec))/100) )/100
           for oneValue in reversed(hepSpecsFractionList):
              if oneValue == None:
                 totHepSpec = None
                 break
              totHepSpec = (oneValue * totHepSpec)/100

        if groupAllocationObject.memory_fraction != None:
            totMemory = ( groupAllocationObject.memory_fraction * (((groupAllocationObject.project_allocation.memory_fraction) * (groupAllocationObject.project_allocation.top_level_allocation.memory))/100) )/100
            for oneValue in reversed(memoryFractionList):
               if oneValue == None:
                  totMemory = None
                  break
               totMemory = (oneValue * totMemory)/100

        if groupAllocationObject.storage_fraction != None:
            totStorage = ( groupAllocationObject.storage_fraction * (((groupAllocationObject.project_allocation.storage_fraction) * (groupAllocationObject.project_allocation.top_level_allocation.storage))/100) )/100
            for oneValue in reversed(storageFractionList):
               if (oneValue == None):
                  totStorage = None
                  break
               totStorage = (oneValue * totStorage)/100

        if groupAllocationObject.bandwidth_fraction != None:
            totBandwidth = ( groupAllocationObject.bandwidth_fraction * (((groupAllocationObject.project_allocation.bandwidth_fraction) * (groupAllocationObject.project_allocation.top_level_allocation.bandwidth))/100) )/100
            for oneValue in reversed(bandwidthFractionList):
               if (oneValue == None):
                  totBandwidth = None
                  break
               totBandwidth = (oneValue * totBandwidth)/100

    if (totHepSpec != None):
        parentTotalResources['hepspec'] = round(totHepSpec, 3)
    if (totMemory != None):
        parentTotalResources['memory'] = round(totMemory, 3)
    if (totStorage != None):
        parentTotalResources['storage'] = round(totStorage, 3)
    if (totBandwidth != None):
        parentTotalResources['bandwidth'] = round(totBandwidth, 3)

def calGrAllocResources(grAllocObject):
    if (grAllocObject.project_allocation):
        ## This means the group has been allocated resources directly from the project
        if (grAllocObject.hepspec_fraction != None):
           grAllocObject.hepspec = ( grAllocObject.hepspec_fraction * (((grAllocObject.project_allocation.hepspec_fraction) * (grAllocObject.project_allocation.top_level_allocation.hepspec))/100) )/100
        if (grAllocObject.memory_fraction != None):
           grAllocObject.memory = ( grAllocObject.memory_fraction * (((grAllocObject.project_allocation.memory_fraction) * (grAllocObject.project_allocation.top_level_allocation.memory))/100) )/100
        if (grAllocObject.storage_fraction != None):
           grAllocObject.storage = ( grAllocObject.storage_fraction * (((grAllocObject.project_allocation.storage_fraction) * (grAllocObject.project_allocation.top_level_allocation.storage))/100) )/100
        if (grAllocObject.bandwidth_fraction != None):
           grAllocObject.bandwidth = ( grAllocObject.bandwidth_fraction * (((grAllocObject.project_allocation.bandwidth_fraction) * (grAllocObject.project_allocation.top_level_allocation.bandwidth))/100) )/100
    else:
        ## This means a hierarchy has been formed, where this group is assigned resources from another group (which might have been allocated resources from another group etc..)
        hepSpecsFractionList = []
        memoryFractionList = []
        storageFractionList = []
        bandwidthFractionList = []
        while True:
           hepSpecsFractionList.append(grAllocObject.hepspec_fraction)
           memoryFractionList.append(grAllocObject.memory_fraction)
           storageFractionList.append(grAllocObject.storage_fraction)
           bandwidthFractionList.append(grAllocObject.bandwidth_fraction)
           newGroupAllocationName = grAllocObject.parent_group_allocation.name
           groupAllocationObject = None
           try:
               groupAllocationObject = GroupAllocation.objects.get(name=newGroupAllocationName)
           except GroupAllocation.DoesNotExist:
               errorMessage = 'Group Allocation Name ' + newGroupAllocationName + ' does not exists'
               return errorMessage
           if (groupAllocationObject.project_allocation):
               break;
        if ( (groupAllocationObject.hepspec_fraction != None) and (groupAllocationObject.project_allocation.hepspec_fraction != None) and (groupAllocationObject.project_allocation.top_level_allocation.hepspec != None) ):
           grAllocObject.hepspec = ( groupAllocationObject.hepspec_fraction * (((groupAllocationObject.project_allocation.hepspec_fraction) * (groupAllocationObject.project_allocation.top_level_allocation.hepspec))/100) )/100
           for oneValue in reversed(hepSpecsFractionList):
              if oneValue == None:
                 grAllocObject.hepspec = None
                 break
              grAllocObject.hepspec = (oneValue * grAllocObject.hepspec)/100

        if ( (groupAllocationObject.memory_fraction != None) and (groupAllocationObject.project_allocation.memory_fraction != None) and (groupAllocationObject.project_allocation.top_level_allocation.memory != None) ):
            grAllocObject.memory = ( groupAllocationObject.memory_fraction * (((groupAllocationObject.project_allocation.memory_fraction) * (groupAllocationObject.project_allocation.top_level_allocation.memory))/100) )/100
            for oneValue in reversed(memoryFractionList):
               if oneValue == None:
                  grAllocObject.memory = None
                  break
               grAllocObject.memory = (oneValue * grAllocObject.memory)/100

        if ( (groupAllocationObject.storage_fraction != None) and (groupAllocationObject.project_allocation.storage_fraction != None) and (groupAllocationObject.project_allocation.top_level_allocation.storage != None) ):
            grAllocObject.storage = ( groupAllocationObject.storage_fraction * (((groupAllocationObject.project_allocation.storage_fraction) * (groupAllocationObject.project_allocation.top_level_allocation.storage))/100) )/100
            for oneValue in reversed(storageFractionList):
               if (oneValue == None):
                  grAllocObject.storage = None
                  break
               grAllocObject.storage = (oneValue * grAllocObject.storage)/100

        if ( (groupAllocationObject.bandwidth_fraction != None) and (groupAllocationObject.project_allocation.bandwidth_fraction != None) and (groupAllocationObject.project_allocation.top_level_allocation.bandwidth != None) ):
            grAllocObject.bandwidth = ( groupAllocationObject.bandwidth_fraction * (((groupAllocationObject.project_allocation.bandwidth_fraction) * (groupAllocationObject.project_allocation.top_level_allocation.bandwidth))/100) )/100
            for oneValue in reversed(bandwidthFractionList):
               if (oneValue == None):
                  grAllocObject.bandwidth = None
                  break
               grAllocObject.bandwidth = (oneValue * grAllocObject.bandwidth)/100

    if (grAllocObject.hepspec != None):
        temp = round(grAllocObject.hepspec, 3)
        grAllocObject.hepspec = temp
    if (grAllocObject.memory != None):
        temp1 = round(grAllocObject.memory, 3)
        grAllocObject.memory = temp1
    if (grAllocObject.storage != None):
        temp2 = round(grAllocObject.storage, 3)
        grAllocObject.storage = temp2
    if (grAllocObject.bandwidth != None):
        temp3 = round(grAllocObject.bandwidth, 3)
        grAllocObject.bandwidth = temp3

def calParentUsedResources(parentUsedResources, grAllocObject):
    totalResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
    calParentTotResources(totalResources, grAllocObject)

    usedHepSpec = 0
    usedMemory = 0
    usedStorage = 0
    usedBandwidth = 0

    allGrAllocObjects = None
    if (grAllocObject.project_allocation):
        ## This means the group has been allocated resources directly from the project
        allGrAllocObjects = GroupAllocation.objects.filter(project_allocation__name = grAllocObject.project_allocation.name)
    else:
        allGrAllocObjects = GroupAllocation.objects.filter(parent_group_allocation__name = grAllocObject.parent_group_allocation.name)
    for oneObject in allGrAllocObjects:
        if (oneObject.hepspec_fraction != None):
           usedHepSpec = usedHepSpec + ( oneObject.hepspec_fraction * totalResources['hepspec'])/100
        if (oneObject.memory_fraction != None):
           usedMemory = usedMemory + ( oneObject.memory_fraction * totalResources['memory'] )/100
        if (oneObject.storage_fraction != None):
           usedStorage = usedStorage + ( oneObject.storage_fraction * totalResources['storage'] )/100
        if (oneObject.bandwidth_fraction != None):
           usedBandwidth = usedBandwidth + ( oneObject.bandwidth_fraction * totalResources['bandwidth'] )/100

    parentUsedResources['hepspec'] = round(usedHepSpec, 3)
    parentUsedResources['memory'] = round(usedMemory, 3)
    parentUsedResources['storage'] = round(usedStorage, 3)
    parentUsedResources['bandwidth'] = round(usedBandwidth, 3)
