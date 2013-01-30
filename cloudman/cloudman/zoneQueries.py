from django.http import HttpResponse
from django.http import HttpResponseRedirect
#from django.template import RequestContext
#from django.shortcuts import render_to_response
#from django.conf import settings
from models import Zone
from models import Region
from forms import ZoneForm
from forms import ResourceForm
from models import ZoneFormValidate
from models import TopLevelAllocationByZone
from models import ZoneAllowedResourceType
from django.db import transaction
from models import ResourceType
from getPrivileges import isSuperUser
from regionQueries import isAdminOfAnyRegion
from regionQueries import isAdminForRegion
from getCount import getRegionCount
from getCount import getResourceTypesCount
from django.core import serializers
from validator import *
from commonFunctions import *
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from validator import *


def checkNameIgnoreCase(regionName,zoneName):
	nameExists = False
	if Zone.objects.filter(region__name__iexact=regionName, name__iexact=zoneName).exists():
		nameExists = True
	return nameExists

@transaction.commit_on_success
def addnew(request):
	## The add zone function can be used in two ways.
	## one way, is to click add new zone from the zone list page.....
	## which will display all the regions and create a zone by selecting a region from the list
	## second way, is to click add new zone from the region detailed page...
	## which means you already selected the region and adding a zone in that region
	## that's why the following variable says whether you already selected region or not
	selRegionName = request.REQUEST.get("regionname", "")
	## Check if there are any regions defined. If not, then zones cannot be added
	regionsCount = getRegionCount()
	if (regionsCount == 0):
		message = "No Regions Defined. First create Region and then try to add Zone"
		html = "<html><body> %s.</body></html>" % message
		return HttpResponse(html)
	## Check if there are any resource types defined. If not, then zones cannot be added
	resourceTypesCount = getResourceTypesCount()
	if (resourceTypesCount == 0):
		message = "No Resource Types Defined. First create Resource Types and then try to add Zone"
		html = "<html><body> %s. </body></html>" % message
		return HttpResponse(html)
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';')
	userIsSuperUser = isSuperUser(groupsList)
	## If the request is through form submission, then try to add the region or else display the add form 
	if request.method == 'POST':
		redirectURL = '/cloudman/message/?msg='
		regionName = request.POST['region']
		zoneName = request.POST['name']
		description = request.POST['description']
		hepSpecs = request.POST['hepspecs']
		memory = request.POST['memory']
		storage = request.POST['storage']
		bandwidth = request.POST['bandwidth']
		hepSpec_overcommit = request.POST['hepspec_overcommit']
		memory_overcommit = request.POST['memory_overcommit']
		comment = request.POST['comment']
		try:
			validate_name(regionName)
			validate_name(zoneName)
			validate_descr(description)
			validate_float(hepSpecs)
			validate_int(memory)
			validate_int(storage)
			validate_float(bandwidth)
			validate_comment(comment)
			validate_float(hepSpec_overcommit)
			validate_float(memory_overcommit)
		except ValidationError as e:
			message ='Add Zone Form  '+', '.join(e.messages)
			html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/zone/list/\"></HEAD><body> %s.</body></html>" % message
			return HttpResponse(html)
		## check for uniqueness of this zone name in the region
		nameExists = checkNameIgnoreCase(regionName, zoneName)
		if nameExists:
			msgAlreadyExists = 'Zone Name ' + zoneName + ' in Region ' + regionName + ' already exists. Hence Add New Zone Operation Stopped'
			transaction.rollback()
			return HttpResponseRedirect(redirectURL + msgAlreadyExists)
		## check whether user has any of the following rights
		## cloudman resource manager privileges
		## If not, then has membership of region admin_group	 
		if not userIsSuperUser:
			userIsAdminOfRegion = isAdminForRegion(regionName, groupsList)
			if not userIsAdminOfRegion:
				message = "You neither have membership of administrative group of region " + regionName + " nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to add new Zone";
				return HttpResponseRedirect(redirectURL + message)
		## Get the Region Object
		try:
			region = Region.objects.get(name=regionName)
		except Region.DoesNotExist:
			errorMessage = 'No Record Found for Region ' + regionName + '. Hence Add New Zone Operation Stopped'
			return HttpResponseRedirect(redirectURL + errorMessage)
		## validate hepspec, memory, storage and bandwidth values
		errorMsg = checkAttributeValues(hepSpecs, memory, storage, bandwidth)
		if (errorMsg != ''):
			return HttpResponseRedirect(redirectURL + errorMsg)
		## validate hepspec over commit and memory over commit values
		if hepSpec_overcommit < 1:
			msgFailure = "Hepspec Over Commit value should be greater than or equal to 1. Hence Add Zone Operation Stopped"
			return HttpResponseRedirect(redirectURL + msgFailure)
		if memory_overcommit < 1:
			msgFailure = "Memory Over Commit value should be greater than or equal to 1. Hence Add Zone Operation Stopped"
			return HttpResponseRedirect(redirectURL + msgFailure)
		## get all the resource types check boxes values (resource type name), 
		## the allowed resource types for this zone will be the ones whose checkbox is selected
		totalResourceTypes = request.POST['totalresourcetypes']
		index = 1
		atleastOneRTsel = False
		resourceTypesList = []
		while index <= int(totalResourceTypes):
			if ('resourcetype'+str(index)) in request.POST.keys() :
				## if checkbox selected
				resourceTypesList.append(request.POST['resourcetype'+str(index)])
				atleastOneRTsel = True
			index = index + 1
		if not atleastOneRTsel:
			message = "No Resource Types selected that are allowed for this Zone. Hence Zone Add Operation Stopped"
			return HttpResponseRedirect(redirectURL + message)
		## get the resource type objects for all those that are selected
		resourceTypesFullInfoList = []
		msgSuccess = ''
		for oneRT in resourceTypesList:
			try:
				resourceType = ResourceType.objects.get(name=oneRT)
				resourceTypesFullInfoList.append(resourceType)
				msgSuccess = msgSuccess + ' ' + oneRT;
			except ResourceType.DoesNotExist:
				errorMessage = 'No Record Found for Resource Type ' + oneRT + '. Hence Add New Zone Operation Stopped'
				return HttpResponseRedirect(redirectURL + errorMessage)
		msgSuccess = 'New Zone ' + zoneName + ' added successfully ' + ' to Region ' + regionName + '. The allowed Resource Types are ' + msgSuccess
		if hepSpecs == '':
			hepSpecs = None
		else:
			hepSpecs = round((float(hepSpecs)), 3)
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
		## create the zone object and save it
		newzone = Zone(name=zoneName, description=description, region=region, hepspecs=hepSpecs, memory=memory, storage=storage, bandwidth=bandwidth, hepspec_overcommit=hepSpec_overcommit, memory_overcommit=memory_overcommit)
		newzone.save()
		## get the newly added zone object
		## add the allowed resource types for this zone
		addedZone = Zone.objects.get(name=zoneName, region=region)
		for oneRT in resourceTypesFullInfoList:
			zrt = ZoneAllowedResourceType(zone=addedZone, resource_type=oneRT)
			zrt.save()
		##Add the Log for Zone
		if addLog(request,zoneName,comment,addedZone,None,'zone','add',True):
			transaction.commit()
		else:
			transaction.rollback()
			msgSuccess = 'Error in creating new zone' + zoneName
			
		## return the success message to the user
		html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/zone/list/\"></HEAD><body> %s.</body></html>" % msgSuccess
		return HttpResponse(html)
	else:
		## Zone can be added provided you have any of the following privileges
		## cloudman resource manager privileges
		## only to regions for which user has membership of its admin_group
		if not userIsSuperUser:
			userIsAdmin = True
			## if region is not already selected, then check user has membership of atleast one region admin_group
			if selRegionName == '':
				userIsAdmin = isAdminOfAnyRegion(groupsList)
				if not userIsAdmin:
					message = "You neither have membership of administrative groups of any region nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to add new Zone";
					html = "<html><body> %s.</body></html>" % message
					return HttpResponse(html)
			else:
				userIsAdmin = isAdminForRegion(selRegionName, groupsList)
				if not userIsAdmin:
					message = "You neither have membership of administrative group of region " + selRegionName + " nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to add new Zone";
					html = "<html><body> %s.</body></html>" % message
					return HttpResponse(html)
		form = ZoneForm(userGroups=groupsList, superUserRights=userIsSuperUser)
                resourceForm=ResourceForm
	resourceType = ResourceType.objects.all()
	return render_to_response('zone/addnew.html',locals(),context_instance=RequestContext(request))

