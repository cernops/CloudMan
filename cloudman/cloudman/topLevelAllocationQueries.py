from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext, loader, Context
from django.shortcuts import render_to_response
from django.conf import settings
from forms import TopLevelAllocationForm
from models import TopLevelAllocation
from models import ProjectAllocation
from models import TopLevelAllocationByZone
from models import TopLevelAllocationAllowedResourceType
from models import Groups
from models import Region
import pdb
from django.db import transaction
from models import Zone
from templatetags.filters import displayNone 
from validator import *
from models import ResourceType
from getPrivileges import isSuperUser
from getCount import getZoneCount
from getCount import getGroupsCount
from ldapSearch import checkEGroup
from django.db.models import Q
from django.core import serializers
import simplejson
import getConfig
import django
from django.db.models import F
from django.db.models import Sum
from matplotlib import font_manager as fm
from commonFunctions import  *
import copy

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

def checkNameIgnoreCase(allocName):
    allocNameExists = False
    if TopLevelAllocation.objects.filter(name__iexact=allocName).exists():
        allocNameExists = True
    return allocNameExists

def isAdminOfAnyTopLevelAllocation(adminGroups):
    userIsAdmin = False
    if len(adminGroups) < 1:
        return userIsAdmin
    qset = Q(group__admin_group__exact=adminGroups[0])
    if len(adminGroups) > 1:
        for group in adminGroups[1:]:
            qset = qset | Q(group__admin_group__exact=group)
    if (TopLevelAllocation.objects.filter(qset)).exists():
        userIsAdmin = True
    return userIsAdmin

def isAdminOfTopLevelAllocation(adminGroups, topLevelAllocationName):
    userIsAdmin = False
    if len(adminGroups) < 1:
        return userIsAdmin
    try:
        tpAllocObject = TopLevelAllocation.objects.get(name=topLevelAllocationName)
        tpAllocGroup = tpAllocObject.group.admin_group
        for oneGroup in adminGroups:
            if oneGroup == tpAllocGroup:
                userIsAdmin = True
                break
    except Exception:
        userIsAdmin = False
    return userIsAdmin

## Used to test whether the requested amount hepSpecs, memory, storage and bandwidth 
## if still free in the zone
def checkZoneShareAvailability(regionName, zoneName, hepSpecShare, memoryShare, storageShare, bandwidthShare):
    retMessage = ''
    try:
       ## First get the total available resources in the selected zone
       zoneObject = Zone.objects.get(name = zoneName, region__name = regionName)
       zoneTotHepSpecs = 0
       if (zoneObject.hepspecs != None):
          zoneTotHepSpecs = round((zoneObject.hepspecs * zoneObject.hepspec_overcommit), 3)
       zoneTotMemory = 0
       if (zoneObject.memory != None):
          zoneTotMemory = round((zoneObject.memory * zoneObject.memory_overcommit), 3)
       zoneTotStorage = 0
       if (zoneObject.storage != None):
          zoneTotStorage = zoneObject.storage
       zoneTotBandwidth = 0
       if (zoneObject.bandwidth != None):
          zoneTotBandwidth = zoneObject.bandwidth

       ## to calculate un-allocated resource values, start by initializing the free values with the total values
       freeHepSpecs = zoneTotHepSpecs
       freeMemory = zoneTotMemory
       freeStorage = zoneTotStorage
       freeBandwidth = zoneTotBandwidth

       ## Get all the top level allocation where this zone is used
       ## reduce the resource values by the share of each allocation
       zoneUsedObjects = TopLevelAllocationByZone.objects.filter(zone__name = zoneName, zone__region__name=regionName)
       for oneObject in zoneUsedObjects:
          hepSpecsUsed = oneObject.hepspec
          memoryUsed = oneObject.memory
          storageUsed = oneObject.storage
          bandwidthUsed = oneObject.bandwidth
          if (hepSpecsUsed != None):
             freeHepSpecs = freeHepSpecs - hepSpecsUsed
          if (memoryUsed != None):
             freeMemory = freeMemory - memoryUsed
          if (storageUsed != None):
             freeStorage = freeStorage - storageUsed
          if (bandwidthUsed != None):
             freeBandwidth = freeBandwidth - bandwidthUsed
                
       ## now check if the requested values can be met with the un-allocated resources available in this zone
       if (hepSpecShare >= 0):
          if (hepSpecShare > freeHepSpecs) :
             retMessage = "The selected Hepspec : %f for Zone %s in Region %s is greater than the free(un-allocated) Hepspec in this Zone. " % (hepSpecShare, zoneName, regionName)
       if (memoryShare >= 0):
          if (memoryShare > freeMemory) :
             retMessage = retMessage + "The selected Memory : %f for Zone %s in Region %s is greater than the free(un-allocated) Memory in this Zone. " % (memoryShare, zoneName, regionName)
       if (storageShare >= 0):
          if (storageShare > freeStorage) :
             retMessage = retMessage + "The selected Storage : %f for Zone %s in Region %s is greater than the free(un-allocated) Storage in this Zone. " % (storageShare, zoneName, regionName)
       if (bandwidthShare >= 0):
          if (bandwidthShare > freeBandwidth) :
             retMessage = retMessage + "The selected Bandwidth : %f for Zone %s in Region %s is greater than the free(un-allocated) Bandwidth in this Zone. " % (bandwidthShare, zoneName, regionName)

    except Exception, err:
       retMessage = retMessage + "Exception arised while checking the selected allocations, reason : %s" % str(err)

    return retMessage

