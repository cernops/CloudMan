from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from models import Region,Egroups,ZoneAllowedResourceType,TopLevelAllocationByZone,TopLevelAllocation
from forms import RegionForm
from django.db.models import Sum
from templatetags.filters import displayNone
from models import Zone
from django.db import transaction
from getPrivileges import isSuperUser
from ldapSearch import checkEGroup
from django.db.models import Q
from commonFunctions import addLog,getLog,getRegionInfo,addUpdateLog
from validator import *
from django.db import connection
import simplejson
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from commonFunctions import *
def checkNameIgnoreCase(regionName):
	regionExists = False
	if Region.objects.filter(name__iexact=regionName).exists():
		regionExists = True
	return regionExists

def isAdminOfAnyRegion(adminGroups):
	userIsAdmin = False
	if len(adminGroups) < 1:
	   return userIsAdmin
	qset = Q(admin_group__exact=adminGroups[0])
	if len(adminGroups) > 1:
	   for group in adminGroups[1:]:
		 qset = qset | Q(admin_group__exact=group)
	if (Region.objects.filter(qset)).exists():
		userIsAdmin = True
	return userIsAdmin

def isAdminForRegion(regionName, adminGroups):
	userIsAdminOfRegion = False
	if len(adminGroups) < 1:
	   return userIsAdminOfRegion
	try:
	   #regionGroup = Region.objects.get(name=regionName).values_list('admin_group__name')
	   regionObj = Region.objects.get(name=regionName)
	   regiongroup = regionObj.admin_group.name
	   if regiongroup in adminGroups:
		  userIsAdminOfRegion = True
	   else:
		  userIsAdminOfRegion = False	   
	except Region.DoesNotExist:
	   return userIsAdminOfRegion
	return userIsAdminOfRegion

def isUserAllowedToUpdateOrDeleteRegion(regionName,groupsList):
	userIsSuperUser = isSuperUser(groupsList)
	if userIsSuperUser:
		return True
	else:
		userIsAdmin = isAdminForRegion(regionName, groupsList)
		return userIsAdmin

@transaction.commit_on_success
def addnew(request):
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';') ;
	userIsSuperUser = isSuperUser(groupsList)
	## Check user cloudman resource manager privileges
	if not userIsSuperUser:
		message = "You don't have cloudman resource manager privileges. Hence you are not authorized to add new Region";
		html = "<html><body> %s.</body></html>" % message
		return HttpResponse(html)
	if request.method == 'POST':
		form = RegionForm(request.POST)
		### Check whether all the fields for creating a region are provided with non-empty values
		if form.is_valid():
			redirectURL = '/cloudman/message/?msg='
			name = form.cleaned_data['name']
			regionExists = checkNameIgnoreCase(name)
			if regionExists:
				msgAlreadyExists = 'Region ' + name + ' already exists. Hence Add Region Operation Stopped'
				return HttpResponseRedirect(redirectURL + msgAlreadyExists)
			description = form.cleaned_data['description']
			admin_group = form.cleaned_data['admin_group']
			comment = form.cleaned_data['comment']	
			## Check that name provided as admin_group exists in the EGroups TABLE
			## If not, then check its existence in external egroup database through ldap
			## If not present there also, then raise an alert or else add the group name to EGroups table also
			egroup = None
			try:
				egroup = Egroups.objects.get(name=admin_group)
			except Egroups.DoesNotExist:
				if not (checkEGroup(admin_group)):
					errorMessage = 'Selected Admin E-Group ' + admin_group + ' does not exists'
					return HttpResponseRedirect(redirectURL + errorMessage)
				egroup = Egroups(name=admin_group)
				egroup.save()
			## Create the Region with all the required values
			regionObj = Region(name=name, description=description, admin_group=egroup)
			regionObj.save()
			regionObj = Region.objects.get(name=name)
			if addLog(request,name,comment,regionObj,None,'region','add',True):
				transaction.commit()
				## Return the Success message
				msgSuccess = 'New region ' + name  + ' added successfully'
			else:
				transaction.rollback()
				msgSuccess = 'Error in creating New region ' + name				
			html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/region/list/\"></HEAD><body> %s.</body></html>" % msgSuccess
			return HttpResponse(html)
	else:
		## If not POST operation, then return the Region Creation Form
		form = RegionForm()
	return render_to_response('region/addnew.html',locals(),context_instance=RequestContext(request))