def listall(request):
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';') ;
	userIsSuperUser = isSuperUser(groupsList)
	zonesList = Zone.objects.all().order_by('name')
	## form an object for each region with its zones, top level allocation hepspec value and the total zone hepspecs
	regionsInfo = {}
	for oneZone in zonesList:
		hepspec = oneZone.hepspecs
		memory = oneZone.memory
		storage = oneZone.storage
		bandwidth = oneZone.bandwidth
		hepspec_overcommit = oneZone.hepspec_overcommit
		memory_overcommit = oneZone.memory_overcommit
		zoneName = oneZone.name
		regionName = oneZone.region.name
		if hepspec != None:
		   hepspec = hepspec * hepspec_overcommit
		else:
		   hepspec = 0
		if memory != None:
		   memory = memory * memory_overcommit
		else:
		   memory = 0
		if storage == None:
		   storage = 0
		if bandwidth == None:
		   bandwidth = 0
		if not (regionName in regionsInfo):
		   regionsInfo[regionName] = {'name': regionName, 'zones': [], 'hepspec': [], 'memory': [], 'storage': [], 'bandwidth': [], 
									  'totalhepspec': 0, 'totalmemory': 0, 'totalstorage': 0, 'totalbandwidth': 0} 
		regionsInfo[regionName]['zones'].append(zoneName)
		regionsInfo[regionName]['hepspec'].append(hepspec)
		regionsInfo[regionName]['memory'].append(memory)
		regionsInfo[regionName]['storage'].append(storage)
		regionsInfo[regionName]['bandwidth'].append(bandwidth)
		regionsInfo[regionName]['totalhepspec'] = regionsInfo[regionName]['totalhepspec'] + hepspec
		regionsInfo[regionName]['totalmemory'] = regionsInfo[regionName]['totalmemory'] + memory
		regionsInfo[regionName]['totalstorage'] = regionsInfo[regionName]['totalstorage'] + storage
		regionsInfo[regionName]['totalbandwidth'] = regionsInfo[regionName]['totalbandwidth'] + bandwidth
	return render_to_response('zone/listall.html',locals(),context_instance=RequestContext(request))

