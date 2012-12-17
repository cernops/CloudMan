from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext, loader, Context
from django.shortcuts import render_to_response
from django.conf import settings
from getUserRoles import getUserRoles
from models import Zone 
from models import ChangeLog
from models import TopLevelAllocation 
from models import ProjectAllocation 
from getEGroupRoles import getAllEGroups
from getCount import getRegionCount
from getCount import getZoneCount
from getCount import getGroupsCount
from django.db import IntegrityError
from django import template
from getPrivileges import isSuperUser
from settings import SUPER_USER_GROUPS
import simplejson
from django.db.models import Sum

def homepanel(request):
    anyRolePresent = False
    groupUserRolePresent = False
    groupManagerRolePresent = False
    projectManagerRolePresent = False
    regionManagerRolePresent = False

    fullName = request.META.get('ADFS_FULLNAME','')
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    rolesList = getUserRoles(groupsList)
    for entry in rolesList:
        if entry[0] == 'group' and entry[1] == 'user':
            groupUserRoles = entry[2]
            if len(groupUserRoles) > 0:
                groupUserRolePresent = True
        if entry[0] == 'group' and entry[1] == 'manager':
            groupManagerRoles = entry[2]
            if len(groupManagerRoles) > 0:
                groupManagerRolePresent = True
        if entry[0] == 'project' and entry[1] == 'manager':
            projectManagerRoles = entry[2]
            if len(projectManagerRoles) > 0:
                projectManagerRolePresent = True
        if entry[0] == 'region' and entry[1] == 'manager':
            regionManagerRoles = entry[2]
            if len(regionManagerRoles) > 0:
                regionManagerRolePresent = True
    if groupUserRolePresent or groupManagerRolePresent or projectManagerRolePresent or regionManagerRolePresent:
        anyRolePresent = True
    egroupsList = getAllEGroups()
    userIsSuperUser = isSuperUser(groupsList)
    usersGroupsSet = set(groupsList)
    SUSet = set(SUPER_USER_GROUPS)

    intersectionValue = usersGroupsSet.isdisjoint(SUSet)
    intersectionSet = usersGroupsSet.intersection(SUSet)
    regionsCount = getRegionCount()
    zonesCount = getZoneCount()
    groupsCount = getGroupsCount()

    return render_to_response('homepanel.html',locals(),context_instance=RequestContext(request))




def home(request):
    title = "Welcome"
    fullName = request.META.get('ADFS_FULLNAME','')
    return render_to_response('home.html',locals(),context_instance=RequestContext(request))

def message(request):
    msgString = request.GET.get('msg','')
    html = "<html><body><h4>%s</h4></body></html>" % msgString
    return HttpResponse(html)

def homepagedata(request):
    #if request.is_ajax():
       format = 'json'
       mimetype = 'application/javascript'
           
       #totalRegionsHepSpecs =  Zone.objects.all().aggregate(total_hepSpecs=Sum('hepspecs'))
       ## Get the sum of all Hepspec in the cloudman
       totalRegionHepSpecs = sum([zn.hepspectotal() for zn in  Zone.objects.all()])
       if (totalRegionHepSpecs == None):
          totalRegionHepSpecs = 0

       ## Get the sum of Hepspec allocated in all the top level allocations
       topLevelAllocationObjects = TopLevelAllocation.objects.all().values('hepspec')
       totalAllocHepSpecs = 0.0
       for oneObject in topLevelAllocationObjects:
          if (oneObject['hepspec'] != None):
             totalAllocHepSpecs = totalAllocHepSpecs + oneObject['hepspec']
    
       ## Calculate the percentage of total cloudman Hepspec allocated to top level allocations
       regionAllocatedPer = 0
       if totalRegionHepSpecs > 0:
          regionAllocatedPer = (totalAllocHepSpecs/totalRegionHepSpecs) * 100
       regionFreePer = 100 - regionAllocatedPer

       ## Calculate the sum of Hepspec allocated in all the project allocations
       totalPrAllocHepSpecs = 0.0
       projectAllocationObjects = ProjectAllocation.objects.all().values('hepspec')
       for oneObject in projectAllocationObjects:
           if (oneObject['hepspec'] != None):
               totalPrAllocHepSpecs = totalPrAllocHepSpecs + oneObject['hepspec']

       ## Calculate the percentage of total top level allocation hepspec allocated to project allocations
       tpLevelAllocatedPer = 0
       if totalAllocHepSpecs > 0:
          tpLevelAllocatedPer = (totalPrAllocHepSpecs/totalAllocHepSpecs) * 100

       tpLevelFreePer = 100 - tpLevelAllocatedPer
       totalRegionHepSpecs = round(totalRegionHepSpecs, 3)
       regionAllocatedPer = round(regionAllocatedPer, 3)
       regionFreePer = round(regionFreePer, 3) 
       totalAllocHepSpecs = round(totalAllocHepSpecs, 3)
       tpLevelAllocatedPer = round(tpLevelAllocatedPer, 3)
       tpLevelFreePer = round(tpLevelFreePer, 3)
   
       ## put all the data in simple json string
       allData = [{"model": "cloudman.region", "fields": {"totalhepsecs": totalRegionHepSpecs, "allocatedhepspecper": regionAllocatedPer, "freehepspecper": regionFreePer}}, {"model": "cloudman.toplevelallocation", "fields": {"totalhepspecs" : totalAllocHepSpecs, "allocatedhepspecper": tpLevelAllocatedPer, "freehepspecper": tpLevelFreePer}}]
       data = simplejson.dumps(allData)
       return HttpResponse(data,mimetype)
    #else:
    #   return HttpResponse(status=400)
