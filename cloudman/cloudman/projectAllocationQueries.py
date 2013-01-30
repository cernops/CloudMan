from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext, loader, Context
from django.shortcuts import render_to_response
from django.conf import settings
from models import Project
from templatetags.filters import displayNone 
from models import Groups,TopLevelAllocation,GroupAllocation,ProjectAllocationAllowedResourceType,ResourceType,ProjectAllocationAllowedResourceType
from forms import ProjectAllocationForm
from forms import ResourceForm
from models import ProjectAllocation
from models import ProjectMetadata
from models import ProjectAllocationMetadata
from getCount import getTopLevelAllocationsCount
from getCount import getProjectsCount
from getCount import getGroupsCount
from django.db import transaction
from logQueries import printStackTrace
from getPrivileges import isSuperUser
from projectQueries import isAdminOfAnyProject
from projectQueries import isAdminOfProject
from validator import *
from topLevelAllocationQueries import isAdminOfAnyTopLevelAllocation
from topLevelAllocationQueries import isAdminOfTopLevelAllocation
from django.db.models import Q
import getConfig
import django
from matplotlib import font_manager as fm
import simplejson
from commonFunctions import *
from topLevelAllocationQueries import getstats as tpallocgetstats
import sys ,traceback
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

def delUpdateAllowed(groupsList,tpAllocName,projectName):
	if isSuperUser(groupsList):
		return True
	else:
		if isAdminOfTopLevelAllocation(groupsList, tpAllocName) or isAdminOfProject(groupsList, projectName):
			return True
		else:
			return False


def checkNameIgnoreCase(allocName):
	allocNameExists = False
	if ProjectAllocation.objects.filter(name__iexact=allocName).exists():
		allocNameExists = True
	return allocNameExists

def isAdminOfProjectAllocation(adminGroups, projectAllocationName):
	userIsAdmin = False
	if len(adminGroups) < 1:
	   return userIsAdmin
	try:
	   prAllocObject = ProjectAllocation.objects.get(name=projectAllocationName)
	   projectGroup = prAllocObject.project.admin_group
	   prAllocGroup = prAllocObject.group.admin_group
		
	   for oneGroup in adminGroups:
		   if oneGroup == prAllocGroup:
			  userIsAdmin = True
			  break
		   if oneGroup == projectGroup:
			  userIsAdmin = True
			  break
	except Exception, err:
	   userIsAdmin = False
	return userIsAdmin

def isAdminOfAnyProjectAllocation(adminGroups):
	userIsAdmin = False
	if len(adminGroups) < 1:
	   return userIsAdmin
	qset = Q(project__admin_group__exact=adminGroups[0])
	group_qset =Q(group__admin_group__exact=adminGroups[0])
	if len(adminGroups) > 1:
	   for group in adminGroups[1:]:
		 qset = qset | Q(project__admin_group__exact=group)
		 group_qset = group_qset |	Q(group__admin_group__exact=group)
	if (ProjectAllocation.objects.filter(qset|group_qset)).exists():
		userIsAdmin = True
	return userIsAdmin

@transaction.commit_on_success
def addnew(request):
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';')
	## Project allocation is possible, if the following things are available
	## atleast one group
	## atleast one top level allocation
	## atleast one project
	groupsCount = getGroupsCount()
	if groupsCount <= 0:
		message = "No Groups Defined. First create Groups and then try to define Project Allocation";
		html = "<html><body> %s.</body></html>" % message
		return HttpResponse(html)
	topLevelAllocationsCount = getTopLevelAllocationsCount()
	if topLevelAllocationsCount <= 0:
		message = "No Top Level Allocations Defined. First create Top Level Allocations and then try to define Project Allocation";
		html = "<html><body> %s.</body></html>" % message
		return HttpResponse(html)
	projectsCount = getProjectsCount()
	if projectsCount <= 0:
		message = "No Projects Defined. First create Projects and then try to define Project Allocation";
		html = "<html><body> %s.</body></html>" % message
		return HttpResponse(html)
	## If the request is through form submission, then try to create the allocation
	## or else return a form for creating new project allocation
	if request.method == 'POST':
		   redirectURL = '/cloudman/message/?msg='
		   ## check the specified name uniquess for project allocation
		   allocName = request.REQUEST.get("name", "")
		   allocNameExists = checkNameIgnoreCase(allocName)
		   if allocNameExists:
			  msgAlreadyExists = 'Allocation Name ' + allocName + ' already exists. Hence New Project Allocation Creation Stopped'
			  return HttpResponseRedirect(redirectURL + msgAlreadyExists)
		   ## Get the remaining fields input values
		   topLevelAllocationName = request.REQUEST.get("top_level_allocation", "")
		   projectName = request.REQUEST.get("project", "")
		   groupName = request.REQUEST.get("group", "")			  
		   hepspec = request.REQUEST.get("hepspecs", "")
		   memory = request.REQUEST.get("memory", "")
		   storage = request.REQUEST.get("storage", "")
		   bandwidth = request.REQUEST.get("bandwidth", "")
		   selAllocResourceTypes = request.REQUEST.getlist("selresourcetype")
		   comment = request.REQUEST.get("comment", "")
		   attr_name_array = request.REQUEST.getlist('attribute_name');
		   attr_value_array = request.REQUEST.getlist('attribute_value');
		   try:
				validate_name(allocName)
				validate_name(topLevelAllocationName)
				validate_name(projectName)
				validate_name(groupName)
				validate_float(hepspec)
				validate_float(memory)
				validate_float(storage)
				validate_float(bandwidth)				
				validate_comment(comment)				
		   except ValidationError as e:
				msg = 'Add ProjectAllocation Form  '+', '.join(e.messages)
				html = "<html><head><meta HTTP-EQUIV=\"REFRESH\" content=\"5; url=/cloudman/projectallocation/list/\"></head><body> %s.</body></html>" % msg
				return HttpResponse(html)
			
		   ## allocation is allowed only if user has 
		   ## either cloudman resource manager privileges
		   ## or membership of admin group of both selected top level allocation and project		   
		   userIsSuperUser = isSuperUser(groupsList)
		   if not userIsSuperUser:
			  userIsAdmin = isAdminOfTopLevelAllocation(groupsList, topLevelAllocationName)
			  if not userIsAdmin:
				message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Group of the Group for which the Top Level Allocation " + topLevelAllocationName + " is created . Hence you are not authorized to create Project Allocation";
				html = "<html><body> %s.</body></html>" % message
				return HttpResponse(html)