@transaction.commit_on_success
def addnew(request):
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';')

    ## Top Level Allocation creation is possible, only if there are atleast one zone and one group defined already
    zoneCount = getZoneCount()
    if zoneCount <= 0:
        message = "No Zones Defined. First create Zones and then try to Create Top Level Allocation";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)
    groupsCount = getGroupsCount()
    if groupsCount <= 0:
        message = "No Groups Defined. First create Groups and then try to Create Top Level Allocation";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html) 

    ## creation possible only if user has cloudman resource manager privileges
    userIsSuperUser = isSuperUser(groupsList)
    if not userIsSuperUser:
        message = "You don't have cloudman resource manager privileges. Hence you are not authorized to add new Top Level Allocation";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)

    ## if the request is through form submission, then get the values of all the fields and try to create top level allocation
    ## else present the form for creating a new top level allocation
    if request.method == 'POST':
        redirectURL = '/cloudman/message/?msg='        
        allocName = request.REQUEST.get("name", "")  ## Get the name of the allocation
        groupName = request.REQUEST.get("group", "") ## Get the group name
        selHepSpecs = request.REQUEST.get("hepspecs", "") 
        selMemory = request.REQUEST.get("memory", "")
        selStorage = request.REQUEST.get("storage", "")
        selBandwidth = request.REQUEST.get("bandwidth", "")
        comment = request.REQUEST.get('comment',"")
        try:
            validate_name(allocName)
            validate_name(groupName)
            validate_float(selHepSpecs)
            validate_float(selMemory)
            validate_float(selStorage)
            validate_float(selBandwidth)
            validate_comment(comment)
        except ValidationError as e:
            msg = 'Add Top Level Allocation Form  '+', '.join(e.messages)
            html = "<html><head><meta HTTP-EQUIV=\"REFRESH\" content=\"5; url=/cloudman/toplevelallocation/list/\"></head><body> %s.</body></html>" % msg
            return HttpResponse(html)

        ## Get the information about the zones used to fulfil the above resource parameters total values
        ## this information include zone ids, region names, zone names
        ## resource parameter values from each zone and the allowed resource types from each zone
        ## there is a one to one mapping among these lists, except the finalresourcestype and countresourcestype
        ## every count says how many rows of the list in resourcestype list belongs to a zone 
        ## E.g 37 test_region test_zone -1 10 -1 10 vm.small,vm.large 2  (-1 is used for NULL values)
        ## last value 2 says that two values from resource type belongs to this zone i.e vm.small and vm.large
        selZoneIds = request.REQUEST.getlist("finalzoneids")
        selRegions = request.REQUEST.getlist("finalregionlist")
        selZones = request.REQUEST.getlist("finalzonelist")
        selAllocHepSpecs = request.REQUEST.getlist("finalhepspecslist")
        selAllocMemory = request.REQUEST.getlist("finalmemorylist")
        selAllocStorage = request.REQUEST.getlist("finalstoragelist")
        selAllocBandwidth = request.REQUEST.getlist("finalbandwidthlist")
        selAllocResourceTypes = request.REQUEST.getlist("finalresourcestype")
        selCountResourceTypes = request.REQUEST.getlist("countresourcestype")
        ## Step 1: Check whether the allocation name is already used?
        allocNameExists = checkNameIgnoreCase(allocName)
        if allocNameExists:
            msgAlreadyExists = 'Allocation Name ' + allocName + ' already exists. Hence New Top Level Allocation Creation Stopped'
            return HttpResponseRedirect(redirectURL + msgAlreadyExists);
        ## Step 2: Get the Group object using the group name for which this allocation is defined
        try:
            groups = Groups.objects.get(name=groupName)
        except Groups.DoesNotExist:
            errorMessage = 'Group Name ' + groupName + ' does not exists'
            return HttpResponseRedirect(redirectURL + errorMessage)
        ## Step 3: Validate the resource parameter total values of this top level allocation
        errorMsg = checkAttributeValues(selHepSpecs, selMemory, selStorage, selBandwidth)
        if (errorMsg != ''):
            return HttpResponseRedirect(redirectURL + errorMsg)
        hepSpecsValue = float(selHepSpecs)
        memoryValue = float(selMemory)
        storageValue = float(selStorage)
        bandwidthValue = float(selBandwidth)
        ## Step 4: An extra validation step
        ## if the total resouce parameter value is Null then the zone share list should have all -1 for all zones hepspecs
        ## same thing checked for memory, storage and bandwidth
        if hepSpecsValue == -1:
            for oneValue in selAllocHepSpecs:
                if (oneValue != "-1"):
                    msgFailure = "Error in Hepspec Allocation. The total Hepspec allocation is equal to null, but Hepspec allocation from a zone appears to be not null"
                    return HttpResponseRedirect(redirectURL + msgFailure)
        if memoryValue == -1:
            for oneValue in selAllocMemory:
                if (oneValue != "-1"):
                    msgFailure = "Error in Memory Allocation. The total Memory allocation is equal to null, but Memory allocation from a zone appears to be not null"
                    return HttpResponseRedirect(redirectURL + msgFailure)
        if storageValue == -1:
            for oneValue in selAllocStorage:
                if (oneValue != "-1"):
                    msgFailure = "Error in Storage Allocation. The total Storage allocation is equal to null, but Storage allocation from a zone appears to be not null"
                    return HttpResponseRedirect(redirectURL + msgFailure)
        if bandwidthValue == -1:
            for oneValue in selAllocBandwidth:
                if (oneValue != "-1"):
                    msgFailure = "Error in Bandwidth Allocation. The total Bandwidth allocation is equal to null, but Bandwidth allocation from a zone appears to be not null"
                    return HttpResponseRedirect(redirectURL + msgFailure)
        ### Step 5: Validate resource parameters share from each zone and calculate the sum of each parameter, 
        ### by adding contribution from each zone (add if the contribution from a zone is not null)
        ## Start by initializing to null
        totalAllocHepSpecs = -1
        totalAllocMemory = -1
        totalAllocStorage = -1
        totalAllocBandwidth = -1
        for i in (range(len(selAllocHepSpecs))):
            zoneShareHepSpec = selAllocHepSpecs[i]
            zoneShareMemory = selAllocMemory[i] 
            zoneShareStorage = selAllocStorage[i] 
            zoneShareBandwidth = selAllocBandwidth[i]
            errorMsg = checkAttributeValues(zoneShareHepSpec, zoneShareMemory, zoneShareStorage, zoneShareBandwidth)
            if (errorMsg != ''):
                return HttpResponseRedirect(redirectURL + errorMsg)
            if (zoneShareHepSpec != "-1"):
                totalAllocHepSpecs = totalAllocHepSpecs + float(zoneShareHepSpec)
            if (zoneShareMemory != "-1"): 
                totalAllocMemory = totalAllocMemory + float(zoneShareMemory)
            if (zoneShareStorage != "-1"):
                totalAllocStorage = totalAllocStorage + float(zoneShareStorage)
            if (zoneShareBandwidth != "-1"):
                totalAllocBandwidth = totalAllocBandwidth + float(zoneShareBandwidth)
        ##### compensate by +1 (due to initialization to -1, if the total of the parameter is not null) 
        if totalAllocHepSpecs != -1:
            totalAllocHepSpecs = totalAllocHepSpecs + 1
        if totalAllocMemory != -1:
            totalAllocMemory = totalAllocMemory + 1
        if totalAllocStorage != -1:
            totalAllocStorage = totalAllocStorage + 1
        if totalAllocBandwidth != -1:
            totalAllocBandwidth = totalAllocBandwidth + 1
        ### Step 6: Check the resource parameter total values are matching with the sum of zones share
        ### both the total and zone share total will have -1, if Null is selected as a value for a parameter 
        if (hepSpecsValue != totalAllocHepSpecs):
            message = "The Selected Value for Hepspec is not matching with the sum of Hepspec of all selected Zones"
            return HttpResponseRedirect(redirectURL + message)
        if (memoryValue != totalAllocMemory):
            message = "The Selected Value for Memory is not matching with the sum of Memory of all selected Zones"
            return HttpResponseRedirect(redirectURL + message)
        if (storageValue != totalAllocStorage):
            message = "The Selected Value for Storage is not matching with the sum of Storage of all selected Zones"
            return HttpResponseRedirect(redirectURL + message)
        if (bandwidthValue != totalAllocBandwidth):
            message = "The Selected Value for Bandwidth is not matching with the sum of Bandwidth of all selected Zones"
            return HttpResponseRedirect(redirectURL + message)
        ## Step 7: for each zone share, validate whether the resources requested can be taken from the zone 
        ## i.e check whether the resources are available from each zone
        for i in range(len(selZones)):
            regionName = selRegions[i]
            zoneName = selZones[i];
            hepSpecs_value = float(selAllocHepSpecs[i])
            memory_value = float(selAllocMemory[i])
            storage_value = float(selAllocStorage[i])
            bandwidth_value = float(selAllocBandwidth[i])
            errorMessage = checkZoneShareAvailability(regionName, zoneName, hepSpecs_value, memory_value, storage_value, bandwidth_value)
            if errorMessage != '':
                return HttpResponseRedirect(redirectURL + errorMessage)
        ## Step 8: If reached till here, that means all validations are done and so now start adding the top level allocation 
        finalMessage = ''
	try:
            ## Create the Top Level Allocation record for the selected group with the total resource values
            groupRecord = Groups.objects.get(name=groupName)
            if (hepSpecsValue == -1):
                hepSpecsValue = None
            if (memoryValue == -1):
                memoryValue = None
            if (storageValue == -1):
                storageValue = None
            if (bandwidthValue == -1):
                bandwidthValue = None
            tpalloc = TopLevelAllocation(name = allocName, group = groupRecord, hepspec = hepSpecsValue, memory = memoryValue, storage = storageValue, bandwidth = bandwidthValue)
            tpalloc.save()
        except Exception, err:
            finalMessage = "Error in Creating Top Level Allocation , reason : %s" % str(err)
            html = "<html><body> %s.</body></html>" % finalMessage
            transaction.rollback()
            return HttpResponse(html)
        finalMessage = "Top Level Allocation Created Successfully with Name %s for group %s with %s Hepspec, %s Memory, %s Storage, %s Bandwidth " % (allocName, groupName, str(hepSpecsValue), str(memoryValue), str(storageValue), str(bandwidthValue))
        finalMessage += "<br/><br/>";
        ## Now assign each zone share to the Top Level Allocation By Zone table
        tpalloc = None
        try:
            finalMessage += " Assigning Allocation to Zones: <br/>";
            tpalloc = TopLevelAllocation.objects.get(name = allocName) 
            for i in range(len(selZones)):
                ## get the values for a zone
                regionName = selRegions[i]
                zoneName = selZones[i];
                hepSpecs_value = float(selAllocHepSpecs[i])
                memory_value = float(selAllocMemory[i])
                storage_value = float(selAllocStorage[i])
                bandwidth_value = float(selAllocBandwidth[i])
                ## Get the zone object
                zoneRecord = Zone.objects.get(name = zoneName, region__name = regionName)
                if (hepSpecs_value == -1):
                   hepSpecs_value = None
                if (memory_value == -1):
                   memory_value = None
                if (storage_value == -1):
                   storage_value = None
                if (bandwidth_value == -1):
                   bandwidth_value = None
                zonealloc = TopLevelAllocationByZone(top_level_allocation = tpalloc, zone = zoneRecord, hepspec = hepSpecs_value, memory = memory_value, storage = storage_value, bandwidth = bandwidth_value)
                zonealloc.save()
                finalMessage += "Zone: %s in Region : %s with Hepspec: %s, Memory: %s, Storage: %s, Bandwidth: %s " % (zoneName, regionName, str(hepSpecs_value), str(memory_value), str(storage_value), str(bandwidth_value))
                finalMessage += "<br/>"
        except Exception, err:                 
                finalMessage += "<br/>Exception Arised while Assigning Allocation To Zones, reason : %s " % str(err)
                finalMessage += "<br/> Hence Top Level Allocation Creation Stopped Here (and also record cleared completely)."
                transaction.rollback()
                tpalloc.delete()
                html = "<html><body> %s.</body></html>" % finalMessage
                return HttpResponse(html)

        ## Finally add the allowed resource types for each zone in this allocation
        finalMessage += "<br/>"
        try:
            finalMessage += " Assigning Allowed Resource Types to Allocation : <br/>"
            index = 0
            for i in range(len(selZones)):
               zoneName = selZones[i]
               regionName = selRegions[i]
               zoneRecord = Zone.objects.get(name = zoneName, region__name = regionName)
               rtCount = float(selCountResourceTypes[i])
               k = 0
               while (k < rtCount):
                 selResourceType = selAllocResourceTypes[index]
                 finalMessage += " Resource Type Name: " + selResourceType + ", Zone: " + zoneName + "<br/>"
                 resourceTypeRecord = ResourceType.objects.get(name = selResourceType)
                 allowedResourceType = TopLevelAllocationAllowedResourceType(top_level_allocation = tpalloc, zone = zoneRecord, resource_type = resourceTypeRecord)
                 allowedResourceType.save() 
                 index = index + 1
                 k = k+1
        except Exception, err:
            finalMessage += "Exceptin Arised while Assinging Allowed Resources Types for the Allocation, reason : %s " %str(err)
            finalMessage += "<br/> Hence Top Level Allocation Creation Stopped Here (and also record cleared completely)."
            transaction.rollback()
            tpalloc.delete()
            html = "<html><body> %s.</body></html>" % finalMessage
            return HttpResponse(html)
        #Add the LOg
        tpAllocObj = TopLevelAllocation.objects.get(name=allocName)
        addLog(request,allocName,comment,tpAllocObj,None,'topallocation','add',True)        
        ## Last Step: Return a success message and breif description of the allocation to the user    
        finalMessage += "<br/> Top Level Allocation Creation Successfully Completed";
        html = "<html><head><meta HTTP-EQUIV=\"REFRESH\" content=\"5; url=/cloudman/toplevelallocation/list/\"></head><body> %s.</body></html>" % finalMessage        
        transaction.commit()
        return HttpResponse(html)
    ## form post method submission ends here
    ## if not a form submission, then get all the available region and group names to prepare a add form
    groupsList = Groups.objects.values_list('name', flat=True).order_by('name');
    regionsList = Region.objects.values_list('name', flat=True).order_by('name');
    return render_to_response('toplevelallocation/addnew.html',locals(),context_instance=RequestContext(request))

