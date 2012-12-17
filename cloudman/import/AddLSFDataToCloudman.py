import xml.dom.minidom
import urllib2
#Line to be one vmcloudman01
from cloudman.models import *
from cloudman.commonFunctions import *
#from cloudman.cloudman.models import *
#from cloudman.cloudman.commonFunctions import *
from LsfMap import *
from importFunction import *
from settings import *
'''This script will read the LSF XML File and insert into the cloudman 
'''
expr_descr_textfile= '/root/groups.txt'
log_file_path = "/var/log/cloudman/lsf_data_export.log"
log_file_misc_path = "/var/log/cloudman/export_misc.log"
lsf_xml_url="https://j2eeps.cern.ch/service-lsfweb/xml/shares"
region_name = 'CERN Meyrin'
zone_name = 'batch CPU servers'
resource_type = 'HS06'
project_name = 'batch LSF'
log_file = open(log_file_path , 'w')
log_file_misc = open(log_file_misc_path , 'w')
try:
    url = urllib2.urlopen(lsf_xml_url)
    doc = xml.dom.minidom.parse(url)
except:
    print "Wrong URL See if the LSF XML Export URL is correct"
    exit()
##this will contain what all the groups are there in the experiment 
expr_group_dict = {}
for node in doc.getElementsByTagName("LSFSHARE"):
    lsfgroup = node.getAttribute("LSFGROUP")
    dedicated = node.getAttribute("DEDICATED")
    groupshare = node.getAttribute("GROUPSHARE")
    hostpartition = node.getAttribute("HOSTPARTITION")
    if hostpartition == 'LHCBCAF':
        hostpartition ='LHCBINTER'
        node.setAttribute("HOSTPARTITION",hostpartition)        
    ##If LSFSUBGROUP is dedicated  then dont add its allocation it will be taken care later
    if dedicated =='yes':
        continue
    try:
        if lsfgroup in lsf_group_map:
            experiment = lsf_group_map[lsfgroup]['EXPERIMENT']
            if experiment in expr_group_dict:
                expr_group_dict[experiment][lsfgroup] = float(groupshare)/float(KSI2K)      
            else:
                expr_group_dict[experiment] = { lsfgroup :  (float(groupshare)/float(KSI2K))}       
        else:
            print >>log_file_misc ,'No mapping for the LSFgroup:%s' %lsfgroup           
    except Exception:
        print  traceback.format_exc()
        continue

'''This dictionary will contain total hepspec allocated for the xperiment
taking into considiration except dedicated resources means total hepspec alloted to experiment taking into 

'''
expr_hepspec_dict = {}
for experiment in expr_group_dict:
    for group,value in expr_group_dict[experiment].items():
        if experiment in expr_hepspec_dict:
            expr_hepspec_dict[experiment] = float(expr_hepspec_dict[experiment]) + float(value)
        else:
            expr_hepspec_dict[experiment] = float(value)




##this will contain hostpartition and lsfgroup using that partition
hostpartition_dict ={}
for node in doc.getElementsByTagName("LSFSHARE"):
    lsfgroup = node.getAttribute("LSFGROUP")
    hostpartition = node.getAttribute("HOSTPARTITION")
    if hostpartition == 'LHCBCAF':
        hostpartition ='LHCBINTER'
    dedicated = node.getAttribute("DEDICATED")
    groupshare = node.getAttribute("GROUPSHARE")
    if dedicated.lower() == 'yes':
        if hostpartition not in hostpartition_dict:
            hostpartition_dict[hostpartition] = { lsfgroup:groupshare }
        else:
            hostpartition_dict[hostpartition][lsfgroup] = groupshare
        continue

##This will contain the total capacity of the partition
hostpart_capacity_dict = {}
for hostpartition in hostpartition_dict:
    groupshare_dict = hostpartition_dict[hostpartition]
    total_share = 0
    for group,share in groupshare_dict.items():
        total_share += int(share)
    hostpart_capacity_dict[hostpartition] = total_share