#			  userIsAdmin = isAdminOfProject(groupsList, projectName)
#			  if not userIsAdmin:
#				message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Groups assigned to the Project " + projectName + ". Hence you are not authorized to create Project Allocation";
#				html = "<html><body> %s.</body></html>" % message
#				return HttpResponse(html)
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
		   ## Get the top level allocation Object
		   topLevelAllocationObject = None
		   try:
			   topLevelAllocationObject = TopLevelAllocation.objects.get(name=topLevelAllocationName)
		   except TopLevelAllocation.DoesNotExist:
			   errorMessage = 'Top Level Allocation Name ' + topLevelAllocationName + ' does not exists'
			   return HttpResponseRedirect(redirectURL + errorMessage)
		   ## Get the project object
		   projectObject = None
		   try:
			   projectObject = Project.objects.get(name=projectName)
		   except Project.DoesNotExist:
			   errorMessage = 'Project Name ' + projectName + ' does not exists'
			   return HttpResponseRedirect(redirectURL + errorMessage)
		   ## Get the group object
		   groupObject = None
		   try:
			   groupObject = Groups.objects.get(name=groupName)
		   except Groups.DoesNotExist:
			   errorMessage = 'Groups Name ' + groupName + ' does not exists'
			   return HttpResponseRedirect(redirectURL + errorMessage)
		   ## initialize three dict, one each for total, free and used fraction resource parameter values
		   ## get these values from the selected top level allocation 
		   totResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
		   freeResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
		   usedFraction = {'hepspec': 0, 'memory': 0, 'storage': 0, 'bandwidth': 0 }
		   ## call this function to calculate the above defined values
		   errorMessage = tpallocgetstats(topLevelAllocationName, totResources, freeResources, usedFraction)
		   if errorMessage != '':
			   return HttpResponseRedirect(redirectURL + errorMessage)
		   ## check whether the selected resource parameter values are available in the top level allocation
		   if (hepspec > freeResources['hepspec']):
			   message = "The Requested Hepspec value is greater than the available Hepspec"
			   return HttpResponseRedirect(redirectURL + message)
		   if (memory > freeResources['memory']):
			   message = "The Requested Memory value is greater than the available Memory"
		   if (storage > freeResources['storage']):
			   message = "The Requested Storage value is greater than the available Storage"
		   if (bandwidth > freeResources['bandwidth']):
			   message = "The Requested Bandwidth value is greater than the available Bandwidth"
		   ## create the project allocation with all the input values
		   finalMessage = ''
		   attr_list = createDictFromList(attr_name_array,attr_value_array)
		   try:
			  pralloc = ProjectAllocation(name = allocName, top_level_allocation = topLevelAllocationObject, project = projectObject, group = groupObject, hepspec = hepspec, memory = memory, storage = storage, bandwidth = bandwidth)
			  pralloc.save()
			  prAllocObj = ProjectAllocation.objects.get(name = allocName)
			  
			  for attr_name,attr_value	in attr_list.items():
				  pralloc_metadata = ProjectAllocationMetadata(attribute = attr_name,value = attr_value,project = projectObject,project_allocation = prAllocObj)
				  pralloc_metadata.save()
		   except Exception, err:
			  finalMessage = "Error in Creating Project Allocation , reason : %s" % str(err)
			  html = "<html><body> %s.</body></html>" % finalMessage
			  transaction.rollback()
			  return HttpResponse(html)
		   finalMessage = "Project Allocation Created Successfully with Name %s using Top Level Allocation %s for Project %s in Group %s with %s Hepspec, %s Memory, %s Storage, %s Bandwidth " % (allocName, topLevelAllocationName, projectName, groupName, (str(hepspec)), (str(memory)), (str(storage)), (str(bandwidth)) )
		   finalMessage += "<br/><br/>"; 
		   ## create the project allocation allowed resource types
		   rtList = []
		   pralloc = None
		   try:
			  pralloc = ProjectAllocation.objects.get(name = allocName)
			  finalMessage += " Assigning Allowed Resource Types to Allocation : <br/>"
			  for i in range(len(selAllocResourceTypes)):
				selResourceType = selAllocResourceTypes[i]
				if selResourceType not in rtList:
				   rtList.append(selResourceType)
				   finalMessage += " Resource Type Name: " + selResourceType + "<br/>"
				   resourceTypeRecord = ResourceType.objects.get(name = selResourceType)
				   allowedResourceType = ProjectAllocationAllowedResourceType(project_allocation = pralloc, resource_type = resourceTypeRecord)
				   allowedResourceType.save()
		   except Exception, err:
			  finalMessage += "Exceptin Arised while Assinging Allowed Resources Types for the Project Allocation, reason : %s " %str(err)
			  finalMessage += "<br/> Hence Project Allocation Creation Stopped Here (and also record cleared completely)."
			  pralloc.delete()
			  transaction.commit()
			  html = "<html><body> %s.</body></html>" % finalMessage
			  return HttpResponse(html)
		   ##Write the Log
		   prAllocObj = ProjectAllocation.objects.get(name = allocName)
		   if not addLog(request,allocName,comment,prAllocObj,None,'projectallocation','add',True):
		   		transaction.rollback()
		   ## finally, return a successful message to the user
		   finalMessage += "<br/> Project Allocation Creation Successfully Completed";
		   html = "<html><head><meta HTTP-EQUIV=\"REFRESH\" content=\"5; url=/cloudman/projectallocation/list/\"></head><body> %s.</body></html>" % finalMessage
		   return HttpResponse(html)
	## form post request if condition ends here - start of else block
	else:
		   ## The creation form is displayed if user has atleast one of the following privileges
		   ## cloudman resource manager privileges
		   ## is member of admin group of atleast one top level allocation and one project
		   userIsSuperUser = isSuperUser(groupsList)
		   if not userIsSuperUser:
			  userIsAdmin = isAdminOfAnyTopLevelAllocation(groupsList)
			  if not userIsAdmin:
				  message = "You neither have cloudman resource manager privileges nor membership of any Group for which Top Level Allocation exist. Hence you are not authorized to create Project Allocation";
				  html = "<html><body> %s.</body></html>" % message
				  return HttpResponse(html)
			  userIsAdmin = isAdminOfAnyProject(groupsList)
#			  if not userIsAdmin:
#				  message = "You neither have cloudman resource manager privileges nor membership of any Administrative E-Groups selected assigned for Projects . Hence you are not authorized to create Project Allocation";
#				  html = "<html><body> %s.</body></html>" % message
#				  return HttpResponse(html)
		   ## if the user has necessary permissions, then get all the data to prepare form and return it to the user
		   tpAllocNames = []
		   projectNames = []
		   groupNames = []
		   if userIsSuperUser:
			   tpAllocNames = TopLevelAllocation.objects.values_list('name', flat=True)
			   projectNames = Project.objects.values_list('name', flat=True)
		   else:
			   groupQset = Q(group__admin_group__exact=groupsList[0])
			   projectQset = Q(admin_group__exact=groupsList[0])
			   if len(groupsList) > 1:
				  for group in groupsList[1:]:
					  groupQset = groupQset | Q(group__admin_group__exact=group)
					  projectQset = projectQset | Q(admin_group__exact=group)
			   tpAllocNames = TopLevelAllocation.objects.filter(groupQset).values_list('name', flat=True)
			   #projectNames = Project.objects.filter(projectQset).values_list('name', flat=True)
			   projectNames = Project.objects.values_list('name', flat=True)
		   groupNames = Groups.objects.values_list('name', flat=True)
		   form = ProjectAllocationForm(userGroups=groupsList, superUserRights=userIsSuperUser)
                   resourceForm=ResourceForm();
		   return render_to_response('projectallocation/addnew.html',locals(),context_instance=RequestContext(request))

def listall(request):
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';')
	projectsAllocationList = ProjectAllocation.objects.select_related('top_level_allocation','project','group').all().order_by('name')
	deleteDict = {}
	showMultiDeleteOption = False
	numManaged=0
	for prjAlloc in projectsAllocationList:
		deleteItem = delUpdateAllowed(groupsList,prjAlloc.top_level_allocation.name,prjAlloc.project.name)
		if deleteItem:
			showMultiDeleteOption = True
			numManaged +=1
		deleteDict[prjAlloc.name] = deleteItem

	return render_to_response('projectallocation/listall.html',locals(),context_instance=RequestContext(request))