def listall(request):
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    userIsSuperUser = isSuperUser(groupsList)
    topLevelAllocationList = TopLevelAllocation.objects.select_related('group').all().order_by('name')    
    #topLevelAllocationList = TopLevelAllocation.objects.all().order_by('name')
    return render_to_response('toplevelallocation/listall.html',locals(),context_instance=RequestContext(request))



def getdetails(request):
    redirectURL = '/cloudman/message/?msg='
    allocName = request.REQUEST.get("name", "")

    ## Get the Top Level Allocation Object
    allocInfo = None
    try:
       allocInfo = TopLevelAllocation.objects.select_related('group').get(name=allocName)
    except TopLevelAllocation.DoesNotExist:
       errorMessage = 'Top Level Allocation with Name ' + allocName + ' does not exists'
       return HttpResponseRedirect(redirectURL + errorMessage)

    ## Get the zones share of this allocation
    allocZonesInfo = TopLevelAllocationByZone.objects.filter(top_level_allocation = allocInfo).select_related('zone','zone__region').order_by('zone__name')

    ## Get the allowed Resource Types of this allocation
    allowedResourceTypesList = TopLevelAllocationAllowedResourceType.objects.select_related('zone','zone__region','resource_type').filter(top_level_allocation = allocInfo).order_by('resource_type__name')

    ## form a record specifying all the parameters for each zone used in this allocation     
    allocZonesShareList = []
    ## also, find out the unique regions used in this allocation
    regionNamesList = []
    for oneZone in allocZonesInfo:
        oneRecord = ()
        hepspec = oneZone.hepspec
        memory = oneZone.memory
        storage = oneZone.storage
        bandwidth = oneZone.bandwidth
        zoneName = oneZone.zone.name
        regionName = oneZone.zone.region.name

        oneRecord = (regionName, zoneName, hepspec, memory, storage, bandwidth)
        if regionName not in regionNamesList:
           regionNamesList.append(regionName)
        allocZonesShareList.append(oneRecord)
    prAllocList = ProjectAllocation.objects.filter(top_level_allocation__name = allocName).select_related('project','group').order_by('name') 
    object_id = allocInfo.id
    changeLogList = getLog('topallocation',allocName,object_id,None)
    return render_to_response('toplevelallocation/getdetails.html',locals(),context_instance=RequestContext(request))



def getProjectAllocInTopLevelAllocation(request):
    mimetype = 'application/javascript'
    tpAllocName = request.REQUEST.get("name", "")
    try:
        prAllocList = ProjectAllocation.objects.filter(top_level_allocation__name = tpAllocName).order_by('name')
        projectAllocationInfo = []
        for prjAlloc in prAllocList:
            name  =  prjAlloc.name
            project = prjAlloc.project.name
            group = prjAlloc.group.name
            hepspec = displayNone(prjAlloc.hepspec)
            memory = displayNone(prjAlloc.memory)
            storage = displayNone(prjAlloc.storage)
            bandwidth = displayNone(prjAlloc.bandwidth)
            projectAllocationInfo.append({'name':name,'project':project,'group':group,'hepspec':hepspec,'memory':memory,
                                          'storage':storage,'bandwidth':bandwidth})    
    except Exception:
        printStackTrace()
    data = simplejson.dumps(projectAllocationInfo)
    return HttpResponse(data,mimetype)



## used to get the hepspec information about a top level allocation 
## region wise allocation information i.e total allocation from each region used in a given top level allocation
## zone wise allocation information i.e total allocation from each zone used in a given top level allocation
def gethepspecstats(request):
    ## if the request is through ajax, then return the json object, otherwise return status 400 - BAD REQUEST
    #if request.is_ajax():
       allocName = request.REQUEST.get("name", "")
       format = 'json'
       mimetype = 'application/javascript'

       ## Get the Top Level Allocation Object
       allocInfo = TopLevelAllocation.objects.get(name=allocName)
       totHepSpecsAlloc = 0
       if (allocInfo.hepspec != None):
          totHepSpecsAlloc = allocInfo.hepspec
  
       ## form an object with the information of this allocation object
       allocStatsInfo = [{"pk": allocName, "model": "cloudman.toplevelallocation", "fields": {"tothepspecs": totHepSpecsAlloc}}]

       ## Get the zone shares of this allocation
       allocZonesInfo = TopLevelAllocationByZone.objects.filter(top_level_allocation__name = allocName).values_list('hepspec', 'zone__name', 'zone__region__name', 'zone__hepspecs', 'zone__hepspec_overcommit').order_by('zone__name')
  
       ## form an object for each region with its zones, top level allocation hepspec value and the total zone hepspecs 
       regionsInfo = {}
       for oneZone in allocZonesInfo:
          hepspec = oneZone[0]
          zoneName = oneZone[1]
          regionName = oneZone[2]
          zoneTotHepSpecs = 0
          if (oneZone[3] != None):
            zoneTotHepSpecs = oneZone[3] * oneZone[4]
          if not (regionName in regionsInfo):
            regionsInfo[regionName] = {'zones': [], 'hepspec': [], 'zonetothepspecs': []}
          regionsInfo[regionName]['zones'].append(zoneName)
          regionsInfo[regionName]['hepspec'].append(hepspec)
          regionsInfo[regionName]['zonetothepspecs'].append(zoneTotHepSpecs)

       ## Iterate through the object formed above to form objects one for each zone with its hepspec share information 
       for oneRegion in regionsInfo.iterkeys():
          regionsInfo[oneRegion]['totalloc'] = 0

          zonesList = regionsInfo[oneRegion]['zones']
          hepspecList = regionsInfo[oneRegion]['hepspec']
          zoneTotHepSpecsList = regionsInfo[oneRegion]['zonetothepspecs']

          for i in range(len(zonesList)):
            zoneName = zonesList[i]
            tpHepSpec = hepspecList[i]
            zoneTotHepSpec = zoneTotHepSpecsList[i]
            if tpHepSpec != None:
               regionsInfo[oneRegion]['totalloc'] = regionsInfo[oneRegion]['totalloc'] + tpHepSpec
            allocStatsInfo.append({"pk": i, "model": "cloudman.zone", "region": oneRegion, "zone": zoneName, "fields": {"allochepspecs": tpHepSpec}})

       ## finally form objects for each region giving its hepspec share for this allocation
       for oneRegion in regionsInfo.iterkeys():
          regionAllocHepSpecs = regionsInfo[oneRegion]['totalloc']
          allocStatsInfo.append({"pk": oneRegion, "model": "cloudman.region", "fields": {"allochepspecs": regionAllocHepSpecs}})
       data = simplejson.dumps(allocStatsInfo)
       return HttpResponse(data,mimetype)
    #else:
    #   return HttpResponse(status=400)

## used to get the entire resource information (hepspec, memory, storage and bandwidth) 
## of a given top level allocation -> primarily used by project allocation
## to check whether a given project allocation can be met by the top level allocation
def getresourceinfo(request):
        redirectURL = '/cloudman/message/?msg='
    ## if the request is through ajax, then return the json object, otherwise return status 400 - BAD REQUEST
    #if request.is_ajax():
        format = 'json'
        mimetype = 'application/javascript'
        topLevelAllocationName = request.REQUEST.get("name", "")

        ## initialize three dict, one each for total, free and used fraction resource parameter values
        totResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
        freeResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
        usedFraction = {'hepspec': 0, 'memory': 0, 'storage': 0, 'bandwidth': 0 }

        ## call this function to calculate the above defined values
        errorMessage = getstats(topLevelAllocationName, totResources, freeResources, usedFraction)
        if errorMessage != '':
           nulldata = []
           data = simplejson.dumps(nulldata)
           return HttpResponse(data,mimetype)

        ## frame an object with all the resource parameter info for this top level allocation
        ## the information include, what is total available, how much is free and percentage of already allocated
        topLevelAllocationInfo = [{"model": "cloudman.toplevelallocationinfo", "fields": {"tothepspecs": totResources['hepspec'], "totmemory": totResources['memory'], "totstorage": totResources['storage'], "totbandwidth": totResources['bandwidth']}}, {"model": "cloudman.toplevelallocationfreeinfo", "fields": {"hepspecsfree" : freeResources['hepspec'], "memoryfree": freeResources['memory'], "storagefree": freeResources['storage'], "bandwidthfree": freeResources['bandwidth']}}, {"model": "cloudman.toplevelallocationusedinfoper", "fields":{"hepspecsfraction": usedFraction['hepspec'], "memoryfraction": usedFraction['memory'], "storagefraction": usedFraction['storage'], "bandwidthfraction": usedFraction['bandwidth']}}]

        ## Get the Top Level Allocation allowed resource types
        topLevelAllocationResourceTypeObjects = TopLevelAllocationAllowedResourceType.objects.filter(top_level_allocation__name=topLevelAllocationName)
        for oneRow in topLevelAllocationResourceTypeObjects:
           rtObject = oneRow.resource_type
           zoneObject = oneRow.zone
           topLevelAllocationInfo.append({"pk": rtObject.id, "model": "cloudman.resourcetype", "fields": {"zonename": zoneObject.name, "regionname": zoneObject.region.name, "name": rtObject.name, "resource_class": rtObject.resource_class, "hepspecs": rtObject.hepspecs, "memory": rtObject.memory, "storage": rtObject.storage, "bandwidth": rtObject.bandwidth}})

        ## finally dump the data into json and return the json object
        data = simplejson.dumps(topLevelAllocationInfo)
        return HttpResponse(data,mimetype)
    # If you want to prevent non AJAX calls
    #else:
    #    return HttpResponse(status=400)