def regionAllZoneInfo(request):
	mimetype = 'application/javascript'
	regionName = request.REQUEST.get("name", "")
	jsondata = []
	try:
		zoneInfoList = Zone.objects.filter(region__name = regionName).all()
		for zoneInfo in zoneInfoList:
			jsondata.append({'hepspec':displayNone(zoneInfo.hepspecs),'memory':displayNone(zoneInfo.memory),'storage':displayNone(zoneInfo.storage),'bandwidth':displayNone(zoneInfo.bandwidth),'zonename':zoneInfo.name,'description':zoneInfo.description,'memoryovercommit':zoneInfo.memory_overcommit,'hepspecovercommit':zoneInfo.hepspec_overcommit})
	except Exception:
		printStackTrace()
	data = simplejson.dumps(jsondata)
	return HttpResponse(data,mimetype)	
	


def listall(request):
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';') ;
	userIsSuperUser = isSuperUser(groupsList)
	zoneInfo = Zone.objects.values('region_id').annotate(hepspec=Sum('hepspecs'),memory=Sum('memory'),storage=Sum('storage'),bandwidth=Sum('bandwidth'))
	region_capacity = {}
	for item in zoneInfo:
		region_capacity[item['region_id']] = {'hepspec':item['hepspec'],'memory':item['memory'],'storage':item['storage'],'bandwidth':item['bandwidth']}
	regionInfoList = []
	regionsList = Region.objects.all().order_by('name').select_related('admin_group__name')
	for region in regionsList:
		if region.id in region_capacity:
			regionInfoList.append({'name':region.name,'egroup':region.admin_group.name,'description':region.description,'capacity':region_capacity[region.id]}) 
		else:
			regionInfoList.append({'name':region.name,'egroup':region.admin_group.name,'description':region.description,'capacity':{'hepspec':None,'memory':None,'storage':None,'bandwidth':None}})
	return render_to_response('region/listall.html',locals(),context_instance=RequestContext(request))

def getdetails(request):
	regionName = request.REQUEST.get("name", "")
	regionInfo = None
	redirectURL = '/cloudman/message/?msg='
	## Get the region object
	try:
	   regionInfo = Region.objects.select_related('admin_group').get(name=regionName)
	except Region.DoesNotExist:
	   errorMessage = 'Region Name ' + regionName + ' does not exists'
	   return HttpResponseRedirect(redirectURL + errorMessage)

	## Get the zones information located in this region
	zonesInfo = Zone.objects.filter(region__name = regionName).order_by('name')

	## Get the allowed resource types information for all the zones present in this region
	allowedResourceTypesList = ZoneAllowedResourceType.objects.select_related('resource_type','zone').filter(zone__region__name=regionName).order_by('resource_type__name')
	object_id = regionInfo.id
	changeLogList = getLog('region',regionName,object_id,None)
	return render_to_response('region/getdetails.html',locals(),context_instance=RequestContext(request))