def getGroupAllocInProjectAllocation(request):
	mimetype = 'application/javascript'
	prjAllocName = request.REQUEST.get("name", "")
	try:
		grpAllocList = GroupAllocation.objects.filter(project_allocation__name=prjAllocName).order_by('name')
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

#this will give the allowed depth for the given Project Allocation
def getdepth(request):
	mimetype = 'application/javascript'
	projectAllocationName = request.REQUEST.get("name", "")
	level = GROUP_ALLOC_DEPTH
	try:
		prjAllocObj = ProjectAllocation.objects.get(name=projectAllocationName)
		if prjAllocObj:
			level = groupAllocLevel(prjAllocObj,None)
	except Exception:
		printStackTrace()
		level=0
	data = simplejson.dumps([{'depth':level}])
	return HttpResponse(data,mimetype)

## used to get the entire resource information (hepspec, memory, storage and bandwidth)
## of a given project allocation -> primarily used by group allocation
## to check whether a given group allocation can be met by the project allocation
def getresourceinfo(request):
		redirectURL = '/cloudman/message/?msg='

	## if the request is through ajax, then return the json object, otherwise return status 400 - BAD REQUEST
	#if request.is_ajax():
		format = 'json'
		mimetype = 'application/javascript'

		projectAllocationName = request.REQUEST.get("name", "")

		## initialize three dict, one each for total, free and used fraction resource parameter values
		totResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
		freeResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
		usedFraction = {'hepspec': 0, 'memory': 0, 'storage': 0, 'bandwidth': 0 }
		## call this function to calculate the above defined values
		errorMessage = getstats(projectAllocationName, totResources, freeResources, usedFraction)
		if errorMessage != '':
		   nulldata = []
		   data = simplejson.dumps(nulldata)
		   return HttpResponse(data,mimetype)
		## frame an object with all the resource parameter info for this project allocation
		## the information include, what is total available, how much is free and percentage of already allocated
		projectAllocationInfo = [{"pk": projectAllocationName, "model": "cloudman.projectallocationinfo", "fields": {"tothepspecs": totResources['hepspec'], "totmemory": totResources['memory'], "totstorage": totResources['storage'], "totbandwidth": totResources['bandwidth']}}, {"model": "cloudman.projectallocationfreeinfo", "fields": {"hepspecsfree" : freeResources['hepspec'], "memoryfree": freeResources['memory'], "storagefree": freeResources['storage'], "bandwidthfree": freeResources['bandwidth']}}, {"model": "cloudman.projectallocationusedinfoper", "fields":{"hepspecsfraction": usedFraction['hepspec'], "memoryfraction": usedFraction['memory'], "storagefraction": usedFraction['storage'], "bandwidthfraction": usedFraction['bandwidth']}}]

		## Get the allowed resource types information for this project allocation
		projectAllocationResourceTypeObjects = ProjectAllocationAllowedResourceType.objects.filter(project_allocation__name=projectAllocationName)
		projectAllocationResourceTypeList = list(projectAllocationResourceTypeObjects)
		resourceTypeIds = []
		resourceTypeObjects = None
		for oneRow in projectAllocationResourceTypeObjects:
			resourceTypeIds.append(oneRow.resource_type.id)
		if len(resourceTypeIds) > 0:
		   resourceTypeObjects = ResourceType.objects.filter(id__in=resourceTypeIds)

		## frame an object one each for each resource type in this project allocation
		for oneRT in resourceTypeObjects:
			projectAllocationInfo.append({"pk": oneRT.id, "model": "cloudman.resourcetype", "fields": {"name": oneRT.name, "resource_class": oneRT.resource_class, "hepspecs": oneRT.hepspecs, "memory": oneRT.memory, "storage": oneRT.storage, "bandwidth": oneRT.bandwidth}})

		## finally dump the data into json and return
		data = simplejson.dumps(projectAllocationInfo)
		return HttpResponse(data,mimetype)
	# If you want to prevent non AJAX calls
	#else:
	#	 return HttpResponse(status=400)

## used to get the entire resource information (hepspec, memory, storage and bandwidth)
## of a given project allocation
def getstats(prAllocName, totResources, freeResources, usedFraction):
	errorMessage = ''
	## Get the Project Allocation object
	projectAllocationObject = None
	try:
		projectAllocationObject = ProjectAllocation.objects.get(name=prAllocName)
	except ProjectAllocation.DoesNotExist:
		errorMessage = 'Project Allocation Name ' + prAllocName + ' does not exists'
		return errorMessage	  
	## Get the total resources of this project allocation 
	totHepSpecs = projectAllocationObject.hepspec
	totMemory = projectAllocationObject.memory
	totStorage = projectAllocationObject.storage
	totBandwidth = projectAllocationObject.bandwidth
	totResources['hepspec'] = totHepSpecs
	totResources['memory'] = totMemory
	totResources['storage'] = totStorage
	totResources['bandwidth'] = totBandwidth

	## Get all the Group allocations objects using this project allocation
	groupAllocationObjects = GroupAllocation.objects.filter(project_allocation__name = prAllocName)

	## Find how much of this project allocation is already allocated. Start with none is allocated
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
	prAllocName = request.REQUEST.get("name", "")
	redirectURL = '/cloudman/message/?msg='
	comment = request.REQUEST.get("comment", "deleting")
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';')
	## Get the Project allocation object
	prAllocObject = None
	try:
		prAllocObject = ProjectAllocation.objects.get(name=prAllocName)
	except ProjectAllocation.DoesNotExist:
		failureMessage = "Project Allocation with Name " + prAllocName + " could not be found"
		return HttpResponseRedirect(redirectURL+failureMessage)

	## update of allocation is allowed only if user has
	## either cloudman resource manager privileges
	## or membership of admin group of both selected top level allocation and project
	if not delUpdateAllowed(groupsList,prAllocObject.top_level_allocation.name,prAllocObject.project.name):
			message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Group of the Group for which the Top Level Allocation " + prAllocObject.top_level_allocation.name + " is created . Hence you are not authorized to delete Project Allocation";
			html = "<html><body> %s.</body></html>" % message
			return HttpResponse(html)
#	userIsSuperUser = isSuperUser(groupsList)
#	if not userIsSuperUser:
#		userIsAdmin = isAdminOfTopLevelAllocation(groupsList, prAllocObject.top_level_allocation.name)
#		if not userIsAdmin:
#			message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Group of the Group for which the Top Level Allocation " + prAllocObject.top_level_allocation.name + " is created . Hence you are not authorized to delete Project Allocation";
#			html = "<html><body> %s.</body></html>" % message
#			return HttpResponse(html)
#		userIsAdmin = isAdminOfProject(groupsList, prAllocObject.project.name)
#		if not userIsAdmin:
#			message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Groups assigned to the Project " + prAllocObject.project.name + ". Hence you are not authorized to delete Project Allocation";
#			html = "<html><body> %s.</body></html>" % message
#			return HttpResponse(html)
	## Check if any group allocations defined using this project allocation
	grAllocNames = GroupAllocation.objects.filter(project_allocation__name__iexact = prAllocName).values_list('name', flat=True).order_by('name')

	## If yes, then alert the user and stop the delete operation
	finalMessage = ''
	grAllocNamesList = list(grAllocNames)
	if len(grAllocNamesList) > 0:
		finalMessage = finalMessage + "Group Allocation Names: " + (', '.join(grAllocNamesList)) + "<br/>"
	if not finalMessage == '':
		finalMessage = "Project Allocation with Name " + prAllocName + " Could not be deleted because it is being used in " + "<br/>" + finalMessage
		html = "<html><body> %s</body></html>" % finalMessage
		return HttpResponse(html)

	oldprAllocObject = prAllocObject	
	status = addLog(request,prAllocName,comment,oldprAllocObject,None,'projectallocation','delete',False)		   
	## If no group allocations exists, then first delete the allowed resource types of this project allocation
	## then delete the project allocation and return a success message to the user
	ProjectAllocationAllowedResourceType.objects.filter(project_allocation__name__iexact = prAllocName).delete()
	prAllocObject.delete()
	if status:
		transaction.commit()
	else:
		transaction.rollback()
	message = "Project Allocation with Name " + prAllocName + " deleted successfully "
	html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/projectallocation/list/\"></HEAD><body> %s.</body></html>" % message
	return HttpResponse(html)