## used to get the entire resource information (hepspec, memory, storage and bandwidth) 
## of a given top level allocation
def getstats(tpAllocName, totResources, freeResources, usedFraction):
    errorMessage = ''
    ## Get the Top Level Allocation Object
    topLevelAllocationObject = None
    try:
        topLevelAllocationObject = TopLevelAllocation.objects.get(name=tpAllocName)
    except TopLevelAllocation.DoesNotExist:
        errorMessage = 'Top Level Allocation Name ' + tpAllocName + ' does not exists'
        return HttpResponseRedirect(redirectURL + errorMessage)
    
    ## Assign the resource parameter values to separate variables 
    totHepSpecs = topLevelAllocationObject.hepspec
    totMemory = topLevelAllocationObject.memory
    totStorage = topLevelAllocationObject.storage
    totBandwidth = topLevelAllocationObject.bandwidth
    totResources['hepspec'] = totHepSpecs
    totResources['memory'] = totMemory
    totResources['storage'] = totStorage
    totResources['bandwidth'] = totBandwidth

    ## Get all the Project allocations using this top level allocation
    projectAllocationObjects = ProjectAllocation.objects.filter(top_level_allocation__name = tpAllocName)

    ## Find how much of top level allocation is already allocated. Start with none is allocated
    hepSpecsFree = totHepSpecs
    memoryFree = totMemory
    storageFree = totStorage
    bandwidthFree = totBandwidth

    for oneProject in projectAllocationObjects:
        hepspec = oneProject.hepspec
        if ( (hepspec != None) and (totHepSpecs != None) ):
           hepSpecsFree = hepSpecsFree - hepspec

        memory = oneProject.memory
        if ( (memory != None) and (totMemory != None) ):
           memoryFree = memoryFree - memory
            
        storage = oneProject.storage
        if ( (storage != None) and (totStorage != None) ):
           storageFree = storageFree - storage

        bandwidth = oneProject.bandwidth
        if ( (bandwidth != None) and (totBandwidth != None) ):
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
    tpAllocName = request.REQUEST.get("name", "")
    redirectURL = '/cloudman/message/?msg='
    comment = request.REQUEST.get("comment", "deleting")
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;

    ## update is allowed only if the user has cloudman resource manager privileges
    userIsSuperUser = isSuperUser(groupsList)
    if not userIsSuperUser:
        message = "You don't have cloudman resource manager privileges. Hence you are not authorized to Delete Top Level Allocation";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)
    ## Get the Top Level Allocation Object
    tpAllocObject = None
    try:
       tpAllocObject = TopLevelAllocation.objects.get(name=tpAllocName)
    except TopLevelAllocation.DoesNotExist:
       failureMessage = "Top Level Allocation with Name " + tpAllocName + " could not be found"
       return HttpResponseRedirect(redirectURL+failureMessage)

    ## Check whether any project allocations are there using this top level allocation
    prAllocNames = ProjectAllocation.objects.filter(top_level_allocation__name__iexact = tpAllocName).values_list('name', flat=True).order_by('name')

    ## If yes, then alert the user and do not delete the top level allocation
    finalMessage = ''
    prAllocNamesList = list(prAllocNames)
    if len(prAllocNamesList) > 0:
       finalMessage = finalMessage + "Project Allocation Names: " + (', '.join(prAllocNamesList)) + "<br/>"
    if not finalMessage == '':
       finalMessage = "Top Level Allocation with Name " + tpAllocName + " Could not be deleted because it is being used in " + "<br/>" + finalMessage
       html = "<html><body> %s</body></html>" % finalMessage
       return HttpResponse(html)


    #Add the Log
    oldtpAllocObject = tpAllocObject    
    status = addLog(request,tpAllocName,comment,oldtpAllocObject,None,'topallocation','delete',False)

    ## If no project allocations, then first delete the allowed resource types, then its zone allocation
    ## and finally its information
    TopLevelAllocationAllowedResourceType.objects.filter(top_level_allocation__name__iexact = tpAllocName).delete()
    TopLevelAllocationByZone.objects.filter(top_level_allocation__name__iexact = tpAllocName).delete()
    tpAllocObject.delete()
    if status:
        transaction.commit()
    else:
        transaction.rollback()
    ## Return a success message to the user
    message = "Top Level Allocation with Name " + tpAllocName + " deleted successfully "
    html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/toplevelallocation/list/\"></HEAD><body> %s.</body></html>" % message
    return HttpResponse(html)

@transaction.commit_on_success
def deleteMultiple(request):
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    comment = request.REQUEST.get("comment", "deleting")
    topAllocNameList = request.REQUEST.get("name_list", "")
    printArray = []
    ## update is allowed only if the user has cloudman resource manager privileges
    userIsSuperUser = isSuperUser(groupsList)
    if not userIsSuperUser:
        message = "You don't have cloudman resource manager privileges. Hence you are not authorized to Delete Top Level Allocation";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)

    title = "Delete multiple Top Level Allocation message"
    topAllocNameArray = topAllocNameList.split("%%")
    for tpAllocName in topAllocNameArray:
        ## Get the Top Level Allocation Object
        tpAllocObject = None
        try:
            tpAllocObject = TopLevelAllocation.objects.get(name=tpAllocName)
        except TopLevelAllocation.DoesNotExist:
            printArray.append ("Top Level Allocation with Name " + tpAllocName + " could not be found")		
            continue
        ## Check whether any project allocations are there using this top level allocation
        prAllocNames = ProjectAllocation.objects.filter(top_level_allocation__name__iexact = tpAllocName).values_list('name', flat=True).order_by('name')
        ## If yes, then alert the user and do not delete the top level allocation
        finalMessage = ''
        prAllocNamesList = list(prAllocNames)
        if len(prAllocNamesList) > 0:
            finalMessage = finalMessage + "Project Allocation Names: " + (', '.join(prAllocNamesList)) + "  "
        if not finalMessage == '':
            finalMessage = "Top Level Allocation with Name " + tpAllocName + " Could not be deleted because it is being used in " + "  " + finalMessage
            printArray.append(finalMessage)
        else:
            #write the Log
            addLog(request,tpAllocName,comment,tpAllocObject,None,'topallocation','delete',False)
            ## If no project allocations, then first delete the allowed resource types, then its zone allocation
            ## and finally its information
            TopLevelAllocationAllowedResourceType.objects.filter(top_level_allocation__name__iexact = tpAllocName).delete()
            TopLevelAllocationByZone.objects.filter(top_level_allocation__name__iexact = tpAllocName).delete()
            tpAllocObject.delete()
            printArray.append("Top Level Allocation with Name " + tpAllocName + " deleted successfully ")
    return render_to_response('base/deleteMultipleMsg.html',locals(),context_instance=RequestContext(request))	

@transaction.commit_on_success
def update(request):
    ## Three options will be provided for updating a top level allocation
    ## 1. Just changing the name of the allocation (optype == updatename)
    ## 2. Updating the resource parameter values of a zone or deleting completely a zone from the allocation 
    ## (optype == updatezone or deletezone)
    ## 3. adding a new zone(s) to the allocation (optype == newzone)

    tpAllocName = request.REQUEST.get("name", "")
    redirectURL = '/cloudman/message/?msg='

    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    ## update is allowed only if the user has cloudman resource manager privileges
    userIsSuperUser = isSuperUser(groupsList)
    if not userIsSuperUser:
        message = "You don't have cloudman resource manager privileges. Hence you are not authorized to edit Top Level Allocation";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)

    ## Get the Top Level Allocation Object
    tpAllocObject = None
    try:
        tpAllocObject = TopLevelAllocation.objects.get(name=tpAllocName)
    except TopLevelAllocation.DoesNotExist:
        failureMessage = "Top Level Allocation with Name " + tpAllocName + " could not be found"
        return HttpResponseRedirect(redirectURL+failureMessage)
    ## if the request is due to a form submission, then perform the update operation
    ## or else return with all the data required to display a form for showing update options
    if request.method == 'POST':
        oldtpAllocInfo = getTopAllocationInfo(tpAllocObject)
        ## Existing values 
        currName = tpAllocObject.name
        currHepSpec = tpAllocObject.hepspec
        currMemory = tpAllocObject.memory
        currStorage = tpAllocObject.storage
        currBandwidth = tpAllocObject.bandwidth
        comment = request.REQUEST.get("comment")
        print request.REQUEST
        ## get the operation type
        opType = request.REQUEST.get("optype", "")
        scale = None
        storagescale = None
        ## if the operation is just changing a name
        if opType == 'updatename':
           ## validate the new name and assign the new name if everything is fine
           newName = request.REQUEST.get("newname", "")
           if (currName != newName):
              if (newName == ''):
                 errorMsg = 'Name name field cannot be left blank. So Edit Top Level Allocation operation stopped'
                 return HttpResponseRedirect(redirectURL + errorMsg)
              nameExists = checkNameIgnoreCase(newName)
              if nameExists:
                 msgAlreadyExists = 'Top Level Allocation ' + newName + ' already exists. Hence Edit Top Level Allocation Operation Stopped'
                 return HttpResponseRedirect(redirectURL + msgAlreadyExists);
              tpAllocObject.name = newName
              currName = newName 
        ## operation is adding a new zone to the allocation with the resource parameters share
        elif opType == 'newzone':
            ## extract all the information needed to add the new zones
            selRegions = request.REQUEST.getlist("finalregionlist")
            selZones = request.REQUEST.getlist("finalzonelist")
            selAllocHepSpecs = request.REQUEST.getlist("finalhepspecslist")
            selAllocMemory = request.REQUEST.getlist("finalmemorylist")
            selAllocStorage = request.REQUEST.getlist("finalstoragelist")
            selAllocBandwidth = request.REQUEST.getlist("finalbandwidthlist")
            selAllocResourceTypes = request.REQUEST.getlist("finalresourcestype")
            selCountResourceTypes = request.REQUEST.getlist("countresourcestype")           
            ## the following function will check the zones resource parameter values that are selected to add 
            ## and if all is fine, then added to the top level allocation
            errorMessage = checkAndInsertNewZone(selRegions, selZones, selAllocHepSpecs, selAllocMemory, selAllocStorage, selAllocBandwidth, selAllocResourceTypes, selCountResourceTypes, tpAllocObject)
            if errorMessage != '':
                transaction.rollback()
                return HttpResponseRedirect(redirectURL + errorMessage)
        ## operation is deleting a zone from the allocation
        elif opType == 'deletezone':
            selRegion = request.REQUEST.get("selregionname")
            selZone = request.REQUEST.get("selzonename")
            ## check whether due to deletion of this zone from the allocation, whether there will be
            ## any impact on the project allocations i.e total minus this zone resource values
            ## are good enough to meet the existing project allocations
            errorMessage = checkAndDeleteZone(selRegion, selZone, tpAllocObject, currName)
            if errorMessage != '':
                transaction.rollback()
                return HttpResponseRedirect(redirectURL + errorMessage)

        ## operation is updating the resource parameter values for existing zone
        elif opType == 'updatezone':
            selRegion = request.REQUEST.get("selregionname")
            selZone = request.REQUEST.get("selzonename")
            newHepSpec = request.REQUEST.get("newhepspec")
            newMemory = request.REQUEST.get("newmemory")
            newStorage =  request.REQUEST.get("newstorage")
            newBandwidth = request.REQUEST.get("newbandwidth")
            scale = request.REQUEST.get("scale")
            storagescale = request.REQUEST.get("storagescale")
            ## check whether due to update of this zone from the allocation, whether there will be
            ## any impact on the project allocations i.e the updated total resources
            ## are good enough to meet the existing project allocations
            errorMessage = checkAndUpdateZone(selRegion, selZone, tpAllocObject, currName, newHepSpec, newMemory, newStorage, newBandwidth,scale,storagescale)
            if errorMessage != '':
                transaction.rollback()
                return HttpResponseRedirect(redirectURL + errorMessage)

        ## Finally save all the changes
        if scale is not None:
            scalefactor = getScaleFactor(newHepSpec,currHepSpec)
            scaleTopAllocationHepSpec(currName,scalefactor,scale=True)    
        if storagescale is not None:
            scalefactor = getScaleFactor(newStorage,currStorage)
            scaleTopAllocationStorage(currName,scalefactor,scale=True)    

        tpAllocObject.save()        
        #Write The Log
        newtpAllocInfo = getTopAllocationInfo(tpAllocObject)
        objectId = tpAllocObject.id
        addUpdateLog(request,currName,objectId,comment,oldtpAllocInfo,newtpAllocInfo,'topallocation',True)        
        ## Return a success message to the user
        message = 'Top Level Allocation ' + tpAllocName + ' Successfully Updated'
        html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/toplevelallocation/list/\"></HEAD><body> %s </body></html>" % (message)
        transaction.commit()
        return HttpResponse(html)

    ## the form submission condition ends here
    ## Get all the Names of all the regions
    regionsList = Region.objects.all().values_list('name', flat=True)
    return render_to_response('toplevelallocation/update.html',locals(),context_instance=RequestContext(request))

