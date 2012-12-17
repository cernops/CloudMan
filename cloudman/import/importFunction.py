import traceback
import ldap
from sys import stdout
##change this to vmcloudman01
#from cloudman.cloudman.models import *
#from cloudman.cloudman.groupQueries import * 
from cloudman.models import *
from cloudman.groupQueries import * 

'''This script will read the XML file(it contains experiment-name,description and Unix-group ) stored on localdisk 
Then it wil insert those pairs as separate group in Cloudman 
'''
#this will get the egroup name 
def getEgroupName(unix_group):
    if unix_group =='':
        return 'it-dep-pes-ps'#if unix_group is empty then egroup name is it-dep-pes-ps
    else:
        return '%s-admins'%unix_group

#this will get the partition hepspec from lsf_dedicated_group_hepspec dictionary
def getPartitionHepSpec(part_dict,partition):
    for key,partition_dict in part_dict.items():
        if partition in partition_dict:
            return partition_dict[partition]    
    return 0

def addNewGroup(group_name,description,admin_egroup,log_file):
    groupExists = checkNameIgnoreCase(group_name)
    if groupExists:
        print >> log_file ,'Group: "%s"EXISTS' %group_name
        return True
    try:
        egroup = Egroups.objects.get(name=admin_egroup)
    except Egroups.DoesNotExist:
        if not (checkEGroup(admin_egroup)):
            print >> log_file ,'ERROR addNewGroup E-Group: "%s" NOT EXISTS' %admin_egroup 
            return False
        else:
            egroup = Egroups(name = admin_egroup)
            egroup.save()
    r = Groups(name=group_name, description=description, admin_group=egroup)
    r.save()
    print >> log_file ,'Group: "%s" CREATED Successfully' %group_name
    return True

def addNewProject(project,description,egroup_name,dedicated,hostpartition,log_file):
    try:
        egroup = Egroups.objects.get(name = egroup_name)
    except Egroups.DoesNotExist:
        if not (checkEGroup(egroup_name)):
            print >> log_file ,'ERROR addNewProject E-Group: "%s"Not Exist for project:'%egroup_name
            return False
        else:
            egroup = Egroups(name = egroup_name)
            egroup.save()
    if Project.objects.filter(name__iexact=project).exists(): 
        print >> log_file ,'Project "%s" already exists' %project
        return True
    projectObj = Project(name=project, description=description, admin_group=egroup_name)
    projectObj.save()
    proj = Project.objects.get(name=project)
    project_metadata = ProjectMetadata(attribute = 'DEDICATED',value = dedicated,project = proj)
    project_metadata.save()
    project_metadata = ProjectMetadata(attribute = 'HOSTPARTITION',value = hostpartition,project = proj)
    project_metadata.save() 
    print >> log_file ,'project for the experiment:"%s" created with Admin e-group:"%s"' %(project,egroup_name)
    return True