@transaction.commit_on_success
def deleteMultiple(request):
	prAllocNameList = request.REQUEST.get("name_list", "")
	comment = request.REQUEST.get("comment", "deleting")
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';') ;

	printArray = []
	title = "Delete multiple Project Allocation message" 
	prAllocNameArray = prAllocNameList.split("%%")
	userIsSuperUser = isSuperUser(groupsList)
	for prAllocName in prAllocNameArray:
		## Get the Project allocation object
		prAllocObject = None
		try:
			prAllocObject = ProjectAllocation.objects.get(name=prAllocName)
		except ProjectAllocation.DoesNotExist:
			printArray.append("Project Allocation with Name " + prAllocName + " could not be found")
			continue
		## delete of allocation is allowed only if user has
		## either cloudman resource manager privileges
		## or membership of admin group of both selected top level allocation and project
		if not delUpdateAllowed(groupsList,prAllocObject.top_level_allocation.name,prAllocObject.project.name):
				message = "Neither cloudman resource manager privileges nor membership of the Admin E-Group of the Group for which the Top Level Allocation " + prAllocObject.top_level_allocation.name + " is created . Hence you can not delete Project Allocation " +prAllocName;
				printArray.append(message)
				continue

#		if not userIsSuperUser:
#			userIsAdmin = isAdminOfTopLevelAllocation(groupsList, prAllocObject.top_level_allocation.name)
#			if not userIsAdmin:
#				message = "neither cloudman resource manager privileges nor membership of the Admin E-Group of the Group for which the Top Level Allocation " + prAllocObject.top_level_allocation.name + " is created . Hence you can not delete Project Allocation " +prAllocName;
#				printArray.append(message)
#				continue
#			userIsAdmin = isAdminOfProject(groupsList, prAllocObject.project.name)
#			if not userIsAdmin:
#				message = "Neither cloudman resource manager privileges nor membership of the Administrative E-Groups assigned to the Project " + prAllocObject.project.name + ". hence You can not delete Project Allocation" + prAllocName;
#				printArray.append(message)
#				continue
		## Check if any group allocations defined using this project allocation
		grAllocNames = GroupAllocation.objects.filter(project_allocation__name__iexact = prAllocName).values_list('name', flat=True).order_by('name')
		## If yes, then alert the user and stop the delete operation
		finalMessage = ''
		grAllocNamesList = list(grAllocNames)
		if len(grAllocNamesList) > 0:
			finalMessage = finalMessage + "Group Allocation Names: " + (', '.join(grAllocNamesList)) + "  "
		if not finalMessage == '':
			finalMessage = "Project Allocation with Name " + prAllocName + " Could not be deleted because it is being used in " + "  " + finalMessage
			printArray.append(finalMessage)
		else:
			#add the Log
			addLog(request,prAllocName,comment,prAllocObject,None,'projectallocation','delete',False)
			## If no group allocations exists, then first delete the allowed resource types of this project allocation
			ProjectAllocationAllowedResourceType.objects.filter(project_allocation__name__iexact = prAllocName).delete()
			prAllocObject.delete()
			printArray.append( "Project Allocation with Name " + prAllocName + " deleted successfully")
	return render_to_response('base/deleteMultipleMsg.html',locals(),context_instance=RequestContext(request))		

def getAttrInfo(request):
	redirectURL = '/cloudman/message/?msg='
	## if the request is through ajax, then return the json object, otherwise return status 400 - BAD REQUEST
	if request.is_ajax():
		format = 'json'
		mimetype = 'application/javascript'
		projectName = request.REQUEST.get("projectName", "")
		allocname = request.REQUEST.get("allocName", "")
		attribute_list = []
		try:
			prallocMetadataList = ProjectAllocationMetadata.objects.filter(project__name__iexact = projectName,project_allocation__name__iexact= allocname ).values_list('attribute','value')
			old_metadata_dict ={}
			for attr,value in prallocMetadataList:
				old_metadata_dict[attr] = value
			if len(old_metadata_dict) ==0:
				errMsg='No Attribute set for Project Allocation Set the attribute'
			else:
				errMsg=''
			prjMetadataList = ProjectMetadata.objects.filter(project__name__iexact = projectName)
			for metadata in prjMetadataList:			   
				attr_name =  metadata.attribute				  
				attr_value = metadata.value				  
				selected = ''
				if attr_name in old_metadata_dict:
					selected = old_metadata_dict[attr_name]
				attribute_list.append({'attribute':attr_name,'value':attr_value,'selected':selected})				
		except Exception:
			print  traceback.format_exc()
		#data = simplejson.dumps({'ERRORMSG':errMsg,'ATTRLIST':attribute_list})
		data = simplejson.dumps(attribute_list)
		return HttpResponse(data,mimetype)

def getdetails(request):
	redirectURL = '/cloudman/message/?msg='   
	allocName = request.REQUEST.get("name", "")
	## Get the Project allocation Object
	allocInfo = None
	try:
		allocInfo = ProjectAllocation.objects.select_related('group','project','top_level_allocation').get(name=allocName)
	except ProjectAllocation.DoesNotExist:
		errorMessage = 'Project Allocation with Name ' + allocName + ' does not exists'
		return HttpResponseRedirect(redirectURL + errorMessage)

	## Get the Allowed Resource Types of this project allocation
	allowedResourceTypesList = ProjectAllocationAllowedResourceType.objects.select_related('resource_type').filter(project_allocation = allocInfo).order_by('resource_type__name')
	#get the projectAllocation metadat
	prAllocMetadata = ProjectAllocationMetadata.objects.filter(project__name__iexact = allocInfo.project.name,project_allocation = allocInfo).values('attribute','value').order_by('attribute')
	## Get the Group Allocations made using this project allocation
	groupAllocationsInfo = GroupAllocation.objects.select_related('group').filter(project_allocation__name=allocName).order_by('name')
	object_id = allocInfo.id
	changeLogList = getLog('projectallocation',allocName,object_id,None)

	return render_to_response('projectallocation/getdetails.html',locals(),context_instance=RequestContext(request))