expr_descr_ldap_dict = getExprDescrfromLDAP(log_file_misc)
expr_descr_file_dict = createUnixgroup_DescrDictfromFile(expr_descr_textfile)
for node in doc.getElementsByTagName("LSFSHARE"):
    lsfgroup = node.getAttribute("LSFGROUP")
    groupshare = node.getAttribute("GROUPSHARE")
    dedicated = node.getAttribute("DEDICATED")
    hostpartition = node.getAttribute("HOSTPARTITION")
    lsfsubgroup = node.getAttribute("LSFSUBGROUP")
    lsfsubgroupalias = node.getAttribute("LSFSUBGROUPALIAS")
    subgroupfraction = node.getAttribute("SUBGROUPFRACTION")
    user = node.getAttribute("USERS")
    header_line = '\nAdding LSF data for LSFGROUP="%s" GROUPSHARE="%s" DEDICATED="%s" HOSTPARTITION="%s" LSFSUBGROUP="%s" LSFSUBGROUPALIAS="%s" SUBGROUPFRACTION="%s" USERS="%s"' %(lsfgroup,groupshare,dedicated,hostpartition,lsfsubgroup,lsfsubgroupalias,subgroupfraction,user)
    print >>log_file ,header_line   
    try:
        if lsfgroup in lsf_group_map:
            experiment = lsf_group_map[lsfgroup]['EXPERIMENT']
            unix_group = lsf_group_map[lsfgroup]['UNIXGROUP']
            egroup_name = getEgroupName(unix_group)
        else:
            msg = 'No mapping of LSFGRoup:' + lsfgroup + 'To Experiment in lsfgroup_expr_map define in file LSFGroup_Expr_Map.py'
            print >> log_file , msg
            continue
        expr_description=''
        if unix_group in expr_descr_file_dict:
            expr_description = expr_descr_file_dict[unix_group]
        elif unix_group in expr_descr_file_dict:
            expr_description = expr_descr_file_dict[unix_group]

        tp_alloc_name = experiment.upper() 
        pr_alloc_name  = experiment.upper() + ' batch public' 
        gr_alloc_name = lsfgroup
        subgrp_alloc_name = lsfsubgroup
        group_exist = addNewGroup(experiment,expr_description,egroup_name,log_file) 
        hepspec_top = expr_hepspec_dict[experiment]
        if lsfgroup in lsf_dedicated_group_hepspec:
            for key,value  in lsf_dedicated_group_hepspec[lsfgroup].items():
                hepspec_top +=value
        ##experiment is the name of the group
        if dedicated =='yes':
            pr_alloc_name = experiment.upper() + ' public '+hostpartition
            hepspec_project = getPartitionHepSpec(lsf_dedicated_group_hepspec,hostpartition) 
            hepspec_group =( float(groupshare)/float(hostpart_capacity_dict[hostpartition]) ) * hepspec_project         
        else:
            hepspec_project = expr_hepspec_dict[experiment]
            hepspec_group = float(groupshare) / float(KSI2K)  

        subgrp_hepspec = float(hepspec_group) * float(subgroupfraction)/100 
        
        top_alloc_created = addTopLevelAllocation(tp_alloc_name,experiment,hepspec_top,region_name,zone_name,resource_type,log_file)                
        project_alloc_created = addProjectAllocation(pr_alloc_name,tp_alloc_name,project_name,experiment,resource_type,hepspec_project,dedicated,hostpartition,log_file)
        group_alloc_created = addGroupAllocation(gr_alloc_name,experiment,pr_alloc_name,hepspec_group,resource_type,hostpartition,log_file)
        subgroup_alloc_created = addSubGroupAllocation(subgrp_alloc_name,gr_alloc_name,experiment,subgrp_hepspec,resource_type,dedicated,hostpartition,user,lsfsubgroupalias,log_file)
    except Exception:
        print  traceback.format_exc()   

