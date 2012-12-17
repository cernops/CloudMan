from cloudman.cloudman.models import TopLevelAllocationByZone,TopLevelAllocation,TopLevelAllocationAllowedResourceType
from cloudman.cloudman.models import ProjectAllocation,Project,ProjectMetadata,ProjectAllocationMetadata,GroupAllocation
from cloudman.cloudman.models import GroupAllocationMetadata
from cloudman.cloudman.commonFunctions import getKSI2K,getPercent,getUserListfromEgroup
from settings import  *



#Will export all the allocation in cloudman starting from top level allocation
def getAllAllocationByProject(resolve):
    # Create the <ALLOCATION> base element
    global resolvegroup
    resolvegroup = resolve
    alloc = {'PROJECT_ALL':  []}
    prjObjList = Project.objects.all()
    for prObj in prjObjList:
        project_name =  prObj.name
        project_attr = genProject(project_name)
        project_attr['TOP_LEVEL_ALLOCATION_ALL'] = []
        for tpAllocNode in genTopAllocByProject(project_name):
            project_attr['TOP_LEVEL_ALLOCATION_ALL'].append(tpAllocNode)
        alloc['PROJECT_ALL'].append({'PROJECT':project_attr})
    return alloc




#Will export all the allocation in cloudman starting from top level allocation
def getAllAllocationByTopLevel(resolve):
    # Create the <ALLOCATION> base element
    global resolvegroup
    resolvegroup = resolve
    alloc = {'TOP_LEVEL_ALLOCATION_ALL':  []}
    #get all top_level_allocation as list
    top_alloc_node = genTopAlloc()
    for node in top_alloc_node:
        alloc['TOP_LEVEL_ALLOCATION_ALL'].append(node) #add the top_level_allocation to main tree
    
    return alloc

def genTopAllocByProject(project_name):
    node_list = []
    tpAllocNameList = ProjectAllocation.objects.filter(project__name = project_name).values_list('top_level_allocation__name',flat =True).distinct()
    for tpAllocName in tpAllocNameList:
        tpAllocList = TopLevelAllocation.objects.filter(name = tpAllocName).select_related(depth=1)
        for alloc in tpAllocList:
            tp_alloc_name =  alloc.name
            attribute = {}
            attribute['NAME'] = tp_alloc_name
            attribute['GROUP'] = str(alloc.group.name)
            attribute['KSI2K'] = str(alloc.hepspec * float(KSI2K))
            attribute['HS06'] = str(alloc.hepspec)
            zone_alloc_node = genZoneAlloc(tp_alloc_name)
            resource_type_node = genAllowedResourceType(tp_alloc_name)
            attribute['ZONE_ALLOCATION'] = zone_alloc_node 
            attribute['ALLOWED_RESOURCE_TYPE'] = resource_type_node
            attribute['MEMORY'] = str(alloc.memory)
            attribute['STORAGE'] = str(alloc.storage)
            attribute['BANDWIDTH'] = str(alloc.bandwidth)
            proj_alloc_list = genProjAlloc(tp_alloc_name,False)
            attribute['PROJECT_ALLOCATION_ALL'] = proj_alloc_list
            child = {'TOP_LEVEL_ALLOCATION':attribute}
            node_list.append(child)
    return node_list



#this will create the list of all the top_level_allocation node
def genTopAlloc():
    node_list = []
    tpAllocList = TopLevelAllocation.objects.select_related(depth=1)
    for alloc in tpAllocList:
        tp_alloc_name =  alloc.name
        attribute = {}
        attribute['NAME'] = tp_alloc_name
        attribute['GROUP'] = str(alloc.group.name)
        attribute['KSI2K'] = str(getKSI2K(alloc.hepspec))
        attribute['HS06'] = str(alloc.hepspec)
        attribute['MEMORY'] = str(alloc.memory)
        attribute['STORAGE'] = str(alloc.storage)
        attribute['BANDWIDTH'] = str(alloc.bandwidth)
        zone_alloc = genZoneAlloc(tp_alloc_name)
        attribute['ZONE_ALLOCATION'] = zone_alloc
        resource_type = genAllowedResourceType(tp_alloc_name)
        attribute['ALLOWED_RESOURCE_TYPE'] = resource_type
        proj_alloc = genProjAlloc(tp_alloc_name)
        attribute['PROJECT_ALLOCATION_ALL'] = proj_alloc 
        child = {'TOP_LEVEL_ALLOCATION':attribute}
        node_list.append(child)
    return node_list