def gethepspecstats(request):
	## if the request is through ajax, then return the json object, otherwise return status 400 - BAD REQUEST
	#if request.is_ajax():
	   allocName = request.REQUEST.get("name", "")
	   format = 'json'
	   mimetype = 'application/javascript'

	   ## Get the Project Allocation Object 
	   projectAllocationInfo = ProjectAllocation.objects.get(name=allocName)

	   ## Step 1: Given the information about the top level allocation used for this project allocation
	   ## Get the Top Level allocation total hepspec 
	   tpAllocTotHepSpecs = 0
	   if (projectAllocationInfo.top_level_allocation.hepspec != None) :
		 tpAllocTotHepSpecs = round(projectAllocationInfo.top_level_allocation.hepspec, 3)

	   ## Calculate the fraction of top level allocation hepspec allocated to this project
	   prAllocHepSpecFraction = 0
	   prAllocTotHepSpecs = 0
	   if (projectAllocationInfo.hepspec_fraction() != ''):
		 prAllocHepSpecFraction = projectAllocationInfo.hepspec_fraction()
		 prAllocTotHepSpecs = projectAllocationInfo.hepspec
	   
	   ## Calculate how much percentage of top level allocation hepspec is allocated to other projects
	   ## Use ~Q to remove this project from consideration
	   tpAllocName = projectAllocationInfo.top_level_allocation.name
	   projectAllocationObjects = ProjectAllocation.objects.filter(~Q(name=allocName), top_level_allocation__name=tpAllocName).values('hepspec')
	   othersTotAlloc = 0.0
	   for oneObject in projectAllocationObjects:
		 if (oneObject['hepspec'] != None):
			othersTotAlloc = othersTotAlloc + oneObject['hepspec']
	   othersTotAllocPer = 0
	   if othersTotAlloc > 0:
		  othersTotAllocPer = round(((othersTotAlloc/tpAllocTotHepSpecs) * 100), 3)

	   ## Frame an object giving the above calculated results i.e 
	   ## top level allocation name, project allocation name, total hepspec in top level allocation 
	   ## fraction allocated to this project and fraction allocated to other projects
	   allocStatsInfo = [{"pk": tpAllocName, "model": "cloudman.toplevelallocation", "projectallocation": allocName, "fields": {"totalhepspec": tpAllocTotHepSpecs, "projectallocfrac": prAllocHepSpecFraction, "othersallocfrac": othersTotAllocPer}}] 

	   ## Step 2: Given the information about the group allocations allocated using this this project allocation
	   ## Get all the Group allocations hepspec value
	   groupAllocationObjects = GroupAllocation.objects.filter(project_allocation__name=allocName).values('hepspec')
	   totAlloc = 0.0
	   for oneObject in groupAllocationObjects:
		 if (oneObject['hepspec'] != None):
		   totAlloc = totAlloc + oneObject['hepspec']

	   totAllocPer = 0
	   if totAlloc > 0:
		  totAllocPer = round(((totAlloc/prAllocTotHepSpecs) * 100), 3)

	   ## Frame an object giving the total hepspec in this project allocation and the percentage of it already
	   ## allocated to the group allocations
	   allocStatsInfo.append({"pk": allocName, "model": "cloudman.projectallocation", "fields": {"totalhepspec": prAllocTotHepSpecs, "allotedfrac": totAllocPer}})

	   ## Step 3: Finally, dump the data into json object and return
	   data = simplejson.dumps(allocStatsInfo)
	   return HttpResponse(data,mimetype)
	#else:
	#  return HttpResponse(status=400)

@transaction.commit_on_success
def update(request):
	prAllocName = request.REQUEST.get("name", "")
	redirectURL = '/cloudman/message/?msg='
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';') ;
	userIsSuperUser = isSuperUser(groupsList)
	## Get the project allocation object
	prAllocObject = None
	try:
		prAllocObject = ProjectAllocation.objects.get(name=prAllocName)
	except ProjectAllocation.DoesNotExist:
		failureMessage = "Project Allocation with Name " + prAllocName + " could not be found"
		return HttpResponseRedirect(redirectURL+failureMessage)
	oldprAllocInfo = getProjectAllocationInfo(prAllocObject)
	## update of allocation is allowed only if user has
	## either cloudman resource manager privileges
	## or membership of admin group of both selected top level allocation and project
	if not delUpdateAllowed(groupsList,prAllocObject.top_level_allocation.name,prAllocObject.project.name):
		message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Group of the Group for which the Top Level Allocation " + prAllocObject.top_level_allocation.name + " is created . Hence you are not authorized to edit Project Allocation";
		html = "<html><body> %s.</body></html>" % message
		return HttpResponse(html)
#	if not userIsSuperUser:
#		userIsAdmin = isAdminOfTopLevelAllocation(groupsList, prAllocObject.top_level_allocation.name)
#		if not userIsAdmin:
#		   message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Group of the Group for which the Top Level Allocation " + prAllocObject.top_level_allocation.name + " is created . Hence you are not authorized to edit Project Allocation";
#		   html = "<html><body> %s.</body></html>" % message
#		   return HttpResponse(html)
#		userIsAdmin = isAdminOfProject(groupsList, prAllocObject.project.name)
#		if not userIsAdmin:
#		   message = "You neither have cloudman resource manager privileges nor membership of the Administrative E-Groups assigned to the Project " + prAllocObject.project.name + ". Hence you are not authorized to edit Project Allocation";
#		   html = "<html><body> %s.</body></html>" % message
#		   return HttpResponse(html)

	## Get the allowed Resource types of this allocation
	prAllocRTList = ProjectAllocationAllowedResourceType.objects.filter(project_allocation__name=prAllocName).values_list('resource_type__name', flat=True)
	## If the request is thorugh form submission, then try to update the field values
	## or else present an update form
	if request.method == 'POST':
		## Existing values
		currName = prAllocObject.name
		currHepSpec = prAllocObject.hepspec
		currMemory = prAllocObject.memory
		currStorage = prAllocObject.storage
		currBandwidth = prAllocObject.bandwidth
		## New values
		newName = request.REQUEST.get("name", "")
		newHepSpec = request.REQUEST.get("hepspecs", "")
		newMemory = request.REQUEST.get("memory", "")
		newStorage = request.REQUEST.get("storage", "")
		newBandwidth = request.REQUEST.get("bandwidth", "")
		newRTList = request.REQUEST.getlist("prallocallowedrt")
		comment = request.REQUEST.get("comment", "")
		attr_name_array = request.REQUEST.getlist('attribute_name');
		attr_value_array = request.REQUEST.getlist('attribute_value');
		scale = request.REQUEST.get("scale")
		storagescale = request.REQUEST.get("storagescale")
		try:
			validate_name(newName)
			validate_float(newHepSpec)
			validate_float(newMemory)
			validate_float(newStorage)
			validate_float(newBandwidth)
			validate_comment(comment)
		except ValidationError as e:
			msg = 'Edit ProjectAllocation Form  '+', '.join(e.messages)
			html = "<html><head><meta HTTP-EQUIV=\"REFRESH\" content=\"5; url=/cloudman/projectallocation/list/\"></head><body> %s.</body></html>" % msg
			return HttpResponse(html)
			#Create dictionary of attr_name and attr_value with attr_name:attr_value as key:value pairs
		attr_list = createDictFromList(attr_name_array,attr_value_array)
		## validate the new resource parameter values
		errorMsg = checkAttributeValues(newHepSpec, newMemory, newStorage, newBandwidth)
		if (errorMsg != ''):
			return HttpResponseRedirect(redirectURL + errorMsg)
		## check whether any existing resource type is de-selected or any new one selected
		rtNotChanged = True;
		for newRt in newRTList:
			if not newRt in prAllocRTList:
				rtNotChanged = False

		for oldRt in prAllocRTList:
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
		## if name is changed, validate it and then assign the new name
		if (currName != newName):
			if (newName == ''):
				errorMsg = 'Name name field cannot be left blank. So Edit Project Allocation operation stopped'
				return HttpResponseRedirect(redirectURL + errorMsg)
			nameExists = checkNameIgnoreCase(newName)
			if nameExists:
				msgAlreadyExists = 'Project Allocation ' + newName + ' already exists. Hence Edit Project Allocation Operation Stopped'
				return HttpResponseRedirect(redirectURL + msgAlreadyExists);
			prAllocObject.name = newName
		## if any of the resource parameter values changed
		if ( (currHepSpec != newHepSpec) or (currMemory != newMemory) or (currStorage != newStorage) or (currBandwidth != newBandwidth) ):
		   ## initialize three dict, one each for total, free and used fraction resource parameter values
		   ## get these values from the selected top level allocation
		   totResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
		   freeResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
		   usedFraction = {'hepspec': 0, 'memory': 0, 'storage': 0, 'bandwidth': 0 }

		   ## call this function to calculate the above defined values
		   errorMessage = tpallocgetstats(prAllocObject.top_level_allocation.name, totResources, freeResources, usedFraction)
		   if errorMessage != '':
			   return HttpResponseRedirect(redirectURL + errorMessage)

		   tpLevelHepSpec = totResources['hepspec']
		   tpLevelMemory = totResources['memory']
		   tpLevelStorage = totResources['storage']
		   tpLevelBandwidth = totResources['bandwidth']

		   ## calculate how much of project allocated resoures are used for group allocations
		   prUsedResources = {'hepspec': None, 'memory': None, 'storage': None, 'bandwidth': None}
		   calPrUsedResources(prUsedResources, currName)

		   ## check whether any changes to the exist resource values can be met using the top level allocation
		   ## Also, check these changes had any effect on the group allocations
		   errorMessage = ''
		   if (currHepSpec != newHepSpec):
			  if newHepSpec == None:
				 if (prUsedResources['hepspec'] > 0):
					errorMessage = errorMessage + 'Setting the Hepspec UNDEFINED is not possible as there exists alloted Hepspec for Group allocations using this Project allocation. '
			  else:
				 if currHepSpec == None:
					if tpLevelHepSpec == None:
					   errorMessage = errorMessage + 'The requested Hepspec ' + str(newHepSpec) + ' cannot be fulfilled as Hepspec is UNDEFINED for this project Top Level Allocation. '
					else:
					   if ( freeResources['hepspec'] < newHepSpec ):
						   errorMessage = errorMessage + 'The requested Hepspec ' + str(newHepSpec) + ' is more than the free Hepspec available from this project Top Level Allocation. '
				 else:
					if ( (freeResources['hepspec'] + currHepSpec) < newHepSpec ):
					   errorMessage = errorMessage + 'The requested Hepspec ' + str(newHepSpec) + ' is more than the free Hepspec available from this project Top Level Allocation. '
