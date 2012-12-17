from xml.dom.minidom import Document
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext, loader, Context
from django.shortcuts import render_to_response
from django.conf import settings
from settings import  *
from cloudman.cloudman.models import *
from cloudman.cloudman.commonFunctions import *


doc = Document()
log_file = open("/var/www/html/cloudman.xml" , 'w')
def getAllAllocationByProject(request):
    doc = Document()
    alloc = doc.createElement("ALLOCATION")
    doc.appendChild(alloc)
    prjObjList = Project.objects.all()
    for prObj in prjObjList:
        project_name =  prObj.name
        project_node = genProject(project_name)
        counter =0
        for tpAllocNode in genTopAllocByProject(project_name):
            project_node.appendChild(tpAllocNode)
        alloc.appendChild(project_node)
    doc = doc.toprettyxml(indent="    ")
    print >>log_file ,doc
    log_file.close()
    return HttpResponse(doc, mimetype="text/xml")
        
def genTopAllocByProject(project_name):
    doc = Document()
    node_list = []
    tpAllocNameList = ProjectAllocation.objects.filter(project__name = project_name).values_list('top_level_allocation__name',flat =True).distinct()
    for tpAllocName in tpAllocNameList:
        tpAllocList = TopLevelAllocation.objects.filter(name = tpAllocName).select_related(depth=1)
        for alloc in tpAllocList:
            tp_alloc_name =  alloc.name
            child = doc.createElement("TOP_LEVEL_ALLOCATION")
            child.setAttribute("NAME",tp_alloc_name)
            child.setAttribute("GROUP",str(alloc.group.name))
            child.setAttribute("KSI2K",str(alloc.hepspec * float(KSI2K)))
            child.setAttribute("HS06",str(alloc.hepspec))
            zone_alloc_node = genZoneAlloc(tp_alloc_name)
            resource_type_node = genAllowedResourceType(tp_alloc_name)
            child.appendChild(zone_alloc_node) 
            child.appendChild(resource_type_node)
            #        child.setAttribute("MEMORY",str(alloc.memory))
            #        child.setAttribute("STORAGE",str(alloc.storage))
            #        child.setAttribute("BANDWIDTH",str(alloc.bandwidth))
            proj_alloc_list = genProjAlloc(tp_alloc_name,False)
            for proj_alloc in proj_alloc_list: 
                child.appendChild(proj_alloc)
        
                node_list.append(child)
    return node_list







#Will export all the allocation in cloudman starting from top level allocation
def getAllAllocationByTopLevel(request):
    # Create the minidom document
    doc = Document()
    # Create the <ALLOCATION> base element
    alloc = doc.createElement("ALLOCATION")
    doc.appendChild(alloc)
    #get all top_level_allocation as list
    top_alloc_node = genTopAlloc()
    for node in top_alloc_node:
        alloc.appendChild(node) #add the top_level_allocation to main tree
    
    # Print our newly created XML
    doc = doc.toprettyxml(indent="  ")
    return HttpResponse(doc, mimetype="text/xml")

#this will create the list of all the top_level_allocation node
def genTopAlloc():
    doc = Document()
    node_list = []
    tpAllocList = TopLevelAllocation.objects.select_related(depth=1)
    for alloc in tpAllocList:
        tp_alloc_name =  alloc.name
        child = doc.createElement("TOP_LEVEL_ALLOCATION")
        child.setAttribute("NAME",tp_alloc_name)
        child.setAttribute("GROUP",str(alloc.group.name))
        child.setAttribute("KSI2K",str(alloc.hepspec * float(KSI2K)))
        child.setAttribute("HS06",str(alloc.hepspec))
        zone_alloc_node = genZoneAlloc(tp_alloc_name)
        resource_type_node = genAllowedResourceType(tp_alloc_name)
        child.appendChild(zone_alloc_node) 
        child.appendChild(resource_type_node)
#       child.setAttribute("MEMORY",str(alloc.memory))
#       child.setAttribute("STORAGE",str(alloc.storage))
#       child.setAttribute("BANDWIDTH",str(alloc.bandwidth))
        proj_alloc_list = genProjAlloc(tp_alloc_name)
        for proj_alloc in proj_alloc_list: 
            child.appendChild(proj_alloc)
        
        node_list.append(child)
    return node_list