#this will create all the project_allocation for a given top_level_allocation_name
def genProjAlloc(tp_alloc_name,showprojectinfo=True):
    alloc_list = ProjectAllocation.objects.filter(top_level_allocation__name = tp_alloc_name).select_related(depth=1)
    prj_alloc_list = []
    for alloc in alloc_list:
        alloc_name = alloc.name
        attribute = {}
        attribute['NAME'] = alloc_name
        attribute['GROUP'] = str(alloc.group.name)
        project_name = alloc.project.name
        if showprojectinfo:
            attribute['PROJECT'] = genProject(project_name)
            attribute['PROJECT_ALLOCATION_METADATA']  = genProjectAllocMetaData(alloc_name)
        hepspec = alloc.hepspec
        tp_alloc_hepspec = alloc.top_level_allocation.hepspec
        hepspec_percent = str(getPercent(hepspec ,tp_alloc_hepspec ))
        attribute['KSI2K'] = str(getKSI2K(hepspec))
        attribute['HS06'] = str(hepspec)
        attribute['HS06PERCENT'] = str(hepspec_percent)
        attribute['MEMORY'] = str(alloc.memory)
        attribute['STORAGE'] = str(alloc.storage)
        attribute['BANDWIDTH'] = str(alloc.bandwidth)
        child = {'PROJECT_ALLOCATION':attribute}
        gp_alloc_list = genGroupAlloc(alloc_name) #get the group_allocation for this project_allocation
        attribute['GROUP_ALLOCATION_ALL'] = gp_alloc_list
        prj_alloc_list.append(child)      
    return prj_alloc_list 


##will generate the Group allocation for the given project allocation it will return the list of group allocation node
def genGroupAlloc(alloc_name,top_group = True):
    if top_group:
        grpAllocObj_list = GroupAllocation.objects.filter(project_allocation__name = alloc_name).select_related('group')
    else:
        grpAllocObj_list = GroupAllocation.objects.filter(parent_group_allocation__name = alloc_name).select_related('group')
    grp_alloc_list = []
    for alloc in grpAllocObj_list:
        grpalloc_name = alloc.name
        hepspec = alloc.hepspec
        if top_group:
            parent_hepspec = alloc.project_allocation.hepspec
        else:
            parent_hepspec = alloc.parent_group_allocation.hepspec
        attribute  ={}
        attribute['NAME'] = grpalloc_name
        attribute['GROUP'] = str(alloc.group.name)
        attribute['KSI2K'] = str(getKSI2K(alloc.hepspec))
        attribute['HS06'] = str(alloc.hepspec)
        attribute['HS06PERCENT'] = str(getPercent(hepspec,parent_hepspec))
        attribute['MEMORY'] = str(alloc.memory)
        attribute['STORAGE'] = str(alloc.storage)
        attribute['BANDWIDTH'] = str(alloc.bandwidth)
        attribute['GROUP_ALLOCATION_METADATA'] = genGroupAllocMetaData(grpalloc_name)
        attribute['GROUP_ALLOCATION_ALL'] = genGroupAlloc(grpalloc_name,False)
        child = {'GROUP_ALLOCATION':attribute}
        grp_alloc_list.append(child)
    return grp_alloc_list