def getdetails(request):
	regionName = request.REQUEST.get("regionname", "")
	zoneName = request.REQUEST.get("zonename", "")
	redirectURL = '/cloudman/message/?msg='

	## Get the Zone Object
	zoneInfo = None
	try:
	   zoneInfo = Zone.objects.get(name=zoneName, region__name=regionName)
	except Zone.DoesNotExist:
	   errorMessage = 'Zone Name ' + zoneName + ' does not exists'
	   return HttpResponseRedirect(redirectURL + errorMessage)

	## Get the information of all the allowed resource types in this zone
	allowedResourceTypesList = ZoneAllowedResourceType.objects.filter(zone__name=zoneName, zone__region__name=regionName).select_related('resource_type').order_by('resource_type__name')

	## Get the Top Level Allocations alloted from this zone
	topLevelAllocationByZoneList = TopLevelAllocationByZone.objects.filter(zone__name=zoneName, zone__region__name=regionName).select_related('top_level_allocation','top_level_allocation__group','zone').order_by('top_level_allocation__name')
	#topLevelAllocationByZoneList = TopLevelAllocationByZone.objects.filter(zone__name=zoneName, zone__region__name=regionName).order_by('top_level_allocation__name')
	## find the total zone hepspec (remember hepspec_overcommit)
	totalZoneHepSpecs = zoneInfo.hepspecs
	if totalZoneHepSpecs == None:
	   totalZoneHepSpecs = 0
	else:
	   totalZoneHepSpecs = zoneInfo.hepspectotal()

	## calculate the total hepspec allocated to top level allocations
	totalAllocHepSpecs = 0.0
	for oneObject in topLevelAllocationByZoneList:
		if (oneObject.hepspec != None):
		   totalAllocHepSpecs = totalAllocHepSpecs + oneObject.hepspec
	object_id = zoneInfo.id
	changeLogList = getLog('zone',zoneName,object_id,None)
	return render_to_response('zone/getdetails.html',locals(),context_instance=RequestContext(request))