#this will create all allowed resource type for this top_level_allocation
def genAllowedResourceType(tp_alloc_name):
    doc = Document()
    node = doc.createElement("ALLOWED_RESOURCE_TYPE")
    allowedResourceTypesList = TopLevelAllocationAllowedResourceType.objects.filter(top_level_allocation__name__iexact = tp_alloc_name).order_by('resource_type__name') 
    for oneRow in allowedResourceTypesList:
        child = doc.createElement("RESOURCE_TYPE")
        child.setAttribute("NAME",str(oneRow.resource_type.name))
        child.setAttribute("ZONE",str(oneRow.zone.name))
        child.setAttribute("CLASS",str(oneRow.resource_type.resource_class ))
        child.setAttribute("HS06",str(oneRow.resource_type.hepspecs ))
        child.setAttribute("MEMORY",str(oneRow.resource_type.memory ))  
        child.setAttribute("STORAGE",str(oneRow.resource_type.storage ))
        child.setAttribute("BANDWIDTH",str(oneRow.resource_type.bandwidth ))
#       child.setAttribute("MEMORY",str())
#       child.setAttribute("STORAGE",str())
#       child.setAttribute("BANDWIDTH",str())
        child.setAttribute("REGION",str(oneRow.zone.region.name))
        node.appendChild(child)
    return node


###this will generate the project information 
def genProject(project_name):
    node = doc.createElement("PROJECT")
    projectInfo = Project.objects.get(name__iexact = project_name)
    description = projectInfo.description
    admin_group = projectInfo.admin_group
    node.setAttribute("NAME",project_name)
    node.setAttribute("DESCRIPTION",description)
    node.setAttribute('ADMINGROUP',admin_group)
    node.appendChild(genProjectMetaData(project_name))
    return node 


##will create and return the MetaData for the given project
def genProjectMetaData(project_name):
    doc = Document()
    node = doc.createElement("PROJECT_METADATA")
    metadata_list = ProjectMetadata.objects.filter(project__name = project_name)
    for metadata in metadata_list:
        child = doc.createElement("METADATA")
        child.setAttribute("NAME",str(metadata.attribute))
        child.setAttribute("VALUE",str(metadata.value))
        node.appendChild(child)
    return node











# this will create the list of all the zone allocation for the top_level_allocation
def genZoneAlloc(tp_alloc_name):
    doc = Document()
    node = doc.createElement("ZONE_ALLOCATION") 
    allocZonesInfo = TopLevelAllocationByZone.objects.filter(top_level_allocation__name__iexact = tp_alloc_name).order_by('zone__name')
    for oneZone in allocZonesInfo:
        child = doc.createElement("ZONE")
        child.setAttribute("NAME",str(oneZone.zone.name))
        hs06 = oneZone.hepspec
        child.setAttribute("HS06",str(hs06))
        child.setAttribute("KSI2K",str( hs06 * float(KSI2K)))
#       child.setAttribute("MEMORY",str())
#       child.setAttribute("STORAGE",str())
#       child.setAttribute("BANDWIDTH",str())
        child.setAttribute("REGION",str(oneZone.zone.region.name))
        node.appendChild(child)
    return node


#this will create all the project_allocation for a given top_level_allocation_name
def genProjAlloc(tp_alloc_name,showprojectinfo=True):
    doc = Document()
    alloc_list = ProjectAllocation.objects.filter(top_level_allocation__name = tp_alloc_name).select_related(depth=1)
#    alloc_list = ProjectAllocation.objects.filter(project__name = project_name).select_related(depth=1)
    list = []
    for alloc in alloc_list:
        alloc_name = alloc.name
        child = doc.createElement("PROJECT_ALLOCATION")
        child.setAttribute("NAME",alloc_name)
        child.setAttribute("GROUP",str(alloc.group.name))
        project_name = alloc.project.name
        if showprojectinfo:
            child.appendChild(genProject(project_name))
            child.appendChild(genProjectAllocMetaData(alloc_name))
        hepspec = alloc.hepspec
        tp_alloc_hepspec = alloc.top_level_allocation.hepspec
        hepspec_percent = float(hepspec)*100/float(tp_alloc_hepspec)
        child.setAttribute("KSI2K",str(hepspec * float(KSI2K)))
        child.setAttribute("HS06",str(hepspec))
        child.setAttribute("HS06PERCENT",str(hepspec_percent))
#       child.setAttribute("MEMORY",str(alloc.memory))
#       child.setAttribute("STORAGE",str(alloc.storage))
#       child.setAttribute("BANDWIDTH",str(alloc.bandwidth))
        
        gpAllocNode = genGroupAlloc(alloc_name) #get the group_allocation for this project_allocation
        for node1 in gpAllocNode:
            child.appendChild(node1) # add the group_allocation_node to the project_allocation_tree
        list.append(child)      
    return list 