## Get the zones with their region names used in a given top level allocation
def getzonelist(request):
    ## if the request is through ajax, then return the json object, otherwise return status 400 - BAD REQUEST
    #if request.is_ajax():
       tpAllocName = request.REQUEST.get("name", "")
       format = 'json'
       mimetype = 'application/javascript'

       ##Get the zones and its region name used in this top level allocation
       allocZonesInfo = TopLevelAllocationByZone.objects.filter(top_level_allocation__name = tpAllocName).values_list('zone__name', 'zone__region__name').order_by('zone__name')

       ## frame an object for each zone and finally dump the data into json object
       allocStatsInfo = []
       i = 1
       for oneZone in allocZonesInfo:           
          allocStatsInfo.append({"pk": i, "model": "cloudman.toplevelallocationbyzone", "region": oneZone[1], "zone": oneZone[0]}) 
          i = i+1
       data = simplejson.dumps(allocStatsInfo)
       return HttpResponse(data,mimetype)
    #else:
    #   return HttpResponse(status=400)

def checkAndDeleteZone(selRegion, selZone, tpAllocObject, currName):
    errorMessage = ''
    ## Get the selected zone object of the top level allocation
    tpAllocZoneObject = None
    try:
      tpAllocZoneObject = TopLevelAllocationByZone.objects.get(top_level_allocation__name = currName, zone__name=selZone, zone__region__name=selRegion)
    except TopLevelAllocationByZone.DoesNotExist:
      return 'Selected Zone ' + selZone + ' of Region ' + selRegion + ' not found in top level allocation '

    totHepSpec = tpAllocObject.hepspec
    totMemory = tpAllocObject.memory
    totStorage = tpAllocObject.storage
    totBandwidth = tpAllocObject.bandwidth

    ## now reduce this values by the values of the selected zone
    if tpAllocZoneObject.hepspec != None:
       totHepSpec = totHepSpec - tpAllocZoneObject.hepspec
    if tpAllocZoneObject.memory != None:
       totMemory = totMemory - tpAllocZoneObject.memory
    if tpAllocZoneObject.storage != None:
       totStorage = totStorage - tpAllocZoneObject.storage
    if tpAllocZoneObject.bandwidth != None:
       totBandwidth = totBandwidth - tpAllocZoneObject.bandwidth

    ## now calculate how much resources are already allocated to projects
    totAllocHepSpec = None
    totAllocMemory = None
    totAllocStorage = None
    totAllocBandwidth = None

    prAllocObjects = ProjectAllocation.objects.filter(top_level_allocation__name = currName)
    for oneObject in prAllocObjects:
        if oneObject.hepspec != None:
           if totAllocHepSpec == None:
              totAllocHepSpec = 0
           totAllocHepSpec = totAllocHepSpec + oneObject.hepspec
        if oneObject.memory != None:
           if totAllocMemory == None:
              totAllocMemory = 0
           totAllocMemory = totAllocMemory + oneObject.memory
        if oneObject.storage != None:
           if totAllocStorage == None:
              totAllocStorage = 0
           totAllocStorage = totAllocStorage + oneObject.storage
        if oneObject.bandwidth != None:
           if totAllocBandwidth == None:
              totAllocBandwidth = 0
           totAllocBandwidth = totAllocBandwidth + oneObject.bandwidth

    ## now check the total resources minus the zone resoures are still greater than or equal to sum
    ## of project allocations
    if ( (totAllocHepSpec == None) or (totHepSpec == None) ):
        if ( (totAllocHepSpec != None) and (totHepSpec == None) ):
           errorMessage = errorMessage + 'The remaining Hepspec cannot fulfill the already allocated Hepspec. '
    else:
        if ( totAllocHepSpec > totHepSpec ) :
           errorMessage = errorMessage + 'The remaining Hepspec cannot fulfill the already allocated Hepspec. '

    if ( (totAllocMemory == None) or (totMemory == None) ):
        if ( (totAllocMemory != None) and (totMemory == None) ):
           errorMessage = errorMessage + 'The remaining Memory cannot fulfill the already allocated Memory. '
    else:
        if ( totAllocMemory > totMemory ) :
           errorMessage = errorMessage + 'The remaining Memory cannot fulfill the already allocated Memory. '

    if ( (totAllocStorage == None) or (totStorage == None) ):
        if ( (totAllocStorage != None) and (totStorage == None) ):
           errorMessage = errorMessage + 'The remaining Storage cannot fulfill the already allocated Storage. '
    else:
        if ( totAllocStorage > totStorage ) :
           errorMessage = errorMessage + 'The remaining Storage cannot fulfill the already allocated Storage. '

    if ( (totAllocBandwidth == None) or (totBandwidth == None) ):
        if ( (totAllocBandwidth != None) and (totBandwidth == None) ):
           errorMessage = errorMessage + 'The remaining Bandwidth cannot fulfill the already allocated Bandwidth. '
    else:
        if ( totAllocBandwidth > totBandwidth ) :
           errorMessage = errorMessage + 'The remaining Bandwidth cannot fulfill the already allocated Bandwidth. '
  
    ## if allocations cannot be met due to the deletion of this zone, then raise an alert to the user 
    if errorMessage != '':
       errorMessage = 'Deletion of Zone ' + selZone + ' of Region ' + selRegion + ' from the Top Level Allocation leads to the failure of the following conditions. Hence deletion operation stopped. ' + errorMessage
       return errorMessage

    ## if allocations can be met, then delete the selected zone
    try:
       ## First delete the allowed resource types and then the zone from the top level allocation
       TopLevelAllocationAllowedResourceType.objects.filter(top_level_allocation__name=currName, zone__name=selZone, zone__region__name=selRegion).delete()
       tpAllocZoneObject.delete()
    except Exception, err:
       errorMessage = 'Zone ' + selZone + ' of Region ' + selRegion + ' for Top Level Allocation could not be deleted , reason : %s' % str(err)
       return errorMessage
   
    ## if any of the resource values becomes zero, then to keep the consistency, make 0 as UNDEFINED i.e NULL
    ## for that parameter in both the top level allocation and in all the zone share  
    if ( (totHepSpec == 0) or (totMemory == 0) or (totStorage == 0) or (totBandwidth == 0) ):
       if totHepSpec == 0:
          totHepSpec = None
          TopLevelAllocationByZone.objects.filter(top_level_allocation__name=currName).update(hepspec=None)
       if totMemory == 0:
          totMemory = None
          TopLevelAllocationByZone.objects.filter(top_level_allocation__name=currName).update(memory=None)
       if totStorage == 0:
          totStorage = None
          TopLevelAllocationByZone.objects.filter(top_level_allocation__name=currName).update(storage=None)
       if totBandwidth == 0:
          totBandwidth = None
          TopLevelAllocationByZone.objects.filter(top_level_allocation__name=currName).update(bandwidth=None)
       
    tpAllocObject.hepspec = totHepSpec
    tpAllocObject.memory = totMemory
    tpAllocObject.storage = totStorage
    tpAllocObject.bandwidth = totBandwidth
    return errorMessage