@transaction.commit_on_success
def delete(request):
	zoneName = request.REQUEST.get("zonename", "")
	regionName = request.REQUEST.get("regionname", "")
	comment = request.REQUEST.get("comment", "deleting")
	redirectURL = '/cloudman/message/?msg='
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';')

	## update operation is allowed for a user if he/she has any one of the following rights
	## cloudman resource manager privileges
	## or has membership of the admin_group of the region to which this zone belongs to

	userIsSuperUser = isSuperUser(groupsList)
	if not userIsSuperUser:
		userIsAdmin = isAdminForRegion(regionName, groupsList)
		if not userIsAdmin:
			message = "You neither have membership of administrative group of region " + regionName + " nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to delete Zone";
			html = "<html><body> %s.</body></html>" % message
			return HttpResponse(html)



	## Get the Zone Object
	zoneObject = None
	try:
	   zoneObject = Zone.objects.get(name=zoneName, region__name=regionName)
	except Zone.DoesNotExist:
	   failureMessage = "Zone with Name " + zoneName + " in Region " + regionName + " could not be found"
	   return HttpResponseRedirect(redirectURL+failureMessage)

	## check if any top level allocations have been made using this zone
	tpAllocNames = TopLevelAllocationByZone.objects.filter(zone__name__iexact = zoneName, zone__region__name__iexact=regionName).values_list('top_level_allocation__name', flat=True).order_by('top_level_allocation__name')

	## if yes, alert the user and stop delete operation
	finalMessage = ''
	tpAllocNamesList = list(tpAllocNames)
	if len(tpAllocNamesList) > 0:
	   finalMessage = finalMessage + "Top Level Allocation Names: " + (', '.join(tpAllocNamesList)) + "<br/>"
	if not finalMessage == '':
	   finalMessage = "Zone with Name " + zoneName + " in Region " + regionName + " Could not be deleted because it is being used in " + "<br/>" + finalMessage
	   html = "<html><body> %s</body></html>" % finalMessage
	   return HttpResponse(html)

	## finally delete the zone
	status = addLog(request,zoneName,comment,zoneObject,None,'zone','delete',False)		   	
	## If no allocations are present, then first delete the allowed resource types for this zone
	ZoneAllowedResourceType.objects.filter(zone__name__iexact = zoneName, zone__region__name__iexact=regionName).delete()
	zoneObject.delete()
	if status:
		transaction.commit()
		message = "Zone with Name " + zoneName + " in Region " + regionName + " deleted successfully "
	else:
		transaction.rollback()
		message = "Error in deleting Zone with Name " + zoneName + " in Region " + regionName 
	## return a success message to the user
	
	html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/zone/list/\"></HEAD><body> %s.</body></html>" % message
	return HttpResponse(html)