@transaction.commit_on_success
def delete(request):
	regionName = request.REQUEST.get("name", "")
	comment = request.REQUEST.get("comment", "deleting")
	redirectURL = '/cloudman/message/?msg='
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';') ;
	## Update is allowed if user has either cloudman resource manager privileges or 
	## belongs to the egroup selected as administrative e-group for this region
	if  not isUserAllowedToUpdateOrDeleteRegion(regionName,groupsList):
		message = "You neither have membership of administrative group of region " + regionName + " nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to Delete Region"
		html = "<html><body> %s.</body></html>" % message		
		return HttpResponse(html)

	## Get the Region Object
	regionObject = None
	try:
	   regionObject = Region.objects.get(name=regionName)
	except Region.DoesNotExist:
	   failureMessage = "Region with Name " + regionName + " could not be found"
	   return HttpResponseRedirect(redirectURL+failureMessage)

	## Check whether any zones are defined for this region
	zoneNames = Zone.objects.filter(region__name__iexact = regionName).values_list('name', flat=True).order_by('name')
	finalMessage = ''
	zoneNamesList = list(zoneNames)

	## If zones are defined, then alert the user and do not delete the region
	if len(zoneNamesList) > 0:
	   finalMessage = finalMessage + "Zone Names: " + (', '.join(zoneNamesList)) + "<br/>"
	if not finalMessage == '':
	   finalMessage = "Region with Name " + regionName + " Could not be deleted because it is being used in " + "<br/>" + finalMessage
	   html = "<html><body> %s</body></html>" % finalMessage
	   return HttpResponse(html)
  
	## If no zones, then delete the region and return a success message to the user
	status = addLog(request,regionName,comment,regionObject,None,'region','delete',False)
	regionObject.delete()
	if status:
		transaction.commit()
		message = "Region with Name " + regionName + " deleted successfully "
	else:
		transaction.rollback()
		message = "Error in deleting Region with Name " + regionName
	html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/region/list/\"></HEAD><body> %s.</body></html>" % message
	return HttpResponse(html)

def getstats(request):
	## Provide the region resource statistics in json format
	## If the request is not an ajax call, then return status 400 - BAD REQUEST

	## First, the entire region hepspecs information is calculated (how much total and how much used)
	## Then, for each zone in this region, individual hepspecs stats will be published (how much total and how much used)

	#if request.is_ajax():
	   format = 'json'
	   mimetype = 'application/javascript'
	   regionName = request.GET['name']
	   ## Step 1: Entire Region Stats
	   ## Get the sum of Hepspec from all the zones in this region 
	   ## If all the zones have a NULL value, then assign the sum to 0
	   totalRegionHepSpecs = sum([zn.hepspectotal() for zn in  Zone.objects.filter(region__name=regionName)])
	   if (totalRegionHepSpecs == None):
		 totalRegionHepSpecs = 0

	   ## Get the hepspec of each top level allocation done using resources from this region
	   topLevelAllocationByZoneObjects = TopLevelAllocationByZone.objects.filter(zone__region__name=regionName).values('hepspec')

	   ## calculate the total hepspec by adding all the top level allocation hepspec from this region		
	   totalAllocHepSpecs = 0.0
	   for oneObject in topLevelAllocationByZoneObjects:
		 if (oneObject['hepspec'] != None):
		   totalAllocHepSpecs = totalAllocHepSpecs + oneObject['hepspec']

	   ## Frame a json object with the total and used hepspec values for this region
	   regionStatsInfo = [{"pk": regionName, "model": "cloudman.region", "fields": {"tothepspecs": totalRegionHepSpecs, "usedhepspecs": totalAllocHepSpecs}}]

	   ## Step 2: Stats for each Zone in this region
	   ## Get the names of all the zones in this region
	   zonesList = Zone.objects.filter(region__name=regionName).values('name').order_by('name') 
	   for zoneInfo in zonesList:	   
		  zoneName = zoneInfo['name']

		  ## Calculate the hepspec of the zone (remember hepspec_overcommit and so use function hepspectotal())
		  totalZoneHepSpecs =  Zone.objects.get(name=zoneName, region__name=regionName)
		  if totalZoneHepSpecs.hepspecs == None:
			totalZoneHepSpecs.hepspecs = 0
		  else:
			totalZoneHepSpecs.hepspecs = totalZoneHepSpecs.hepspectotal()

		  ## Now get the total hepspec already allocated from this zone in the top level allocations
 
		  topLevelAllocationByZoneObjects = TopLevelAllocationByZone.objects.filter(zone__name=zoneName, zone__region__name=regionName).values('hepspec')
		  totalAllocHepSpecs = 0.0
		  for oneObject in topLevelAllocationByZoneObjects:
			if (oneObject['hepspec'] != None):
			  totalAllocHepSpecs = totalAllocHepSpecs + oneObject['hepspec']

		  ## Frame a json object for each zone with their hepspec stats
		  regionStatsInfo.append({"pk": zoneName, "model": "cloudman.zone", "fields": {"tothepspecs": totalZoneHepSpecs.hepspecs, "usedhepspecs": totalAllocHepSpecs}})

	   ## finally dump the json objects and send that as a response to the ajax query
	   data = simplejson.dumps(regionStatsInfo)
	   return HttpResponse(data,mimetype)
	#else:
	#	return HttpResponse(status=400)