#this will create the top level allocation for a experiment 
def addTopLevelAllocation(tp_alloc_name,experiment,groupshare,region_name,zone_name,resource_type,log_file):
    if Zone.objects.filter(region__name__iexact=region_name, name__iexact=zone_name).exists() is False:
        print >> log_file ,"ERROR addTopLevelAllocation No Zones Defined. First create Zones and then try to Create Top Level Allocation";
        return False
    ###Check if the group_exists or not
    if Groups.objects.filter(name__iexact=experiment).exists() is False:
        print >> log_file ,'ERROR  addTopLevelAllocation Group "%s" does not exists.' %experiment
        return False
    ##check if the rsource_type is present in the zone_name
    if ZoneAllowedResourceType.objects.filter(zone__name__iexact = zone_name , resource_type__name__iexact = resource_type) is False:
        print >> log_file ,'ERROR addTopLevelAllocation Resource Type "%s" Does not exist in Zone "%s"' %resource_type %zone_name
        return False
    ###Check if top_level_allocation already exists
    if TopLevelAllocation.objects.filter(name__iexact=tp_alloc_name).exists():
        print >> log_file ,'Top Allocation Name "%s" already exists. ' %tp_alloc_name
        return False
    ##Add the top_level_allocation for the LSFgroup
    try:
        groupRecord = Groups.objects.get(name = experiment)
        tpalloc = TopLevelAllocation(name = tp_alloc_name, group = groupRecord, hepspec = groupshare)
        tpalloc.save()
        print >>log_file ,'Top Level Allocation "%s" created Successfully' %tp_alloc_name
    except Exception, err:
        print msg >> log_file ,'ERROR addTopLevelAllocation "%s" reason : %s' %tp_alloc_name %str(err)
        return False
    ## Now assign each zone share to the Top Level Allocation By Zone table
    tpalloc = None
    try:
        tpalloc = TopLevelAllocation.objects.get(name = tp_alloc_name)
        ## Get the zone object
        zoneRecord = Zone.objects.get(name = zone_name, region__name = region_name)
        zonealloc = TopLevelAllocationByZone(top_level_allocation=tpalloc, zone=zoneRecord, hepspec=groupshare)
        zonealloc.save()
    except Exception , err:
        print  traceback.format_exc()
        tpalloc.delete()
        print >> log_file ,'ERROR addTopLevelAllocation Error in creating "%s" ' %tp_alloc_name
        return False
    ##Finally add the allowed resource type for this top-level-allocation
    try:
        resourceTypeRecord = ResourceType.objects.get(name=resource_type)               
        allowedResourceType = TopLevelAllocationAllowedResourceType(top_level_allocation=tpalloc,zone=zoneRecord, resource_type=resourceTypeRecord)
        allowedResourceType.save()
    except Exception:
        zonealloc.delete()
        tpalloc.delete()
        print traceback.format_exc()
        print >> log_file ,'ERROR addTopLevelAllocation in creating the TopLevelAllocation "%s" ' %tp_alloc_name      
        return False
###this will create the Project allocation for the experiment aka group aka project
def addProjectAllocation(pr_alloc_name,tp_alloc_name,project,group,resource_type,hepspec,dedicated,hostpartition,log_file):
    if ProjectAllocation.objects.filter(name__iexact=pr_alloc_name).exists():
        print >> log_file ,'Project Allocation: "%s" Already Exist' %pr_alloc_name
        return True
    ## Get the top level allocation Object
    topAllocObject = None
    try:
        topAllocObject = TopLevelAllocation.objects.get(name=tp_alloc_name)
    except TopLevelAllocation.DoesNotExist:
        print >> log_file ,'ERROR addProjectAllocation Top Level Allocation "%s" does not exists' %tp_alloc_name
        return False
    ##get Get the group object
    groupObject = None
    try:
        groupObject = Groups.objects.get(name=group)
    except Groups.DoesNotExist:
        print >> log_file ,'ERROR addProjectAllocation group  "%s" does not exists' %group
        return False
    ## Get the project object
    projectObject = None
    try:
        projectObject = Project.objects.get(name=project)
    except Project.DoesNotExist:
        print >> log_file ,'ERROR addProjectAllocation Project  "%s" does not exists' %project
        return False
    ##create the Project_allocation_objects
    try:
        memory = topAllocObject.memory
        storage = topAllocObject.storage
        bandwidth = topAllocObject.bandwidth
        pralloc = ProjectAllocation(name = pr_alloc_name, top_level_allocation = topAllocObject, project = projectObject, group = groupObject, hepspec = hepspec, memory = memory, storage = storage, bandwidth = bandwidth)
        pralloc.save()
    except Exception:
        print >> log_file ,'ERROR addProjectAllocation in creating Project-allocation %s ' %pr_alloc_name
        return False
    ###create the allowed_resource_type for the project_allocation
    try:    
        resourceTypeRecord = ResourceType.objects.get(name=resource_type)
        prAllocObject = ProjectAllocation.objects.get(name=pr_alloc_name)
        allowedResourceType = ProjectAllocationAllowedResourceType(project_allocation=prAllocObject,resource_type=resourceTypeRecord)
        allowedResourceType.save()
        pralloc_metadata = ProjectAllocationMetadata(attribute = 'HOSTPARTITION',value = hostpartition,project_allocation = prAllocObject,project=projectObject)
        pralloc_metadata.save()
        pralloc_metadata = ProjectAllocationMetadata(attribute = 'DEDICATED',value = dedicated,project_allocation = prAllocObject,project=projectObject)
        pralloc_metadata.save()

        print >> log_file ,'Project Allocation  "%s" created Successfully' %pr_alloc_name
    except Exception:
        ProjectAllocation.objects.filter(name=pr_alloc_name).delete()
        print >> log_file ,'ERROR addProjectAllocation in creating Project-allocation %s' %pr_alloc_name
        print  traceback.format_exc()
        return False