##will create and return the MetaData child for the given group_allocation 
def genGroupAllocMetaData(gp_alloc_name):
    node = []
    grpAllocMetaObj_list = GroupAllocationMetadata.objects.filter(group_allocation__name = gp_alloc_name)
    for gpAllocMeta in grpAllocMetaObj_list:
        attribute = {}
        attrname = gpAllocMeta.attribute
        value = gpAllocMeta.value
        if attrname.lower() == 'EGROUP'.lower() and resolvegroup.lower() !='no':
            if resolvegroup.lower() =='yes' or resolvegroup.lower() =='':
                user_list = getUserListfromEgroup(value)
                egrp_resolve_attr = {}
                egrp_resolve_attr['NAME'] = 'USER_LIST_LDAP'
                egrp_resolve_attr['VALUE'] = user_list                 
                egroup_child = {'METADATA':egrp_resolve_attr}
                node.append(egroup_child)
            if resolvegroup.lower() =='':
                attribute['NAME'] = attrname
                attribute['VALUE'] = value
                child = {'METADATA':attribute}
                node.append(child)
        else:
            attribute['NAME'] = attrname
            attribute['VALUE'] = value
            child = {'METADATA':attribute}
            node.append(child)
    return node


##will create and return the MetaData child for the given group_allocation 
def genProjectAllocMetaData(prj_alloc_name):
    node = []
    alloc_list = ProjectAllocationMetadata.objects.filter(project_allocation__name = prj_alloc_name)
    for prjAllocMeta in alloc_list:
        attribute = {}
        attribute['NAME'] = str(prjAllocMeta.attribute)
        attribute['VALUE'] = str(prjAllocMeta.value)
        child = {'METADATA':attribute}
        node.append(child)
    return node

###this will generate the project information 
def genProject(project_name):
    projectInfo = Project.objects.get(name__iexact = project_name)
    description = projectInfo.description
    admin_group = projectInfo.admin_group
    attribute  = {}
    attribute['NAME'] = project_name
    attribute['DESCRIPTION'] = description
    attribute['ADMINGROUP'] = admin_group
    attribute['PROJECT_METADATA']  = genProjectMetaData(project_name)
    return attribute 


##will create and return the MetaData for the given project
def genProjectMetaData(project_name):
    prj_metadatalist = []
    metadata_list = ProjectMetadata.objects.filter(project__name = project_name)
    for metadata in metadata_list:
        attribute = {}
        attribute['NAME'] = str(metadata.attribute)
        attribute['VALUE'] = str(metadata.value)
        child = {'METADATA':attribute}
        prj_metadatalist.append(child)
    return prj_metadatalist

#this will create all allowed resource type for this top_level_allocation
def genAllowedResourceType(tp_alloc_name):
    node = []
    allowedResourceTypesList = TopLevelAllocationAllowedResourceType.objects.filter(top_level_allocation__name__iexact = tp_alloc_name).order_by('resource_type__name') 
    for oneRow in allowedResourceTypesList:
        attribute = {}
        attribute['NAME'] = str(oneRow.resource_type.name)
        attribute['ZONE'] = str(oneRow.zone.name)
        attribute['CLASS'] = str(oneRow.resource_type.resource_class )
        attribute['HS06'] = str(oneRow.resource_type.hepspecs )
        attribute['MEMORY'] = str(oneRow.resource_type.memory )  
        attribute['STORAGE'] = str(oneRow.resource_type.storage )
        attribute['BANDWIDTH'] = str(oneRow.resource_type.bandwidth )
        attribute['REGION'] = str(oneRow.zone.region.name)
        child = {'RESOURCE_TYPE':attribute}
        node.append(child)
    return node

# this will create the list of all the zone allocation for the top_level_allocation
def genZoneAlloc(tp_alloc_name):
    node = [] 
    allocZonesInfo = TopLevelAllocationByZone.objects.filter(top_level_allocation__name__iexact = tp_alloc_name).order_by('zone__name')
    for oneZone in allocZonesInfo:
        attribute = {}
        attribute['NAME'] = str(oneZone.zone.name)
        hs06 = oneZone.hepspec
        attribute['HS06'] = str(hs06)
        attribute['KSI2K'] = str(getKSI2K(hs06))
        attribute['MEMORY'] = str(oneZone.memory)
        attribute['STORAGE'] = str(oneZone.storage)
        attribute['BANDWIDTH'] = str(oneZone.bandwidth)
        attribute['REGION'] = str(oneZone.zone.region.name)
        child = {'ZONE':attribute}
        node.append(child)
    return node