##commented to implement scaling factor
				 if ( (scale is None) and (newHepSpec < prUsedResources['hepspec']) ):
					errorMessage = errorMessage + 'The requested Hepspec ' + str(newHepSpec) + ' is less than the already alloted Hepspec for Group Allocations using this Project allocation. '

		   if (currMemory != newMemory):
			  if newMemory == None:
				 if (prUsedResources['memory'] > 0):
					errorMessage = errorMessage + 'Setting the Memory UNDEFINED is not possible as there exists alloted Memory for Group allocations using this Project allocation. '
			  else:
				 if currMemory == None:
					if tpLevelMemory == None:
					   errorMessage = errorMessage + 'The requested Memory ' + str(newMemory) + ' cannot be fulfilled as Memory is UNDEFINED for this project Top Level Allocation. '
					else:
					   if ( freeResources['memory'] < newMemory ):
						   errorMessage = errorMessage + 'The requested Memory ' + str(newMemory) + ' is more than the free Memory available from this project Top Level Allocation. '
				 else:
					if ( (freeResources['memory'] + currMemory) < newMemory ):
					   errorMessage = errorMessage + 'The requested Memory ' + str(newMemory) + ' is more than the free Memory available from this project Top Level Allocation. '
				 if (newMemory < prUsedResources['memory']):
					errorMessage = errorMessage + 'The requested Memory ' + str(newMemory) + ' is less than the already alloted Memory for Group Allocations using this Project allocation. '

		   if (currStorage != newStorage):
			  if newStorage == None:
				 if (prUsedResources['storage'] > 0):
					errorMessage = errorMessage + 'Setting the Storage UNDEFINED is not possible as there exists alloted Storage for Group allocations using this Project allocation. '
			  else:
				 if currStorage == None:
					if tpLevelStorage == None:
					   errorMessage = errorMessage + 'The requested Storage ' + str(newStorage) + ' cannot be fulfilled as Storage is UNDEFINED for this project Top Level Allocation. '
					else:
					   if ( freeResources['storage'] < newStorage ):
						  errorMessage = errorMessage + 'The requested Storage ' + str(newStorage) + ' is more than the free Storage available from this project Top Level Allocation. '
				 else:
					if ( (freeResources['storage'] + currStorage) < newStorage ):
					   errorMessage = errorMessage + 'The requested Storage ' + str(newStorage) + ' is more than the free Storage available from this project Top Level Allocation. '
				 if ((storagescale is None)) and (newStorage < prUsedResources['storage']):
					errorMessage = errorMessage + 'The requested Storage ' + str(newStorage) + ' is less than the already alloted Storage for Group allocations using this Project allocation '

		   if (currBandwidth != newBandwidth):
			  if newBandwidth == None:
				 if (prUsedResources['bandwidth'] > 0):
					errorMessage = errorMessage + 'Setting the Bandwidth UNDEFINED is not possible as there exists alloted Bandwidth for Group allocations using this Project allocation. '
			  else:
				 if currBandwidth == None:
					if tpLevelBandwidth == None:
					   errorMessage = errorMessage + 'The requested Bandwidth ' + str(newBandwidth) + ' cannot be fulfilled as Bandwidth is UNDEFINED for this project Top Level Allocation. '
					else:
					   if ( freeResources['bandwidth'] < newBandwidth ):
						  errorMessage = errorMessage + 'The requested Bandwidth ' + str(newBandwidth) + ' is more than the free Bandwidth available from this project Top Level Allocation. '
				 else:
					if ( (freeResources['bandwidth'] + currBandwidth) < newBandwidth ):
					   errorMessage = errorMessage + 'The requested Bandwidth ' + str(newBandwidth) + ' is more than the free Bandwidth available from this project Top Level Allocation. '
				 if (newBandwidth < prUsedResources['bandwidth']):
					errorMessage = errorMessage + 'The requested Bandwidth ' + str(newBandwidth) + ' is less than the already alloted Bandwidth for Group allocations using this Project allocation. '

		   if errorMessage != '':
			  errorMessage = errorMessage + ' Hence Edit Project Allocation Operation Stopped'
			  transaction.rollback()
			  return HttpResponseRedirect(redirectURL + errorMessage)
		   ## assign the new values to the project allocation
		   ## if any of the resource values becomes NULL, then to keep the consistency, make all group allocations
		   ## resource value UNDEFINED i.e NULL for that parameter
		   if (currHepSpec != newHepSpec):
			   if (newHepSpec == None):
				  GroupAllocation.objects.filter(project_allocation__name = currName).update(hepspec=None)
			   prAllocObject.hepspec = newHepSpec

		   if (currMemory != newMemory):
			   if (newMemory == None):
				  GroupAllocation.objects.filter(project_allocation__name = currName).update(memory=None)
			   prAllocObject.memory = newMemory

		   if (currStorage != newStorage):
			   if (newStorage == None):
				  GroupAllocation.objects.filter(project_allocation__name = currName).update(storage=None)
			   prAllocObject.storage = newStorage

		   if (currBandwidth != newBandwidth):
			   if (newBandwidth == None):
				  GroupAllocation.objects.filter(project_allocation__name = currName).update(bandwidth=None)
			   prAllocObject.bandwidth = newBandwidth
		## save all the changes
		if scale is not None:
			scalefactor = getScaleFactor(newHepSpec,currHepSpec)
			scaleGroupAllocationHepSpec(currName,scalefactor,scale=True)	
		if storagescale is not None:
			scalefactor = getScaleFactor(newStorage,currStorage)
			scaleGroupAllocationStorage(currName,scalefactor,scale=True)	
		
		prAllocObject.save()
		try:
			ProjectAllocationMetadata.objects.filter(project = prAllocObject.project,project_allocation = prAllocObject).delete()		  
			for attr_name,attr_value  in attr_list.items():
				pralloc_metadata = ProjectAllocationMetadata(attribute = attr_name,value = attr_value,project = prAllocObject.project,project_allocation = prAllocObject)
				pralloc_metadata.save()
		except Exception:
			printStackTrace()
		## if the allowed resource type list is changed, then add newly selected or delete the un-selected ones
		errorMessage = ''
		if not rtNotChanged:
		   for newRt in newRTList:
			 if not newRt in prAllocRTList:
				try:
				   rtObject = ResourceType.objects.get(name=newRt)
				   prrt = ProjectAllocationAllowedResourceType(project_allocation=prAllocObject, resource_type=rtObject)
				   prrt.save()
				except ResourceType.DoesNotExist:
				   transaction.rollback()
				   errorMessage = errorMessage + 'No Record Found for Resource Type ' + newRt + '. Hence Project Allocation Allowed Resource Types Edit Failed. '

		   for oldRt in prAllocRTList:
			 if not oldRt in newRTList:
				try:
				   prrt = ProjectAllocationAllowedResourceType.objects.get(resource_type__name=oldRt, project_allocation__name=prAllocName)
				   prrt.delete()
				except ProjectAllocationAllowedResourceType.DoesNotExist:
				   transaction.rollback()
				   errorMessage = errorMessage + 'No Record Found for Project Allocation Allowed Resource Type ' + oldRt + '. Hence Project Allocation Allowed Resource Types Edit Failed. '
		#Add the Log
		newprAllocInfo = getProjectAllocationInfo(prAllocObject)
		objectId = prAllocObject.id
		if addUpdateLog(request,newName,objectId,comment,oldprAllocInfo,newprAllocInfo,'projectallocation',True):
			transaction.commit()
		else:
			transaction.rollback()
		## finally, return a successful message to the user
		message = 'Project Allocation ' + prAllocName + ' Successfully Updated'
		html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/projectallocation/list/\"></HEAD><body> %s<br/> %s </body></html>" % (message, errorMessage)
		return HttpResponse(html)
   
	totalHepSpec = prAllocObject.top_level_allocation.hepspec
	totalMemory = prAllocObject.top_level_allocation.memory
	totalStorage = prAllocObject.top_level_allocation.storage
	totalBandwidth = prAllocObject.top_level_allocation.bandwidth
 
	hepSpecPer = None
	memoryPer = None
	storagePer = None
	bandwidthPer = None
	if (prAllocObject.hepspec != None ):
	   if (prAllocObject.hepspec > 0) :
		  hepSpecPer = round(((prAllocObject.hepspec/prAllocObject.top_level_allocation.hepspec) * 100), 3)
	   else:
		  hepSpecPer = 0
	if (prAllocObject.memory != None ):
	   if (prAllocObject.memory > 0):
		  memoryPer = round(((prAllocObject.memory/prAllocObject.top_level_allocation.memory) * 100), 3)
	   else:
		  memoryPer = 0
	if (prAllocObject.storage != None ):
	   if (prAllocObject.storage > 0):
		  storagePer = round(((prAllocObject.storage/prAllocObject.top_level_allocation.storage) * 100), 3)
	   else:
		  storagePer = 0
	if (prAllocObject.bandwidth != None ):
	   if (prAllocObject.bandwidth > 0):
		  bandwidthPer = round(((prAllocObject.bandwidth/prAllocObject.top_level_allocation.bandwidth) * 100), 3)
	   else:
		  bandwidthPer = 0
	
	## if the request is not a post request, then present the update form
	form =ResourceForm
        return render_to_response('projectallocation/update.html',locals(),context_instance=RequestContext(request))