@transaction.commit_on_success
def update(request):
	regionName = request.REQUEST.get("regionname", "")
	zoneName = request.REQUEST.get("zonename", "")
	redirectURL = '/cloudman/message/?msg='
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';') 
	## update operation is allowed for a user if he/she has any one of the following rights
	## cloudman resource manager privileges
	## or has membership of the admin_group of the region to which this zone belongs to
	userIsSuperUser = isSuperUser(groupsList)
	if not userIsSuperUser:
		userIsAdmin = isAdminForRegion(regionName, groupsList)
		if not userIsAdmin:
		  message = "You neither have membership of administrative group of region " + regionName + " nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to Edit Zone";
		  html = "<html><body> %s.</body></html>" % message
		  return HttpResponse(html)

	## Get the Zone Object
	zoneObject = None
	try:
	   zoneObject = Zone.objects.get(name=zoneName, region__name=regionName)
	except Zone.DoesNotExist:
	   failureMessage = "Zone with Name " + zoneName + " in Region " + regionName + " could not be found"
	   return HttpResponseRedirect(redirectURL+failureMessage)
	oldZoneInfo = getZoneInfo(zoneObject)
	## if the request is from a update form submission, then try to update the values or else return to
	## display the form
	if request.method == 'POST':
	   ## Existing values
	   currRegionName = zoneObject.region.name
	   currName = zoneObject.name
	   currDescription = zoneObject.description
	   currHepSpec = zoneObject.hepspecs
	   currMemory = zoneObject.memory
	   currStorage = zoneObject.storage
	   currBandwidth = zoneObject.bandwidth
	   currHepspec_overcommit = zoneObject.hepspec_overcommit
	   currMemory_overcommit = zoneObject.memory_overcommit
	   currRTList = ZoneAllowedResourceType.objects.filter(zone__name=zoneName, zone__region__name=regionName).values_list('resource_type__name', flat=True)
	   ## new values
	   newRegionName = request.POST['region']
	   newName = request.POST['name']
	   newDescription = request.POST['description']
	   newHepSpec = request.POST['hepspecs']
	   newMemory = request.POST['memory']
	   newStorage = request.POST['storage']
	   newBandwidth = request.POST['bandwidth']
	   newHepspec_overcommit = request.POST['hepspec_overcommit']
	   newMemory_overcommit = request.POST['memory_overcommit']
	   newRTList = request.POST.getlist('zoneallowedrt')
	   comment = request.POST['comment']
	   try:
			validate_name(newRegionName)
			validate_name(newName)
			validate_descr(newDescription)
			validate_float(newHepSpec)
			validate_float(newMemory)
			validate_float(newStorage)
			validate_float(newBandwidth)
			validate_comment(comment)
	   except ValidationError as e:
			message ='Edit Zone Form  '+', '.join(e.messages)
			html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/zone/list/\"></HEAD><body> %s.</body></html>" % message
			return HttpResponse(html)
	   ## validate the new resource parameter values
	   errorMsg = checkAttributeValues(newHepSpec, newMemory, newStorage, newBandwidth)
	   if (errorMsg != ''):
		   return HttpResponseRedirect(redirectURL + errorMsg)

	   newHepspec_overcommit = float(newHepspec_overcommit)
	   newMemory_overcommit = float(newMemory_overcommit)
	   if newHepspec_overcommit < 1:
		   msgFailure = "Hepspec Over Commit value should be greater than or equal to 1. Hence Edit Zone Operation Stopped"
		   return HttpResponseRedirect(redirectURL + msgFailure)

	   if newMemory_overcommit < 1:
		   msgFailure = "Memory Over Commit value should be greater than or equal to 1. Hence Edit Zone Operation Stopped"
		   return HttpResponseRedirect(redirectURL + msgFailure)

	   ## check whether any new resource type has been selected or existing resource type is de-selected
	   rtNotChanged = True;
	   for newRt in newRTList:
		   if not newRt in currRTList:
			  rtNotChanged = False

	   for oldRt in currRTList:
		   if not oldRt in newRTList:
			  rtNotChanged = False

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

	   ## check if atleast one field value has been changed
	   if ( (currRegionName == newRegionName) and (currName == newName) and (currDescription == newDescription) and (currHepSpec == newHepSpec) and (currMemory == newMemory) and (currStorage == newStorage) and (currBandwidth == newBandwidth) and (currHepspec_overcommit == newHepspec_overcommit) and (currMemory_overcommit == newMemory_overcommit) and (rtNotChanged) ):
		   message = 'No New Value provided for any field to perform Edit Operation. Hence Edit Zone ' + zoneName + ' in Region ' + regionName + ' aborted'
		   return HttpResponseRedirect(redirectURL + message)

	   ## if region is changed, then validate it, check if user has either cloudman resource manager privileges
	   ## or new region admin_group membership
	   ## if all is fine, then assign the new region name and get the new Region Object 
	   if (currRegionName != newRegionName):
		  if newRegionName == '':
			 errorMsg = 'Region name field cannot be left blank. So Edit Zone operation stopped'
			 return HttpResponseRedirect(redirectURL + errorMsg)
		  # do for region
		  if not userIsSuperUser:
			 userIsAdmin = isAdminForRegion(newRegionName, groupsList)
			 if not userIsAdmin:
				message = "You neither have membership of administrative group of region " + newRegionName + " nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to shift Zone from Region " + currRegionName + " to Region " + newRegionName;
				html = "<html><body> %s.</body></html>" % message
				return HttpResponse(html) 
		  regionName = newRegionName
		  regionObject = None
		  try:
			 regionObject = Region.objects.get(name=newRegionName)
		  except Region.DoesNotExist:
			 errorMessage = 'No record found for Region with name ' + newRegionName + '. Hence Edit Zone operation stopped'
			 return HttpResponseRedirect(redirectURL + errorMessage)
		  zoneObject.region = regionObject

	   ## if zone name is changed, then validate it and assign the new name
	   if (currName != newName):
		   if (newName == ''):
			  errorMsg = 'Name name field cannot be left blank. So Edit Zone operation stopped'
			  return HttpResponseRedirect(redirectURL + errorMsg)
		   if (currRegionName != newRegionName):
			  nameExists = checkNameIgnoreCase(newRegionName, newName)
			  if nameExists:
				  msgAlreadyExists = 'Zone ' + newName + ' in Region ' + newRegionName + ' already exists. Hence Edit Zone Operation Stopped'
				  return HttpResponseRedirect(redirectURL + msgAlreadyExists);
		   else:
			  nameExists = checkNameIgnoreCase(currRegionName, newName)
			  if nameExists:
				  msgAlreadyExists = 'Zone ' + newName + ' in Region ' + currRegionName + ' already exists. Hence Edit Zone Operation Stopped'
				  return HttpResponseRedirect(redirectURL + msgAlreadyExists);
		   zoneObject.name = newName

	   ## check if description is changed and if so, assign the new value
	   if (currDescription != newDescription):
		   zoneObject.description = newDescription
	   
	   if ( (currHepSpec != newHepSpec) or (currMemory != newMemory) or (currStorage != newStorage) or (currBandwidth != newBandwidth) ):
		  newResourceValues = {'hepspecs': newHepSpec, 'memory': newMemory, 'storage': newStorage, 'bandwidth': newBandwidth, 'hepspec_overcommit': newHepspec_overcommit, 'memory_overcommit': newMemory_overcommit}	  
		  ## check whether top level allocations of this zone can be met with the new resource values
		  errorMessage = checkTpLevelAllocations(currName, currRegionName, newResourceValues)
		  if errorMessage != '':
			 return HttpResponseRedirect(redirectURL + errorMessage)

	   ## Assign the new resource values if changed
	   if (currHepSpec != newHepSpec):
		  zoneObject.hepspecs = newHepSpec
	   if (currMemory != newMemory):
		  zoneObject.memory = newMemory
	   if (currStorage != newStorage):
		  zoneObject.storage = newStorage
	   if (currBandwidth != newBandwidth):
		  zoneObject.bandwidth = newBandwidth
	   if (currHepspec_overcommit != newHepspec_overcommit):
		  zoneObject.hepspec_overcommit = newHepspec_overcommit
	   
	   if (currMemory_overcommit != newMemory_overcommit):
		  zoneObject.memory_overcommit = newMemory_overcommit

	   ## delete the resouce types which are de-selected
	   if not rtNotChanged:
		  for oldRt in currRTList:
			 if not oldRt in newRTList:
			   try:
				  #rtObject = ResourceType.objects.get(name=oldRt)
				  zrt = ZoneAllowedResourceType.objects.get(resource_type__name=oldRt, zone__name=currName, zone__region__name=currRegionName)
				  zrt.delete()
			   except ZoneAllowedResourceType.DoesNotExist:
				  errorMessage = 'No Record Found for Resource Type ' + oldRt + '. Hence Edit Zone Operation Stopped'
				  return HttpResponseRedirect(redirectURL + errorMessage)

	   ## Finally save all the zone object changes	   
	   zoneObject.save()
	  # newZoneObj = copy.copy(zoneObject)

	   ## if a new resource type is selected, then add it to the zone allowed resource type table
	   if not rtNotChanged:
		  for newRt in newRTList:
			 if not newRt in currRTList:
				try:
				   rtObject = ResourceType.objects.get(name=newRt)
				   zrt = ZoneAllowedResourceType(zone=zoneObject, resource_type=rtObject)
				   zrt.save()
				except Exception, err:
				   errorMessage = "Error in Creating Zone Allowed Resource Type , reason : %s" % str(err)
				   return HttpResponseRedirect(redirectURL + errorMessage)

	   #Write The Log
  	   newZoneInfo = getZoneInfo(zoneObject)
	   objectId = zoneObject.id 	   
	   if addUpdateLog(request,newName,objectId,comment,oldZoneInfo,newZoneInfo,'zone',True):
	   		transaction.commit()
	   	 	message = 'Zone ' + zoneName + ' in Region ' + currRegionName + ' Successfully Updated'
	   else:
	   		transaction.rollback()
	   		message = 'Error in updating Zone ' + zoneName + ' in Region ' + currRegionName 
	   ## Finally display a success message to the user
	   html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/zone/list/\"></HEAD><body> %s.</body></html>" % message
	   return HttpResponse(html)
	## The request POST condition ends here 
	## Get all the information required to display the update form
	## Zone can be moved from one region to region
	## Get the all regions list if user has resource manager privileges
	## else zone can be moved to only those regions in which user is member of its admin_group
	regionList = None
	if userIsSuperUser:
	   regionList = Region.objects.all().values_list('name', flat=True)
	else:
	   qset = Q(admin_group__exact=groupsList[0])
	   if len(groupsList) > 1:
		  for group in groupsList[1:]:
			qset = qset | Q(admin_group__exact=group)
	   regionList = Region.objects.filter(qset).values_list('name', flat=True)
	## Get the current zone allowed resource types
	zoneRTList = ZoneAllowedResourceType.objects.filter(zone__name=zoneName, zone__region__name=regionName).values_list('resource_type__name', flat=True)
	## Get all the resource types 
	resourceTypeList = ResourceType.objects.all().values_list('name', flat=True)
	return render_to_response('zone/update.html',locals(),context_instance=RequestContext(request))