# here add the group allocation from the LSF data
def addGroupAllocation(gr_alloc_name,experiment,pr_alloc_name,hepspec,resource_type,hostpartition,log_file):
    if GroupAllocation.objects.filter(name__iexact=gr_alloc_name).exists():
        print >> log_file ,'Group Allocation: "%s" Already Exist' %gr_alloc_name
        return True
    ## Get the Project allocation Object
    prAllocObject = None        
    try:
        prAllocObject = ProjectAllocation.objects.get(name=pr_alloc_name)
    except ProjectAllocation.DoesNotExist:  
        print >> log_file ,'ERROR addGroupAllocation Project-Allocation "%s" does not exists' %pr_alloc_name
        return False
    #get Get the group object experiment is aka group
    groupObject = None
    try:
        groupObject = Groups.objects.get(name=experiment)
    except Groups.DoesNotExist:
        print >> log_file ,'ERROR addGroupAllocation group "%s" does not exists' %experiment
        return False
    #add the group allocation for LSF to cloudman
    try:
        gralloc = GroupAllocation(name=gr_alloc_name, group=groupObject, project_allocation=prAllocObject, parent_group_allocation=None , hepspec=hepspec)
        gralloc.save()
        print >> log_file ,'Group Allocation  "%s" created Successfully' %gr_alloc_name
    except Exception:
        print  traceback.format_exc()
        GroupAllocation.objects.get(name=gr_alloc_name).delete()
        print >> log_file ,'ERROR addGroupAllocation error in creating Group Allocation "%s"  Error' %gr_alloc_name
        return False
    ##create the group_allocation allowed resource type
    gralloc = None
    try:
        gralloc = GroupAllocation.objects.get(name=gr_alloc_name)
        resourceTypeRecord = ResourceType.objects.get(name=resource_type)
        allowedResourceType = GroupAllocationAllowedResourceType(group_allocation=gralloc, resource_type=resourceTypeRecord)
        allowedResourceType.save()
        gralloc_metadata = GroupAllocationMetadata(attribute = 'HOSTPARTITION',value = hostpartition,group_allocation = gralloc)
        gralloc_metadata.save()
    except Exception:
        GroupAllocation.objects.get(name=gr_alloc_name).delete()
        print  traceback.format_exc()
        print >> log_file ,'ERROR addGroupAllocation Error in creating Group-Allocation %s' %gr_alloc_name     
        return False
    