def calPrUsedResources(prUsedResources, prAllocName):
	## calculate how much of project allocated resources are already allocated to groups
	usedHepSpec = 0
	usedMemory = 0
	usedStorage = 0
	usedBandwidth = 0

	allGrAllocObjects = GroupAllocation.objects.filter(project_allocation__name = prAllocName)
	for oneObject in allGrAllocObjects:
		if (oneObject.hepspec != None):
			usedHepSpec = usedHepSpec + oneObject.hepspec
		if (oneObject.memory != None):
			usedMemory = usedMemory + oneObject.memory
		if (oneObject.storage != None):
			usedStorage = usedStorage + oneObject.storage
		if (oneObject.bandwidth != None):
			usedBandwidth = usedBandwidth + oneObject.bandwidth
	prUsedResources['hepspec'] = round(usedHepSpec, 3)
	prUsedResources['memory'] = round(usedMemory, 3)
	prUsedResources['storage'] = round(usedStorage, 3)
	prUsedResources['bandwidth'] = round(usedBandwidth, 3)

### The following functions are not used as of now
def getallowedresourcetypes(request):
	## if the request is through ajax, then return the json object, otherwise return status 400 - BAD REQUEST
	#if request.is_ajax():
	   allocName = request.REQUEST.get("projectallocationname", "")
	   format = 'json'
	   mimetype = 'application/javascript'

	   rtInfo = []
	   projectAllocationResourceTypeObjects = ProjectAllocationAllowedResourceType.objects.filter(project_allocation__name=allocName)
	   projectAllocationResourceTypeList = list(projectAllocationResourceTypeObjects)
	   resourceTypeIds = []
	   resourceTypeObjects = None
	   for oneRow in projectAllocationResourceTypeObjects:
		   resourceTypeIds.append(oneRow.resource_type.id)
	   if len(resourceTypeIds) > 0:
		  resourceTypeObjects = ResourceType.objects.filter(id__in=resourceTypeIds)

	   for oneRT in resourceTypeObjects:
		   rtInfo.append({"pk": oneRT.id, "model": "cloudman.projectallocationallowedresourcetype", "fields": {"name": oneRT.name, "resource_class": oneRT.resource_class, "hepspecs": oneRT.hepspecs, "memory": oneRT.memory, "storage": oneRT.storage, "bandwidth": oneRT.bandwidth}})

	   data = simplejson.dumps(rtInfo)
	   return HttpResponse(data,mimetype)
	#else:
	#	return HttpResponse(status=400)