@transaction.commit_on_success
def update(request):
	regionName = request.REQUEST.get("name", "")
	redirectURL = '/cloudman/message/?msg='
	groups = request.META.get('ADFS_GROUP','')
	groupsList = groups.split(';') ;
	## Update is allowed if user has either cloudman resource manager privileges or 
	## belongs to the egroup selected as administrative e-group for this region
	if  not isUserAllowedToUpdateOrDeleteRegion(regionName,groupsList):
		message = "You neither have membership of administrative group of region " + regionName + " nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to Edit Region";
		html = "<html><body> %s.</body></html>" % message
		return HttpResponse(html)
	## Get the region Object
	regionObject = None
	try:
		regionObject = Region.objects.get(name=regionName)
	except Region.DoesNotExist:
		failureMessage = "Region with Name " + regionName + " could not be found"
		return HttpResponseRedirect(redirectURL+failureMessage)
	oldRegionInfo = getRegionInfo(regionObject)
	## If the current request is due to form submission then do update 
	## or else return to template to display the update form
	if request.method == 'POST':
	        ## Existing values
		currName = regionObject.name
		currDescription = regionObject.description
		currAdmin_group = regionObject.admin_group
		## New Values
		newName = request.POST['name']
		newDescription = request.POST['description']
		newAdmin_group = request.POST['admin_group']
		comment = request.REQUEST.get("comment", "")
		try:
			validate_name(newName)
			validate_descr(newDescription)
			validate_name(newAdmin_group)
			validate_comment(comment)
		except ValidationError as e:
			message ='Edit Region Form  '+', '.join(e.messages)
			html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/region/list/\"></HEAD><body> %s.</body></html>" % message
			return HttpResponse(html)
		## Check for atleast one field value change
		if ( (currName == newName) and (currDescription == newDescription) and (currAdmin_group == newAdmin_group) ):
			message = 'No New Value provided for any field to perform Edit Operation. Hence Edit Region ' + regionName + ' aborted'
			return HttpResponseRedirect(redirectURL + message)
		## Assign the new name to the region if it is changed
		if (currName != newName):
			if (newName == ''):
				errorMsg = 'Region name field cannot be left blank. So Edit Region operation stopped'
				return HttpResponseRedirect(redirectURL + errorMsg)
			regionExists = checkNameIgnoreCase(newName)
			if regionExists:
				msgAlreadyExists = 'Region ' + newName + ' already exists. Hence Edit Region Operation Stopped'
				return HttpResponseRedirect(redirectURL + msgAlreadyExists);
			regionObject.name = newName
		## Assign the new description if it is changed
		if (currDescription != newDescription):
			regionObject.description = newDescription
		## If admin egroup is changed, then first check its existence in the local egroups table
		## If not present, then check its existence in the external egroup database through ldap
		## If checked using external database and found, then add the egroup to the local egroups table
		## If not found both local and external, then return an error to the user
		egroup = None
		if (currAdmin_group != newAdmin_group):
			if (newAdmin_group == ''):
				errorMsg = 'Admin E-Group field cannot be left blank. So Edit Region operation stopped'
				return HttpResponseRedirect(redirectURL + errorMsg)
			try:
				egroup = Egroups.objects.get(name=newAdmin_group)
			except Egroups.DoesNotExist:
				if not (checkEGroup(newAdmin_group)):
					errorMessage = 'Selected Admin E-Group ' + newAdmin_group + ' does not exists'
					return HttpResponseRedirect(redirectURL + errorMessage)
				egroup = Egroups(name=newAdmin_group)
				egroup.save()
			regionObject.admin_group = egroup
		## Save the new values and return success message to the user
		regionObject.save()
		newRegionInfo = getRegionInfo(regionObject)
		objectId = regionObject.id 
		if addUpdateLog(request,newName,objectId,comment,oldRegionInfo,newRegionInfo,'region',True):
			transaction.commit()
			message = 'Region ' + regionName + ' Successfully Updated'
		else:
			message = 'Error in Updating Region ' + regionName
			transaction.rollback()
		html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/region/list/\"></HEAD><body> %s.</body></html>" % message

      		return HttpResponse(html)
        else:
                form=RegionForm();    

	return render_to_response('region/update.html',locals(),context_instance=RequestContext(request))