def checkAndInsertNewZone(selRegions, selZones, selAllocHepSpecs, selAllocMemory, selAllocStorage, selAllocBandwidth, selAllocResourceTypes, selCountResourceTypes, tpAllocObject):

    errorMessage = '' 
    ## First check for each zone, whether resources requested are available or not
    for i in range(len(selZones)):
       errorMessage = ''
       regionName = selRegions[i]
       zoneName = selZones[i];
       hepSpecs_value = round((float(selAllocHepSpecs[i])), 3)
       memory_value = round((float(selAllocMemory[i])), 3)
       storage_value = round((float(selAllocStorage[i])), 3)
       bandwidth_value = round((float(selAllocBandwidth[i])), 3)
       errorMessage = errorMessage + checkAttributeValues(hepSpecs_value, memory_value, storage_value, bandwidth_value)
       errorMessage = errorMessage + checkZoneShareAvailability(regionName, zoneName, hepSpecs_value, memory_value, storage_value, bandwidth_value)
       if errorMessage != '':
          return errorMessage

    totAllocHepSpec = tpAllocObject.hepspec
    totAllocMemory = tpAllocObject.memory
    totAllocStorage = tpAllocObject.storage
    totAllocBandwidth = tpAllocObject.bandwidth

    for i in (range(len(selRegions))):
        regionName = selRegions[i]
        zoneName = selZones[i]
        hepSpec = round((float(selAllocHepSpecs[i])), 3)
        memory = round((float(selAllocMemory[i])), 3)
        storage = round((float(selAllocStorage[i])), 3)
        bandwidth = round((float(selAllocBandwidth[i])), 3)

        ## Get the zone object
        zoneRecord = Zone.objects.get(name = zoneName, region__name = regionName)

        ## if the selected resource parameter is not null, then add it to the existing resource parameter values
        ## of the top level allocation
        if (hepSpec == -1):
           hepSpec = None
        else:
           if totAllocHepSpec == None:
              totAllocHepSpec = 0
           totAllocHepSpec = totAllocHepSpec + hepSpec

        if (memory == -1):
           memory = None
        else:
           if totAllocMemory == None:
              totAllocMemory = 0
           totAllocMemory = totAllocMemory + memory

        if (storage == -1):
           storage = None
        else:
           if totAllocStorage == None:
              totAllocStorage = 0
           totAllocStorage = totAllocStorage + storage

        if (bandwidth == -1):
           bandwidth = None
        else:
           if totAllocBandwidth == None:
              totAllocBandwidth = 0
           totAllocBandwidth = totAllocBandwidth + bandwidth

        ## finally add the zone to the top level allocation
        zonealloc = TopLevelAllocationByZone(top_level_allocation = tpAllocObject, zone = zoneRecord, hepspec = hepSpec, memory = memory, storage = storage, bandwidth = bandwidth)
        zonealloc.save()

    ## add the allowed resource types selected for each zone to the top level allocation allowed resource types
    index = 0
    for i in range(len(selZones)):
        zoneName = selZones[i]
        regionName = selRegions[i]
        zoneRecord = Zone.objects.get(name = zoneName, region__name = regionName)
        rtCount = float(selCountResourceTypes[i])
        k = 0
        while (k < rtCount):
           selResourceType = selAllocResourceTypes[index]
           resourceTypeRecord = ResourceType.objects.get(name = selResourceType)
           allowedResourceType = TopLevelAllocationAllowedResourceType(top_level_allocation = tpAllocObject, zone = zoneRecord, resource_type = resourceTypeRecord)
           allowedResourceType.save()
           index = index + 1
           k = k+1

    ## finally update the resource parameter values of the top level allocation object
    tpAllocObject.hepspec = totAllocHepSpec
    tpAllocObject.memory = totAllocMemory
    tpAllocObject.storage = totAllocStorage
    tpAllocObject.bandwidth = totAllocBandwidth

    return errorMessage

def checkAndUpdateZone(selRegion, selZone, tpAllocObject, currName, newHepSpec, newMemory, newStorage, newBandwidth,scale,storagescale):
    retMessage = ''
    retMessage = checkAttributeValues(newHepSpec, newMemory, newStorage, newBandwidth) 
    if retMessage != '':
       return retMessage
    ## Get the selected zone object of the top level allocation
    tpAllocZoneObject = None
    try:
      tpAllocZoneObject = TopLevelAllocationByZone.objects.get(top_level_allocation__name = currName, zone__name=selZone, zone__region__name=selRegion)
    except TopLevelAllocationByZone.DoesNotExist:
      return 'Selected Zone ' + selZone + ' of Region ' + selRegion + ' not found in top level allocation '

    ### Get this zone share values
    zoneShareHepSpec = tpAllocZoneObject.hepspec
    zoneShareMemory = tpAllocZoneObject.memory
    zoneShareStorage = tpAllocZoneObject.storage
    zoneShareBandwidth = tpAllocZoneObject.bandwidth

    ## if any of the new values are empty, then make them None i.e NULL or else round off to 3 decimal digits
    if newHepSpec == '':
       newHepSpec = None
    else:
       newHepSpec = round(float(newHepSpec), 3)
    if newMemory == '':
       newMemory = None
    else:
       newMemory = round(float(newMemory), 3)
    if newStorage == '':
       newStorage = None
    else:
       newStorage = round(float(newStorage), 3)
    if newBandwidth == '':
       newBandwidth = None
    else:
       newBandwidth = round(float(newBandwidth), 3)
    
    ## Its time to check if any of the resource parameter value has been increased, then whether
    ## the zone can fulfil this increase. Start by initializing the amount of increment for each parameter to 0
    ## also calculate the decrement values, if new values is less than old value (can be used to compare
    ## for the project allocations)
    hepSpecInc = 0;
    hepSpecDec = 0;
    memoryInc = 0;
    memoryDec = 0;
    storageInc = 0;
    storageDec = 0;
    bandwidthInc = 0;
    bandwidthDec = 0;

    ## calculate the increment for each parameter
    ## remember four combinations between old and new values 
    ## old - Null, new - Null;   old-Null, new - +ve value;  old - +ve value, new - Null, old - +ve value, new - +ve value;
    ## Null is less than +ve value
    if newHepSpec > zoneShareHepSpec:
       if zoneShareHepSpec == None:
          hepSpecInc = newHepSpec
       else:
          hepSpecInc = newHepSpec - zoneShareHepSpec
    elif newHepSpec < zoneShareHepSpec:
       if newHepSpec == None:
          hepSpecDec = zoneShareHepSpec
       else:
          hepSpecDec = zoneShareHepSpec - newHepSpec

    if newMemory > zoneShareMemory:
       if zoneShareMemory == None:
          memoryInc = newMemory
       else:
          memoryInc = newMemory - zoneShareMemory
    elif newMemory < zoneShareMemory:
       if newMemory == None:
          memoryDec = zoneShareMemory
       else:
          memoryDec = zoneShareMemory - newMemory

    if newStorage > zoneShareStorage:
       if zoneShareStorage == None:
          storageInc = newStorage
       else:
          storageInc = newStorage - zoneShareStorage
    elif newStorage < zoneShareStorage:
       if newStorage == None:
          storageDec = zoneShareStorage
       else:
          storageDec = zoneShareStorage - newStorage

    if newBandwidth > zoneShareBandwidth:
       if zoneShareBandwidth == None:
          bandwidthInc = newBandwidth
       else:
          bandwidthInc = newBandwidth - zoneShareBandwidth
    elif newBandwidth < zoneShareBandwidth:
       if newBandwidth == None:
          bandwidthDec = zoneShareBandwidth
       else:
          bandwidthDec = zoneShareBandwidth - newBandwidth

    ## check for the requested zone, whether this increment in resources are available or not. If not available then
    ## return an alert message
    if ( (hepSpecInc > 0) or (memoryInc > 0) or (storageInc > 0) or (bandwidthInc > 0) ):
       retMessage = checkZoneShareAvailability(selRegion, selZone, hepSpecInc, memoryInc, storageInc, bandwidthInc)
       if retMessage != '':
         return retMessage

    ## now calculate how much resources are already allocated to projects
    totAllocHepSpec = None
    totAllocMemory = None
    totAllocStorage = None
    totAllocBandwidth = None

    prAllocObjects = ProjectAllocation.objects.filter(top_level_allocation__name = currName)
    for oneObject in prAllocObjects:
        if oneObject.hepspec != None:
           if totAllocHepSpec == None:
              totAllocHepSpec = 0
           totAllocHepSpec = totAllocHepSpec + oneObject.hepspec
        if oneObject.memory != None:
           if totAllocMemory == None:
              totAllocMemory = 0
           totAllocMemory = totAllocMemory + oneObject.memory
        if oneObject.storage != None:
           if totAllocStorage == None:
              totAllocStorage = 0
           totAllocStorage = totAllocStorage + oneObject.storage
        if oneObject.bandwidth != None:
           if totAllocBandwidth == None:
              totAllocBandwidth = 0
           totAllocBandwidth = totAllocBandwidth + oneObject.bandwidth
 
    ## get the top level allocation total resource values
    totHepSpec = tpAllocObject.hepspec
    totMemory = tpAllocObject.memory
    totStorage = tpAllocObject.storage
    totBandwidth = tpAllocObject.bandwidth

    ## calculate the new top level allocation total resource values
    if (totHepSpec == None):
       totHepSpec = newHepSpec
    elif ( (totHepSpec != None) and (newHepSpec == None) ):
       if zoneShareHepSpec != None:
          totHepSpec = totHepSpec - zoneShareHepSpec
    else:
       totHepSpec = totHepSpec + hepSpecInc - hepSpecDec

    if (totMemory == None):
       totMemory = newMemory
    elif ( (totMemory != None) and (newMemory == None) ):
       if zoneShareMemory != None:
          totMemory = totMemory - zoneShareMemory
    else:
       totMemory = totMemory + memoryInc - memoryDec
 
    if (totStorage == None): 
       totStorage = newStorage
    elif ( (totStorage != None) and (newStorage == None) ):
       if zoneShareStorage != None:
          totStorage = totStorage - zoneShareStorage
    else:
       totStorage = totStorage + storageInc - storageDec

    if (totBandwidth == None):
       totBandwidth = newBandwidth
    elif ( (totBandwidth != None) and (newBandwidth == None) ):
       if zoneShareBandwidth != None:
          totBandwidth = totBandwidth - zoneShareBandwidth
    else:
       totBandwidth = totBandwidth + bandwidthInc - bandwidthDec
    
    ## compare whether this new top level allocation total resource values are enought to meet the project allocations
    if ((scale is None) and (totAllocHepSpec > totHepSpec)) :
       retMessage = retMessage + "With the new Hepspec value, it is not possible to meet the existing project allocations. "
    if (totAllocMemory > totMemory) :
       retMessage = retMessage + "With the new Memory value, it is not possible to meet the existing project allocations. "
    if ((storagescale is None)) and (totAllocStorage > totStorage) :
       retMessage = retMessage + "With the new Storage value, it is not possible to meet the existing project allocations. "
    if (totAllocBandwidth > totBandwidth) :
       retMessage = retMessage + "With the new Bandwidth value, it is not possible to meet the existing project allocations."
    if retMessage != '':
       return retMessage

    ## if any of the resource values becomes zero, then to keep the consistency, make 0 as UNDEFINED i.e NULL
    ## for that parameter in both the top level allocation and in all the zone share
    if ( (totHepSpec == 0) or (totMemory == 0) or (totStorage == 0) or (totBandwidth == 0) ):
       if totHepSpec == 0:
          totHepSpec = None
          TopLevelAllocationByZone.objects.filter(top_level_allocation__name=currName).update(hepspec=None)
       if totMemory == 0:
          totMemory = None
          TopLevelAllocationByZone.objects.filter(top_level_allocation__name=currName).update(memory=None)
       if totStorage == 0:
          totStorage = None
          TopLevelAllocationByZone.objects.filter(top_level_allocation__name=currName).update(storage=None)
       if totBandwidth == 0:
          totBandwidth = None
          TopLevelAllocationByZone.objects.filter(top_level_allocation__name=currName).update(bandwidth=None)

    ## if all is well, then update the zone share in the top level allocation
    ## also, assign the new total values to the top level allocation object
    tpAllocZoneObject.hepspec = newHepSpec
    tpAllocZoneObject.memory = newMemory
    tpAllocZoneObject.storage = newStorage
    tpAllocZoneObject.bandwidth = newBandwidth
    tpAllocZoneObject.save()

    tpAllocObject.hepspec = totHepSpec
    tpAllocObject.memory = totMemory
    tpAllocObject.storage = totStorage
    tpAllocObject.bandwidth = totBandwidth

    return retMessage