def gettphepspecspiechart(request):
	prAllocName = request.REQUEST.get("name", "")
	projectAllocationInfo = ProjectAllocation.objects.get(name=prAllocName)
	tpAllocTotHepSpecs = 0
	if (projectAllocationInfo.top_level_allocation.hepspec != None) :
	   tpAllocTotHepSpecs = round(projectAllocationInfo.top_level_allocation.hepspec, 3)
	prAllocHepSpecFraction = 0
	if (projectAllocationInfo.hepspec_fraction != None):
	   prAllocHepSpecFraction = projectAllocationInfo.hepspec_fraction
	
	freePer = 100
	freePer = freePer - prAllocHepSpecFraction
	tpAllocName = projectAllocationInfo.top_level_allocation.name

	projectAllocationObjects = ProjectAllocation.objects.filter(~Q(name=prAllocName), top_level_allocation__name=tpAllocName).values('hepspec_fraction')
	othersTotAllocPer = 0.0
	for oneObject in projectAllocationObjects:
		if (oneObject['hepspec_fraction'] != None):
		   othersTotAllocPer = othersTotAllocPer + oneObject['hepspec_fraction']
	fig = Figure(figsize=(4,4))
	canvas = FigureCanvas(fig)
	ax = fig.add_subplot(111)
	labels = []
	fracs = []
	labels.append('Project:\n' + prAllocName)
	fracs.append(prAllocHepSpecFraction)
	if (othersTotAllocPer > 0):
	   labels.append('Other Projects')
	   fracs.append(othersTotAllocPer)
	   freePer = freePer - othersTotAllocPer
	if freePer > 0:
	   labels.append('Free')
	   fracs.append(freePer)
	patches, texts, autotexts = ax.pie(fracs, explode=None, labels=labels, colors=('r', 'g', 'c', 'm', 'y', 'k', 'w', 'b'), autopct='%.2f%%', pctdistance=0.4, labeldistance=1.1, shadow=False)
	ax.set_title('\n Top Level Allocation ' + tpAllocName + ' Hepspec \n Total: ' + str(tpAllocTotHepSpecs), fontdict=None, verticalalignment='bottom')
	ax.grid(True)
	response=django.http.HttpResponse(content_type='image/png')
	canvas.print_png(response)
	canvas.draw()
	return response

def getprhepspecspiechart(request):
	prAllocName = request.REQUEST.get("name", "")
	projectAllocationInfo = ProjectAllocation.objects.get(name=prAllocName)
	tpAllocTotHepSpecs = 0
	if (projectAllocationInfo.top_level_allocation.hepspec != None):
	   tpAllocTotHepSpecs = projectAllocationInfo.top_level_allocation.hepspec
	prAllocHepSpecFraction = 0
	if (projectAllocationInfo.hepspec_fraction != None):
	   prAllocHepSpecFraction = projectAllocationInfo.hepspec_fraction
	prAllocTotHepSpecs = round(((prAllocHepSpecFraction * tpAllocTotHepSpecs)/100), 3)
	tpAllocName = projectAllocationInfo.top_level_allocation.name

	groupAllocationObjects = GroupAllocation.objects.filter(project_allocation__name=prAllocName).values('hepspec_fraction')
	totAllocPer = 0.0
	for oneObject in groupAllocationObjects:
	   if (oneObject['hepspec_fraction'] != None):
		  totAllocPer = totAllocPer + oneObject['hepspec_fraction']

	fig = Figure(figsize=(4,4))
	canvas = FigureCanvas(fig)
	ax = fig.add_subplot(111)
	labels = []
	fracs = []
	freePer = 100  
	freePer = freePer - totAllocPer
	if totAllocPer > 0:
	   labels.append('Allocated')
	   fracs.append(totAllocPer)
	if freePer > 0:
	   labels.append('Free')
	   fracs.append(freePer)
	patches, texts, autotexts = ax.pie(fracs, explode=None, labels=labels, colors=('r', 'g', 'c', 'm', 'y', 'k', 'w', 'b'), autopct='%.2f%%', pctdistance=0.4, labeldistance=1.1, shadow=False)
	ax.set_title('\n Project Allocation ' + prAllocName + ' Hepspec \n Total: ' + str(prAllocTotHepSpecs), fontdict=None, verticalalignment='bottom')
	ax.grid(True)
	response=django.http.HttpResponse(content_type='image/png')
	canvas.print_png(response)
	canvas.draw()
	return response

def calPrAllocResources(prAllocObject):
	if (prAllocObject.hepspec_fraction != None):
		prAllocObject.hepspec = ( prAllocObject.hepspec_fraction * prAllocObject.top_level_allocation.hepspec )/100
	if (prAllocObject.memory_fraction != None):
		prAllocObject.memory = ( prAllocObject.memory_fraction * prAllocObject.top_level_allocation.memory )/100
	if (prAllocObject.storage_fraction != None):
		prAllocObject.storage = ( prAllocObject.storage_fraction * prAllocObject.top_level_allocation.storage )/100
	if (prAllocObject.bandwidth_fraction != None):
		prAllocObject.bandwidth = ( prAllocObject.bandwidth_fraction * prAllocObject.top_level_allocation.bandwidth )/100

	if (prAllocObject.hepspec != None):
		temp = round(prAllocObject.hepspec, 3)
		prAllocObject.hepspec = temp
	if (prAllocObject.memory != None):
		temp1 = round(prAllocObject.memory, 3)
		prAllocObject.memory = temp1
	if (prAllocObject.storage != None):
		temp2 = round(prAllocObject.storage, 3)
		prAllocObject.storage = temp2
	if (prAllocObject.bandwidth != None):
		temp3 = round(prAllocObject.bandwidth, 3)
		prAllocObject.bandwidth = temp3

def calTpLevelUsedResources(tpLevelUsedResources, prAllocObject):
	totalHepSpec = prAllocObject.top_level_allocation.hepspec
	totalMemory = prAllocObject.top_level_allocation.memory
	totalStorage = prAllocObject.top_level_allocation.storage
	totalBandwidth = prAllocObject.top_level_allocation.bandwidth

	usedHepSpec = 0
	usedMemory = 0
	usedStorage = 0
	usedBandwidth = 0

	allPrAllocObjects = ProjectAllocation.objects.filter(top_level_allocation__name = prAllocObject.top_level_allocation.name)
	for oneObject in allPrAllocObjects:
		if (oneObject.hepspec_fraction != None):
		   usedHepSpec = usedHepSpec + ( oneObject.hepspec_fraction * totalHepSpec )/100
		if (oneObject.memory_fraction != None):
		   usedMemory = usedMemory + ( oneObject.memory_fraction * totalMemory )/100
		if (oneObject.storage_fraction != None):
		   usedStorage = usedStorage + ( oneObject.storage_fraction * totalStorage )/100
		if (oneObject.bandwidth_fraction != None):
		   usedBandwidth = usedBandwidth + ( oneObject.bandwidth_fraction * totalBandwidth )/100

	tpLevelUsedResources['hepspec'] = round(usedHepSpec, 3)
	tpLevelUsedResources['memory'] = round(usedMemory, 3)
	tpLevelUsedResources['storage'] = round(usedStorage, 3)
	tpLevelUsedResources['bandwidth'] = round(usedBandwidth, 3)

def updateAllocationHierarchy(currName, prAllocObject, newHepSpec, newMemory, newStorage, newBandwidth):
	allGrAllocObjects = GroupAllocation.objects.filter(project_allocation__name = currName)
	oldHepSpec = prAllocObject.hepspec
	oldMemory = prAllocObject.memory
	oldStorage = prAllocObject.storage
	oldBandwidth = prAllocObject.bandwidth
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