def checkTpLevelAllocations(zoneName, regionName, newResourceValues):
	## This fuctions is used to check when zone resource values are changed, then whether
	## the existing top level allocations can be met
	## if not then return an error message or else return empty message
	## Get all the top level allocations made using this zone
	tpZoneAllocObjects = TopLevelAllocationByZone.objects.filter(zone__name = zoneName, zone__region__name = regionName)
	## calculate the sum of hepspec, memory, storage and bandwidth for all these top level allocations
	totalAllocHepSpec = None
	totalAllocMemory = None
	totalAllocStorage = None
	totalAllocBandwidth = None
	for oneAlloc in tpZoneAllocObjects:
	   if (oneAlloc.hepspec != None):
		  if totalAllocHepSpec == None:
			 totalAllocHepSpec = 0
		  totalAllocHepSpec = totalAllocHepSpec + oneAlloc.hepspec
	   if (oneAlloc.memory != None):
		  if totalAllocMemory == None:
			 totalAllocMemory = 0
		  totalAllocMemory = totalAllocMemory + oneAlloc.memory
	   if (oneAlloc.storage != None):
		  if totalAllocStorage == None:
			 totalAllocStorage = 0
		  totalAllocStorage = totalAllocStorage + oneAlloc.storage
	   if (oneAlloc.bandwidth != None):
		  if totalAllocBandwidth == None:
			 totalAllocBandwidth = 0
		  totalAllocBandwidth = totalAllocBandwidth + oneAlloc.bandwidth
	## Get the new resource values 
	newHepSpec = None
	newMemory = None
	if (newResourceValues['hepspecs'] != None):
	   newHepSpec = newResourceValues['hepspecs'] * newResourceValues['hepspec_overcommit']
	if (newResourceValues['memory'] != None):
	   newMemory = newResourceValues['memory'] * newResourceValues['memory_overcommit']
	newStorage = newResourceValues['storage']
	newBandwidth = newResourceValues['bandwidth']	 

	## check if with the new resource values the total allocation calculated above can be met
	errorMessage = ''
	if (totalAllocHepSpec > newHepSpec):
	   errorMessage = errorMessage + 'The total alloted Top Level Allocation Hepspec from this zone is greater than the new Hepspec * Hepspec_overcommit Value. '
	if (totalAllocMemory > newMemory):
	   errorMessage = errorMessage + 'The total alloted Top Level Allocation Memory from this zone is greater than the new Memory * Memory_overcommit Value. '
	if (totalAllocStorage > newStorage):
	   errorMessage = errorMessage + 'The total alloted Top Level Allocation Storage from this zone is greater than the new Storage Value. '
	if (totalAllocBandwidth > newBandwidth):
	   errorMessage = errorMessage + 'The total alloted Top Level Allocation Bandwidth from this zone is greater than the new Bandwidth Value. '
   
	return errorMessage