def getzoneresourceinfo(request):
    ## if the request is through ajax, then return the json object, otherwise return status 400 - BAD REQUEST 
    #if request.is_ajax():
        format = 'json'
        mimetype = 'application/javascript'

        selRegion = request.REQUEST.get("regionname", "")
        selZone = request.REQUEST.get("zonename", "")
        selAllocName = request.REQUEST.get("name", "")

        ##Get the zone share details of this top level allocation
        allocZoneInfo = TopLevelAllocationByZone.objects.get(top_level_allocation__name = selAllocName, zone__name=selZone, zone__region__name=selRegion)
 
        ## frame an object giving this zone share details
        zoneShareInfo = []
        zoneShareInfo.append({"pk": allocZoneInfo.id, "model": "cloudman.toplevelallocationbyzone", "region": selRegion, "zone": selZone, "fields": {"hepspec": allocZoneInfo.hepspec, "memory": allocZoneInfo.memory, "storage": allocZoneInfo.storage, "bandwidth": allocZoneInfo.bandwidth}})

        ## Now, get how much of this zone resources are already allocated in the top level allocations 
        ## inclusive of this top level allocation
        zoneTotResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None} 
        zoneUsedResources = {'hepspec': 0, 'memory': 0, 'storage': 0, 'bandwidth': 0}
        errorMessage = getzonetotalallocinfo(zoneTotResources, zoneUsedResources, selZone, selRegion)
 
        zoneShareInfo.append({"pk": selZone, "model": "cloudman.zoneallocinfo", "region": selRegion, "fields": {"tothepspec": zoneTotResources['hepspec'], "totmemory": zoneTotResources['memory'], "totstorage": zoneTotResources['storage'], "totbandwidth": zoneTotResources['bandwidth'], "usedhepspec": zoneUsedResources['hepspec'], "usedmemory": zoneUsedResources['memory'], "usedstorage": zoneUsedResources['storage'], "usedbandwidth": zoneUsedResources['bandwidth']}})

        ## finally dump the data into json object
        data = simplejson.dumps(zoneShareInfo)
        return HttpResponse(data,mimetype)
    # If you want to prevent non AJAX calls
    #else:        
    #    return HttpResponse(status=400)

def getzonetotalallocinfo(zoneTotResources, zoneUsedResources, selZone, selRegion):
    retMessage = ''
    try:
       ## First get the total available resources in the selected zone
       zoneObject = Zone.objects.get(name = selZone, region__name = selRegion)
       zoneTotHepSpecs = None
       if (zoneObject.hepspecs != None):
          zoneTotHepSpecs = round((zoneObject.hepspecs * zoneObject.hepspec_overcommit), 3)
       zoneTotMemory = None
       if (zoneObject.memory != None):
          zoneTotMemory = round((zoneObject.memory * zoneObject.memory_overcommit), 3)
       zoneTotStorage = None
       if (zoneObject.storage != None):
          zoneTotStorage = zoneObject.storage
       zoneTotBandwidth = None
       if (zoneObject.bandwidth != None):
          zoneTotBandwidth = zoneObject.bandwidth

       usedHepSpecs = 0
       usedMemory = 0
       usedStorage = 0
       usedBandwidth = 0

       ## Get all the top level allocation where this zone is used
       zoneUsedObjects = TopLevelAllocationByZone.objects.filter(zone__name = selZone, zone__region__name=selRegion)
       for oneObject in zoneUsedObjects:
          if (oneObject.hepspec != None):             
             usedHepSpecs = usedHepSpecs + oneObject.hepspec
          if (oneObject.memory != None):
             usedMemory = usedMemory + oneObject.memory
          if (oneObject.storage != None):
             usedStorage = usedStorage + oneObject.storage
          if (oneObject.bandwidth != None):
             usedBandwidth = usedBandwidth + oneObject.bandwidth

       ## assign the total and used information to the dictionary objects
       zoneTotResources['hepspec'] = zoneTotHepSpecs
       zoneTotResources['memory'] = zoneTotMemory
       zoneTotResources['storage'] = zoneTotStorage
       zoneTotResources['bandwidth'] = zoneTotBandwidth

       zoneUsedResources['hepspec'] = usedHepSpecs
       zoneUsedResources['memory'] = usedMemory
       zoneUsedResources['storage'] = usedStorage
       zoneUsedResources['bandwidth'] = usedBandwidth
    except Exception, err:
       retMessage = retMessage + "Exception arised while calculating the zone used allocations, reason : %s" % str(err)
    return retMessage

def listonlynames(request):
    tpAllocNameList = TopLevelAllocation.objects.all().values('name').order_by('name')
    return render_to_response('toplevelallocation/listonlynames.html',locals(),context_instance=RequestContext(request))