def listonlynames(request):
    regionsNameList = Region.objects.all().values('name').order_by('name')
    return render_to_response('region/listonlynames.html',locals(),context_instance=RequestContext(request))

## The following functions as of now not used..they are used to draw pie charts with matplotlib python library
def getRegionHepSpecsPieChart(request):
	regionName = request.REQUEST.get("regionname", "")
	#totalRegionsHepSpecs =  Zone.objects.filter(region__name=regionName).aggregate(total_hepSpecs=Sum('hepspecs'))
	totalRegionHepSpecs = sum([zn.hepspectotal() for zn in	Zone.objects.filter(region__name=regionName)])
	if (totalRegionHepSpecs == None):
	   totalRegionHepSpecs = 0

	topLevelAllocationByZoneObjects = TopLevelAllocationByZone.objects.filter(zone__region__name=regionName).values('hepspec_fraction', 'zone__hepspecs')
	totalAllocHepSpecs = 0.0
	for oneObject in topLevelAllocationByZoneObjects:
		if ( (oneObject['hepspec_fraction'] != None) and (oneObject['zone__hepspecs'] != None) ):
		   totalAllocHepSpecs = totalAllocHepSpecs + ((oneObject['hepspec_fraction'] * oneObject['zone__hepspecs'])/100)
	fig = Figure(figsize=(4,4))
	canvas = FigureCanvas(fig)
	ax = fig.add_subplot(111)
	labels = []
	fracs = []
	allotedPer = 0
	if totalRegionHepSpecs > 0:
		allotedPer = (totalAllocHepSpecs/totalRegionHepSpecs) * 100
	freePer = 100 - allotedPer
	labels.append('Free')
	fracs.append(freePer)
	if (allotedPer > 0):
	  labels.append('Allocated')
	  fracs.append(allotedPer)
	patches, texts, autotexts = ax.pie(fracs, explode=None, labels=labels, colors=('g', 'r', 'c', 'm', 'y', 'k', 'w', 'b'), autopct='%.2f%%', pctdistance=0.4, labeldistance=1.1, shadow=False)
	ax.set_title('\n Hepspec Allocation - Region - ' + regionName + '\n Total: ' + str(round(totalRegionHepSpecs, 3)), fontdict=None, verticalalignment='bottom')
	ax.grid(True)
	#fig.canvas.mpl_connect('button_press_event', onclick)
	response=HttpResponse(content_type='image/png')
	canvas.print_png(response)
	canvas.draw()
	return response