def getallocationsinfo(request):
	## if the request is through ajax, then reply the json string or else return status 400 BAD REQUEST
	#if request.is_ajax():
		#format == 'xml' or 'json'
		#mimetype = 'application/xml' or 'application/javascript'
		format = 'json'
		mimetype = 'application/javascript'
 
		regionName = request.REQUEST.get("regionname", "")
		## Get all the zones in the region
		zonesObjects = Zone.objects.filter(region__name=regionName)
		zonesList = list(zonesObjects)
		if (len(zonesList) <= 0):
			data = serializers.serialize(format, zonesList)
			return HttpResponse(data,mimetype)

		## Get the Top Level Allocations made using zones of this region
		zonesUsedObjects = TopLevelAllocationByZone.objects.filter(zone__region__name=regionName)
		zonesUsedList = list(zonesUsedObjects)

		## Get all the allowed resource types of each zones of this region
		zoneResourceTypeObjects = ZoneAllowedResourceType.objects.filter(zone__region__name=regionName)
		zoneResourceTypeList = list(zoneResourceTypeObjects)
		resourceTypeIds = []
		resourceTypeList = []
		for oneRow in zoneResourceTypeObjects:
			resourceTypeIds.append(oneRow.resource_type.id)
		if len(resourceTypeIds) > 0:
		   resourceTypeObjects = ResourceType.objects.filter(id__in=resourceTypeIds)
		   resourceTypeList = list(resourceTypeObjects)

		## serialize all the data and send in json format
		data = serializers.serialize(format, (zonesList + zonesUsedList + zoneResourceTypeList + resourceTypeList))
		return HttpResponse(data,mimetype)
	# If you want to prevent non AJAX calls
	#else:
	#	 return HttpResponse(status=400)