##will create and return the MetaData child for the given group_allocation 
def genProjectAllocMetaData(prj_alloc_name):
    doc = Document()
    node = doc.createElement("PROJECT_ALLOCATION_METADATA")
    alloc_list = ProjectAllocationMetadata.objects.filter(project_allocation__name = prj_alloc_name)
    for prjAllocMeta in alloc_list:
        child = doc.createElement("METADATA")
        child.setAttribute("NAME",str(prjAllocMeta.attribute))
        child.setAttribute("VALUE",str(prjAllocMeta.value))
        node.appendChild(child)
    return node





##will create and return the MetaData child for the given group_allocation 
def genGroupAllocMetaData(gp_alloc_name):
    doc = Document()
    node = doc.createElement("GROUP_ALLOCATION_METADATA")
    alloc_list = GroupAllocationMetadata.objects.filter(group_allocation__name = gp_alloc_name)
    for gpAllocMeta in alloc_list:
        child = doc.createElement("METADATA")
        attribute = gpAllocMeta.attribute
        value = gpAllocMeta.value
        if attribute.lower() == 'EGROUP'.lower():
            user_list = getUserListfromEgroup(value)
            egroup_child = doc.createElement("METADATA")
            egroup_child.setAttribute("NAME","USER_LIST_LDAP")
            egroup_child.setAttribute("VALUE",user_list)                 
            node.appendChild(egroup_child)
        child.setAttribute("NAME",attribute)
        child.setAttribute("VALUE",value)
        node.appendChild(child)
    return node

##will generate the Group allocation for the given project allocation it will return the list of group allocation node
def genGroupAlloc(pr_alloc_name):
    doc = Document()
    alloc_list = GroupAllocation.objects.filter(project_allocation__name = pr_alloc_name).select_related('group')
    list = []
    for alloc in alloc_list:
        alloc_name = alloc.name
        hepspec = alloc.hepspec
        pr_alloc_hepspec = alloc.project_allocation.hepspec
        hepspec_percent = float(hepspec)*100/float(pr_alloc_hepspec)
        child = doc.createElement("GROUP_ALLOCATION")
        child.setAttribute("NAME",alloc_name)
        child.setAttribute("GROUP",str(alloc.group.name))
        child.setAttribute("KSI2K",str(alloc.hepspec * float(KSI2K)))
        child.setAttribute("HS06",str(alloc.hepspec))
        child.setAttribute("HS06PERCENT",str(hepspec_percent))
        
#       child.setAttribute("MEMORY",str(alloc.memory))
#       child.setAttribute("STORAGE",str(alloc.storage))
#       child.setAttribute("BANDWIDTH",str(alloc.bandwidth))
        child.appendChild(genGroupAllocMetaData(alloc_name))
        #get all the sub_group_allocation for this group_allocation
        subgrp_alloc_node = genSubGroupAlloc(alloc_name)
        for node1 in subgrp_alloc_node:
            child.appendChild(node1) # add the sub_group_allocation_node to the group_allocation_tree
        list.append(child)
    return list


##will generate all the subgroup_allocation for the given group_allocation_name
def genSubGroupAlloc(gp_alloc_name):
    doc = Document()
    allocList = GroupAllocation.objects.filter(parent_group_allocation__name = gp_alloc_name).select_related('group')
    list = []
    for alloc in allocList:
        alloc_name = alloc.name
        child = doc.createElement("GROUP_ALLOCATION")
        child.setAttribute("NAME",alloc_name)
        child.setAttribute("GROUP",str(alloc.group.name))
        child.setAttribute("KSI2K",str(alloc.hepspec * float(KSI2K)))
        child.setAttribute("HS06",str(alloc.hepspec))
#       child.setAttribute("MEMORY",str(alloc.memory))
#       child.setAttribute("STORAGE",str(alloc.storage))
#       child.setAttribute("BANDWIDTH",str(alloc.bandwidth))
        child.appendChild(genGroupAllocMetaData(alloc_name))
        #get all the sub_group_allocation for this group_allocation
        subgrp_alloc_node = genSubGroupAlloc(alloc_name)
        for node1 in subgrp_alloc_node:
            child.appendChild(node1) # add the sub_group_allocation_node to the group_allocation_tree
        list.append(child)
    return list