#####
### The following functions are not used as of now
#####
#####
def getregionshepspecspiechart(request):
    allocName = request.REQUEST.get("name", "")
    allocInfo = TopLevelAllocation.objects.get(name=allocName)
    allocZonesInfo = TopLevelAllocationByZone.objects.filter(top_level_allocation__name = allocName).values_list('hepspec_fraction', 'zone__name', 'zone__region__name', 'zone__hepspecs', 'zone__hepspec_overcommit').order_by('zone__name')
    totHepSpecsAlloc = 0
    if (allocInfo.hepspec != None):
       totHepSpecsAlloc = allocInfo.hepspec

    regionsInfo = {}
    for oneZone in allocZonesInfo:
        hepspec_fraction = oneZone[0]
        zoneName = oneZone[1]
        regionName = oneZone[2]
        zoneTotHepSpecs = 0
        if (oneZone[3] != None):
           zoneTotHepSpecs = oneZone[3] * oneZone[4]
        if not (regionName in regionsInfo):
           regionsInfo[regionName] = {'zones': [], 'hepspec_fraction': [], 'zonetothepspecs': []}
        regionsInfo[regionName]['zones'].append(zoneName)
        regionsInfo[regionName]['hepspec_fraction'].append(hepspec_fraction)
        regionsInfo[regionName]['zonetothepspecs'].append(zoneTotHepSpecs)

    #{u'CERN-Meyrin': {'zones': [u'1', u'test_zone'], 'zonetothepspecs': [100.0, 100.0], 'hepspec_fraction': [5.0, 5.0]}}
    # This loop is just for in case when same zone from same region is allotted more than once for a top level allocation (which is not allowed ..but just to be very much sure)

    for oneRegion in regionsInfo.iterkeys():
        zonesList = regionsInfo[oneRegion]['zones']
        hepspec_fractionList = regionsInfo[oneRegion]['hepspec_fraction']
        zoneTotHepSpecsList = regionsInfo[oneRegion]['zonetothepspecs']
      
        zonesFinalList = []
        hepspec_fractionFinalList = []
        zoneTotHepSpecsFinalList = []
        foundIndex = 0
        for i in range(len(zonesList)):
            currZoneName = zonesList[i]
            currHepSpecsFraction = hepspec_fractionList[i]
            if currHepSpecsFraction == None:
               currHepSpecsFraction = 0
            currZoneTotHepSpecs = zoneTotHepSpecsList[i]
            if currZoneTotHepSpecs == None:
               currZoneTotHepSpecs = 0
            foundIndex = -1
            for j in range(len(zonesFinalList)):
                if zonesFinalList[j] == currZoneName:
                   foundIndex = j
                   break
            if foundIndex >= 0:
                hepspec_fractionFinalList[j] = hepspec_fractionFinalList[j] + currHepSpecsFraction
            else:
               zonesFinalList.append(currZoneName)
               hepspec_fractionFinalList.append(currHepSpecsFraction)
               zoneTotHepSpecsFinalList.append(currZoneTotHepSpecs)
        regionsInfo[oneRegion]['totalloc'] = 0
        for i in range(len(zonesFinalList)):
            currZoneName = zonesFinalList[i]
            currHepSpecsFraction = hepspec_fractionFinalList[i]
            currZoneTotHepSpecs = zoneTotHepSpecsFinalList[i]
            zoneAllocHepSpecs = round(((currZoneTotHepSpecs * currHepSpecsFraction)/100), 3)
            regionsInfo[oneRegion]['totalloc'] = regionsInfo[oneRegion]['totalloc'] + zoneAllocHepSpecs
   
    fig = Figure(figsize=(4,4))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    labels = []
    fracs = []
    for oneRegion in regionsInfo.iterkeys():
        regionAllocHepSpecs = regionsInfo[oneRegion]['totalloc']
        regionPerFromTotal = 0
        if (totHepSpecsAlloc > 0):
            regionPerFromTotal = round(((regionAllocHepSpecs * 100)/totHepSpecsAlloc), 3)
        labels.append(oneRegion + '\n' + str(regionAllocHepSpecs))
        fracs.append(regionPerFromTotal)

    patches, texts, autotexts = ax.pie(fracs, explode=None, labels=labels, colors=('g', 'b', 'c', 'm', 'y', 'k', 'w', 'r'), autopct='%.2f%%', pctdistance=0.4, labeldistance=0.8, shadow=False)
    ax.set_title('Region - Hepspec Allocation for ' + allocName + '\n')
    ax.grid(True)
    response=django.http.HttpResponse(content_type='image/png')
    canvas.print_png(response)
    canvas.draw()
    return response

def getzoneshepspecspiechart(request):
    allocName = request.REQUEST.get("name", "")
    regionName = request.REQUEST.get("regionname", "")
    allocZonesInfo = TopLevelAllocationByZone.objects.filter(top_level_allocation__name = allocName, zone__region__name=regionName).values_list('hepspec_fraction', 'zone__name', 'zone__hepspecs', 'zone__hepspec_overcommit').order_by('zone__name')

    zonesInfo = {}
    for oneZone in allocZonesInfo:
        hepspec_fraction = oneZone[0]
        if hepspec_fraction == None:
           hepspec_fraction = 0
        zoneName = oneZone[1]
        zoneTotHepSpecs = oneZone[2]
        if zoneTotHepSpecs == None:
           zoneTotHepSpecs = 0
        else:
           zoneTotHepSpecs = zoneTotHepSpecs * oneZone[3]
        if zoneName in zonesInfo:
           zonesInfo[zoneName]['hepspec_fraction'] = zonesInfo[zoneName]['hepspec_fraction'] + hepspec_fraction
        else:
           zonesInfo[zoneName] = {'hepspec_fraction': 0, 'zonetothepspecs': 0}
           zonesInfo[zoneName]['hepspec_fraction'] = hepspec_fraction
           zonesInfo[zoneName]['zonetothepspecs'] = zoneTotHepSpecs

    totalAllocFromRegion = 0
    for oneZone in zonesInfo.iterkeys():
        hepspec_fraction = zonesInfo[oneZone]['hepspec_fraction']
        zoneTotHepSpecs = zonesInfo[oneZone]['zonetothepspecs']
        zoneAllocation = round(((hepspec_fraction * zoneTotHepSpecs)/100), 3)
        zonesInfo[oneZone]['hepspec_value'] = zoneAllocation
        totalAllocFromRegion = totalAllocFromRegion + zoneAllocation
    fig = Figure(figsize=(4,4))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    labels = []
    fracs = []
    for oneZone in zonesInfo.iterkeys():
        hepspec_fraction = zonesInfo[oneZone]['hepspec_fraction']
        zoneTotHepSpecs = zonesInfo[oneZone]['zonetothepspecs']
        zoneAllocHepSpecs = (zoneTotHepSpecs * hepspec_fraction)/100
        zonePerFromTotal = 0
        if totalAllocFromRegion > 0:
           zonePerFromTotal = round(((zoneAllocHepSpecs * 100)/totalAllocFromRegion), 3)
        labels.append(oneZone + "\n " + str(round(zoneAllocHepSpecs, 3)))
        fracs.append(zonePerFromTotal)
    patches, texts, autotexts = ax.pie(fracs, explode=None, labels=labels, colors=('g', 'b', 'c', 'm', 'y', 'k', 'w', 'r'), autopct='%.2f%%', pctdistance=0.4, labeldistance=0.8, shadow=False)
    ax.set_title('Hepspec Allocation in Region - ' + regionName + '\n')
    ax.grid(True)
    #fontP = FontProperties()
    #fontP.set_size('small')
    #ax.legend("1", prop = fontP)
    response=django.http.HttpResponse(content_type='image/png')
    canvas.print_png(response)
    canvas.draw()
    return response

def gethepspecspiechart(request):
    allocName = request.REQUEST.get("name", "")
    allocInfo = TopLevelAllocation.objects.get(name=allocName)
    #allocZonesInfo = TopLevelAllocationByZone.objects.filter(top_level_allocation__name = allocName).order_by('zone__name')
    allocZonesInfo = TopLevelAllocationByZone.objects.filter(top_level_allocation__name = allocName).values_list('hepspec_fraction', 'zone__name', 'zone__region__name', 'zone__hepspecs', 'zone__hepspec_overcommit').order_by('zone__name')
    totHepSpecsAlloc = allocInfo.hepspec
    if (allocInfo.hepspec == None):
       totHepSpecsAlloc = 0
    
    fig = Figure(figsize=(4,4))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    labels = []
    fracs = []
    for oneZone in allocZonesInfo:
        hepspec_fraction = oneZone[0]
        if hepspec_fraction == None:
           hepspec_fraction = 0
        zoneName = oneZone[1]
        regionName = oneZone[2]
        zoneTotHepSpecs = oneZone[3]
        if zoneTotHepSpecs == None:
           zoneTotHepSpecs = 0
        else:
           zoneTotHepSpecs = oneZone[3] * oneZone[4]
        zoneAllocHepSpecs = (zoneTotHepSpecs * hepspec_fraction)/100
        if totHepSpecsAlloc > 0:
           zonePerFromTotal = round(((zoneAllocHepSpecs * 100)/totHepSpecsAlloc), 3)
        labels.append("Region: " + regionName + "\n Zone: " + zoneName + "\n Fraction: " + str(round(zoneAllocHepSpecs, 3)))
        fracs.append(zonePerFromTotal)
       
    patches, texts, autotexts = ax.pie(fracs, explode=None, labels=labels, colors=('g', 'b', 'c', 'm', 'y', 'k', 'w', 'r'), autopct='%.2f', pctdistance=1.1, labeldistance=-0.4, shadow=False)
    ax.set_title('Hepspec Allocation\n')
    ax.grid(True)
    #fontP = FontProperties()
    #fontP.set_size('small')
    #ax.legend("1", prop = fontP)
    response=django.http.HttpResponse(content_type='image/png')
    canvas.print_png(response)
    canvas.draw()
    return response

def getTopAllocHepSpecPieChart(request):
    topLevelAllocationObjects = TopLevelAllocation.objects.all().values('hepspec')
    totalTopAllocHepSpecs = 0.0
    for oneObject in topLevelAllocationObjects:
        if (oneObject['hepspec'] != None):
           totalTopAllocHepSpecs = totalTopAllocHepSpecs + oneObject['hepspec']

    totalAllocHepSpecs = 0.0
    projectAllocationObjects = ProjectAllocation.objects.all().values('hepspec_fraction', 'top_level_allocation__hepspec')
    for oneObject in projectAllocationObjects:
        if ( (oneObject['hepspec_fraction'] != None) and (oneObject['top_level_allocation__hepspec'] != None) ):
            totalAllocHepSpecs = totalAllocHepSpecs + (oneObject['hepspec_fraction'] * oneObject['top_level_allocation__hepspec'])/100
    fig = Figure(figsize=(4,4))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    labels = []
    fracs = []
    allotedPer = 0
    if totalTopAllocHepSpecs > 0:
        allotedPer = round(((totalAllocHepSpecs/totalTopAllocHepSpecs) * 100), 3)
    freePer = 100 - allotedPer
    labels.append('Allocated')
    fracs.append(allotedPer)
    labels.append('Free')
    fracs.append(freePer)
    patches, texts, autotexts = ax.pie(fracs, explode=None, labels=labels, colors=('r', 'g', 'c', 'm', 'y', 'k', 'w', 'b'), autopct='%.2f%%', pctdistance=0.4, labeldistance=1.1, shadow=False)
    ax.set_title('\n Total Hepspec - Top Level Alloction \n Total: ' + str(totalTopAllocHepSpecs), fontdict=None, verticalalignment='bottom')
    ax.grid(True)
    #fig.canvas.mpl_connect('button_press_event', onclick)
    response=django.http.HttpResponse(content_type='image/png')
    canvas.print_png(response)
    canvas.draw()
    return response