def addSubGroupAllocation(subgrp_alloc_name,gr_alloc_name,experiment,hepspec,resource_type,dedicated,hostpartition,user,lsfsubgroupalias,log_file):
    if GroupAllocation.objects.filter(name__iexact=subgrp_alloc_name).exists():
        print >> log_file ,'Sub Group Allocation: "%s" Already Exist' %subgrp_alloc_name
        return True
    #get Get the group object experiment is aka group
    groupObject = None
    try:
        groupObject = Groups.objects.get(name=experiment)
    except Groups.DoesNotExist:
        print >> log_file ,'ERROR addSubGroupAllocation group  "%s" does not exists' %experiment
        return False
    ##create the group_allocation allowed resource type
    grAllocObj = None
    try:
        grAllocObj = GroupAllocation.objects.get(name=gr_alloc_name)
    except Exception:
        print >> log_file ,'ERROR addSubGroupAllocation Group-Allocation "%s" does not exist' %gr_alloc_name
        return False
    #add the subgroup allocation for LSF to cloudman
    try:
        gralloc = GroupAllocation(name=subgrp_alloc_name, group=groupObject, parent_group_allocation=grAllocObj, project_allocation=None , hepspec=hepspec)
        gralloc.save()
    except Exception:
        print  traceback.format_exc()
        print >> log_file ,'ERROR addSubGroupAllocation in creating Sub Group Allocation "%s"  Error' %subgrp_alloc_name
        return False
    ##create the group_allocation allowed resource type
    gralloc = None
    try:
        gralloc = GroupAllocation.objects.get(name=subgrp_alloc_name)
        resourceTypeRecord = ResourceType.objects.get(name=resource_type)
        allowedResourceType = GroupAllocationAllowedResourceType(group_allocation=gralloc, resource_type=resourceTypeRecord)
        allowedResourceType.save()
    except Exception:
        print  traceback.format_exc()
        GroupAllocation.objects.get(name=subgrp_alloc_name).delete()
        print >> log_file ,'ERROR addSubGroupAllocation in creating Sub Group Allocation "%s"  Error' %subgrp_alloc_name
        return False
    #Create the Sub group allocation metadata
    try:
        gralloc_metadata = GroupAllocationMetadata(attribute = 'HOSTPARTITION',value = hostpartition,group_allocation = gralloc)
        gralloc_metadata.save()
        if subgrp_alloc_name.startswith('grid_'):
            gralloc_metadata = GroupAllocationMetadata(attribute = 'EGROUP',value = subgrp_alloc_name.replace('_','-'),group_allocation = gralloc)
            gralloc_metadata.save()     
        if user !='':
            gralloc_metadata = GroupAllocationMetadata(attribute = 'USER_LIST',value = user,group_allocation = gralloc)
            gralloc_metadata.save()
        gralloc_metadata = GroupAllocationMetadata(attribute = 'LSFSUBGROUPALIAS',value = lsfsubgroupalias,group_allocation = gralloc)
        if lsfsubgroupalias !='':
            gralloc_metadata.save()
        print >> log_file ,'Sub Group Allocation  "%s" created Successfully' %subgrp_alloc_name
        return True
    except Exception:
        GroupAllocation.objects.get(name=subgrp_alloc_name).delete()
        print  traceback.format_exc()
        print >> log_file ,'ERROR addSubGroupAllocation n creating Sub Group Allocation "%s"  Error' %subgrp_alloc_name
        return False
    
#This will create mapping from unixgroup to description
def createUnixgroup_DescrDictfromFile(map_file_path):
    map_file = open(map_file_path)
    expr_descr_map = {}
    while 1:
        line = map_file.readline()
        if not line:
            break
        str_array = line.split(":")
        description = ''
        if len(str_array) == 2:
            #remove newline from the end of the string 
            description = str_array[1].rstrip('\n').rstrip().lstrip()
            unixgroup_expr_str = str_array[0]
            group_expr_array = unixgroup_expr_str.split(" ")
            group = group_expr_array[0].lower()
            expr_descr_map[group] = description
    return expr_descr_map

def getExprDescrfromLDAP(file_handle):
    cern_ldap_server = 'xldap.cern.ch'
    base = "DC=cern,DC=ch"
    ldap_filter = "(&(objectClass=group)(memberof=CN=computing-groups,OU=e-groups,OU=Workgroups,DC=cern,DC=ch))"
    try:
        l = ldap.open(cern_ldap_server)
        l.simple_bind_s("","" )        
    except ldap.LDAPError, error_message:
        print >>stdout,"Error connecting... %s " % error_message    
    timeout = 0
    scope = ldap.SCOPE_SUBTREE
    attributes = ("name" ,"description")
    result_id = l.search(base, scope, ldap_filter, attributes)
    result_set = []
    expr_dict = {}
    while 1:
        result_type, result_data = l.result(result_id, timeout)                        
        if (result_data == []):
            break
        else:
            if result_type == ldap.RES_SEARCH_ENTRY:
                result_set.append(result_data)
            if len(result_set) == 0:
                print "No Results."
    for i in range(len(result_set)):
        for entry in result_set[i]:                 
            try:            
                desc_project = entry[1]['description'][0]
                unix_group = entry[1]['name'][0]            
                str_array = desc_project.split(" - ")
                if len(str_array) == 2:
                    description = str_array[0]
                    expr_dict[unix_group] = description
                else :                
                    print >> file_handle ,"Not able to find experiment description in Static file given by Ulrich groups.txt %s"%str_array    
            except ldap.LDAPError, error_message:
                print error_message
    return expr_dict