## The following functions are not used as of now
def getZoneHepSpecsPieChart(request):
	regionName = request.REQUEST.get("regionname", "")
	zoneName = request.REQUEST.get("zonename", "")
	zoneInfo =	Zone.objects.get(name=zoneName, region__name=regionName)
	totalZoneHepSpecs = zoneInfo.hepspecs
	if totalZoneHepSpecs == None:
	   totalZoneHepSpecs = 0
	else:
	   totalZoneHepSpecs = zoneInfo.hepspectotal()

	topLevelAllocationByZoneObjects = TopLevelAllocationByZone.objects.filter(zone__name=zoneName, zone__region__name=regionName).values('hepspec_fraction')
	totalAllocHepSpecs = 0.0
	for oneObject in topLevelAllocationByZoneObjects:
		if (oneObject['hepspec_fraction'] != None):
		   totalAllocHepSpecs = totalAllocHepSpecs + ((oneObject['hepspec_fraction'] * totalZoneHepSpecs)/100)
	fig = Figure(figsize=(4,4))
	canvas = FigureCanvas(fig)
	ax = fig.add_subplot(111)
	labels = []
	fracs = []
	allotedPer = 0
	if totalZoneHepSpecs > 0:
		allotedPer = (totalAllocHepSpecs/totalZoneHepSpecs) * 100
	freePer = 100 - allotedPer
	labels.append('Free')
	fracs.append(freePer)
	if (allotedPer > 0):
	  labels.append('Allocated')
	  fracs.append(allotedPer)
	patches, texts, autotexts = ax.pie(fracs, explode=None, labels=labels, colors=('g', 'r', 'c', 'm', 'y', 'k', 'w', 'b'), autopct='%.2f%%', pctdistance=0.4, labeldistance=1.1, shadow=False)
	ax.set_title('\n Hepspec Allocation - Zone - ' + zoneName + '\n Region: ' + regionName + ' Total: ' + str(round(totalZoneHepSpecs, 3)), fontdict=None, verticalalignment='bottom')
	ax.grid(True)
	#fig.canvas.mpl_connect('button_press_event', onclick)
	response=HttpResponse(content_type='image/png')
	canvas.print_png(response)
	canvas.draw()
	return response

def allowedresourcetypes(request):
	redirectURL = '/cloudman/message/?msg='
	zoneName = request.REQUEST.get("zonename", "")
	regionName = request.REQUEST.get("regionname", "")
	#allowedResourceTypesList = ZoneAllowedResourceType.objects.filter(zone__name=zoneName, zone__region__name=regionName).values('resource_type__name', 'resource_type__resource_class', 'resource_type__hepspecs', 'resource_type__memory', 'resource_type__storage', 'resource_type__bandwidth')
	allowedResourceIds = ZoneAllowedResourceType.objects.filter(zone__name=zoneName, zone__region__name=regionName).values('resource_type')
	allowedResourceTypesList = ResourceType.objects.filter(id__in=allowedResourceIds)
	return render_to_response('listzoneresourcetypes.html',locals(),context_instance=RequestContext(request))