def getAllRegionHepSpecsPieChart(request):
	#totalRegionsHepSpecs =  Zone.objects.all().aggregate(total_hepSpecs=Sum('hepspecs'))
	totalRegionHepSpecs = sum([zn.hepspectotal() for zn in	Zone.objects.all()])
	if (totalRegionHepSpecs == None):
	   totalRegionHepSpecs = 0

	#totalAllocatedHepSpecs = TopLevelAllocationByZone.objects.all().extra(select = {'total': 'SUM((hepspec_fraction * zone.hepspecs)/100)'}).values('hepspec_fraction', 'zone__hepspecs', 'total')

	topLevelAllocationObjects = TopLevelAllocation.objects.all().values('hepspec')
	totalAllocHepSpecs = 0.0
	for oneObject in topLevelAllocationObjects:
		if (oneObject['hepspec'] != None):
		   totalAllocHepSpecs = totalAllocHepSpecs + oneObject['hepspec']
	fig = Figure(figsize=(4,4))
	canvas = FigureCanvas(fig)
	ax = fig.add_subplot(111)
	labels = []
	fracs = []
	allotedPer = 0
	if totalRegionHepSpecs > 0:
		allotedPer = (totalAllocHepSpecs/totalRegionHepSpecs) * 100
	freePer = 100 - allotedPer
	labels.append('Free')
	fracs.append(freePer)
	if allotedPer > 0:
	   labels.append('Allocated')
	   fracs.append(allotedPer)
	patches, texts, autotexts = ax.pie(fracs, explode=None, labels=labels, colors=('g', 'r', 'c', 'm', 'y', 'k', 'w', 'b'), autopct='%.2f%%', pctdistance=0.4, labeldistance=1.1, shadow=False)
	ax.set_title('\n Total Hepspec Allocation - All Regions \n Total: ' + str(round(totalRegionHepSpecs, 3)), fontdict=None, verticalalignment='bottom')
	ax.grid(True)
	#fig.canvas.mpl_connect('button_press_event', onclick)
	response=HttpResponse(content_type='image/png')
	canvas.print_png(response)
	canvas.draw()
	return response

def getZoneHepSpecsPieChart(request):
	regionName = request.REQUEST.get("regionname", "")
	zoneName = request.REQUEST.get("zonename", "")
	totalZoneHepSpecs =  Zone.objects.get(name=zoneName, region__name=regionName)
	if totalZoneHepSpecs.hepspecs == None:
	   totalZoneHepSpecs.hepspecs = 0
	else:
	   totalZoneHepSpecs.hepspecs = totalZoneHepSpecs.hepspectotal()
	topLevelAllocationByZoneObjects = TopLevelAllocationByZone.objects.filter(zone__name=zoneName, zone__region__name=regionName).values('hepspec_fraction', 'zone__hepspecs')
	totalAllocHepSpecs = 0.0
	for oneObject in topLevelAllocationByZoneObjects:
		if ( (oneObject['hepspec_fraction'] != None) and (oneObject['zone__hepspecs'] != None) ):
		   totalAllocHepSpecs = totalAllocHepSpecs + ((oneObject['hepspec_fraction'] * oneObject['zone__hepspecs'])/100)
	fig = Figure(figsize=(4,4))
	canvas = FigureCanvas(fig)
	ax = fig.add_subplot(111)
	labels = []
	fracs = []
	allotedPer = 0
	if (totalZoneHepSpecs.hepspecs) > 0:
		allotedPer = (totalAllocHepSpecs/totalZoneHepSpecs.hepspecs) * 100
	freePer = 100 - allotedPer
	labels.append('Free')
	fracs.append(freePer)
	if (allotedPer > 0):
	  labels.append('Allocated')
	  fracs.append(allotedPer)
	patches, texts, autotexts = ax.pie(fracs, explode=None, labels=labels, colors=('g', 'r', 'c', 'm', 'y', 'k', 'w', 'b'), autopct='%.2f%%', pctdistance=0.4, labeldistance=1.1, shadow=False)
	ax.set_title('\n Hepspec Allocation - Zone - ' + zoneName + '\n Region: ' + regionName + '(Total: ' + str(round(totalZoneHepSpecs.hepspecs, 3)) + ')', fontdict=None, verticalalignment='bottom')
	ax.grid(True)
	response=HttpResponse(content_type='image/png')
	canvas.print_png(response)
	canvas.draw()
	return response
