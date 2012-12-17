import pprint
import sys
import ldap
import ldap.resiter
import time
from ldap.controls import SimplePagedResultsControl
import ldap.modlist as modlist
from xml.dom.minidom import Document
#import xml.dom.minidom
#import urllib2
#import pprint
#import ldap.resiter
#import time
#from ldap.controls import SimplePagedResultsControl
#import ldap.modlist as modlist
#import re


def getExperUnixgroupAsXML(xml_file , log_file):
    cern_ldap_server = 'xldap.cern.ch'
    base = "DC=cern,DC=ch"
    ldap_filter = "(&(objectClass=group)(memberof=CN=computing-groups,OU=e-groups,OU=Workgroups,DC=cern,DC=ch))"
    try:
        l = ldap.open(cern_ldap_server)
        l.simple_bind_s("","" )
        print "Successfully connected..."
    except ldap.LDAPError, error_message:
        print "Error connecting... %s " % error_message    
    timeout = 0
    scope = ldap.SCOPE_SUBTREE
    attributes = ("name" ,"description")
    result_id = l.search(base, scope, ldap_filter, attributes)
    result_set = []
    while 1:
        result_type, result_data = l.result(result_id, timeout)                        
        if (result_data == []):
            break
        else:
            if result_type == ldap.RES_SEARCH_ENTRY:
                result_set.append(result_data)
                doc = Document()
                exp = doc.createElement("EXPERIMENT_LIST")
                file_handle = open(log_file, 'w')
                if len(result_set) == 0:
                    print "No Results."
                for i in range(len(result_set)):
                    for entry in result_set[i]:                 
                        try:            
                            desc_project = entry[1]['description'][0]
                            unix_group = entry[1]['name'][0]            
                            str_array = desc_project.split(" - ")
                            if len(str_array) == 2:
                                experiment = str_array[1].lower()
                                description = str_array[0]
                                node = doc.createElement("EXPERIMENT")
                                node.setAttribute("NAME",experiment)
                                node.setAttribute("DESCRIPTION",description)
                                node.setAttribute("UNIX_GROUP",unix_group)
                                exp.appendChild(node)
                            else :                
                                print  >> file_handle , "description:" + desc_project
                                print  >> file_handle , "name:" + unix_group
                                print >> file_handle ,"                "    
                        except ldap.LDAPError, error_message:
                                print error_message
    doc.appendChild(exp)         
    file = open(xml_file,'w')
    print >> file ,doc.toprettyxml(indent="  ")
    
def createDictFromExperimentUnixGroupFile(map_file_path):
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
        experiment = group_expr_array[1].lower()
        if experiment in expr_descr_map:
            pass
        else :
            expr_descr_map[experiment]={}
        expr_descr_map[experiment][group] = description    
    return expr_descr_map    

#This will create dictionary from LDAP unixgroup and description
def createUnixgroup_DescrDictfromXML(map_file_path):
    try:
        xml_file_handle = open(map_file_path , 'r')
        xml_data = xml_file_handle.read()
        xml_file_handle.close()
    except:
        print "Wrong URL See if the EXPERIMENT Unix group XML Export URL is correct"
        exit()
    dict ={}
    dom = xml.dom.minidom.parseString(xml_data)
    for node in dom.getElementsByTagName("EXPERIMENT"):
        description = node.getAttribute("DESCRIPTION").rstrip().lstrip()
        unix_group = node.getAttribute("UNIX_GROUP")
        dict[unix_group] = description
    return dict



##This will create the dictionary from the XML Data containing Experiment_name,description and Unix_group
def createDictFromExperimentUnixGroupXML(map_file_path):
    try:
        xml_file_handle = open(map_file_path , 'r')
        xml_data = xml_file_handle.read()
        xml_file_handle.close()
    except:
        print "Wrong URL See if the EXPERIMENT Unix group XML Export URL is correct"
        exit()
    dict ={}
    dom = xml.dom.minidom.parseString(xml_data)
    for node in dom.getElementsByTagName("EXPERIMENT"):
        description = node.getAttribute("DESCRIPTION").rstrip().lstrip()
        experiment = node.getAttribute("NAME") #name of the experiment is same as the group name
        unix_group = node.getAttribute("UNIX_GROUP")
        if experiment in dict:
            pass
        else :
            dict[experiment] = {}
        
        dict[experiment][unix_group] = description
    return dict
        
###This will check if the two dict have same experiment and also the corresponding unix_group is same
def checkExprUnixGroupConsistencyAndMakeNewDict(dict_xml ,dict_file,log_file):
    dict = {}
    for experiment in dict_xml.iterkeys():
        try:
            group_descr_dict = dict_file[experiment]
            if set(dict_xml[experiment].keys()) == set(dict_file[experiment].keys()):
                if len(dict_xml[experiment]) > 1:
                    msg = 'Experiment "%s" has more than one unix_groups' %experiment
                    print >> log_file , msg    
                for unix_group_key in dict_xml[experiment]:                 
                    if experiment not in dict:
                        dict[experiment] = {}
                    if    dict_file[experiment][unix_group_key] == '':
                        dict[experiment][unix_group_key] = dict_xml[experiment][unix_group_key]
                    else:
                        dict[experiment][unix_group_key] = dict_file[experiment][unix_group_key]
            else:
                msg = 'Experiment "%s" unix_groups differ between the two maps' %experiment    
                print >> log_file , msg
            del dict_file[experiment] ###delete the key from dict_xml file if the key exist
        except KeyError:
            print experiment
            dict[experiment] = dict_xml[experiment]
            pass    
    ##here add all the ramining remaining keys to the dictionary
    for experiment in dict_file.keys():
        dict[experiment] = dict_file[experiment]    
    return dict


###This will contain the map between the lSF group_name and the corresponding experiment
lsfgroup_expr_map = {
        "u_ALICE":"ALICE",
        "u_ATLAS":"ATLAS",
        "u_ATLASCAT":"ATLASCAT",
        "u_ATLASCAF":"ATLASCAF",
        "u_CMS":"CMS",
        "u_LHCB":"LHCB", # renamed from LHCb to LHCB
        "u_NTOF":"PS",
        "u_NA49":"NA49",
        "u_NA61":"NA61",
        "u_DELPHI":"DELPHI",
        "u_ALEPH":"ALEPH",
        "u_L3":"L3",
        "u_OPAL":"OPAL",
        "u_ITU":"ITU",
        "u_NA38NA50":"NA60", #the name of the experiment is NA38NA50 or NA60
        "u_C4":"C4",
        "u_ITDC":"ITDC",
        "u_PARC":"PARC",
        "u_CMSCOMM":"CMSCOMM",
        "u_CMSPHYS":"CMSPHYS",
        "u_CMSALCA":"CMSALCA",
        "u_LHCBT3":"LHCBT3",
        "u_FLUKARP":"FLUKA", 
        "u_TOTEM":"TOTEM",
        "u_AMS":"RE1",
        "u_CAST":"CAST",
        "u_CMST3":"CMS",
        "u_COMPASS":"NA58",
        "u_DIRAC":"PS212",
        "u_GEANT4":"PH-SFT",
        "u_HARP":"PS214",
        "u_HARPD":"PS214",
        "u_ILC":"CTF3",
        "u_ISOLDE":"ISOLDE",                    
        "u_LHCF":"LHCF",                    
        "u_NA45":"NA45/2",                    
        "u_NA48":"NA48/2",
        "u_NOMAD":"WA96",
        "u_NTOF":"PS",
        "u_SLDIV":"BE",
        "u_THEORY":"PH-TH",
        "u_DTEAM":"IT",
        "u_UNOSAT":"IT",
        "u_GEAR":"IT",
        "u_C3":"IT",
        "u_OPERA":"CNGS1"
                 }

lsf_group_expr_map_drop = {
#    "u_ATLCASTORACL":"",
#    "u_AMSP":"",
#    "u_ATLDEDICATED":"",
#    "u_LHCBCAF":"",
#    "u_SFT":""
}

def createDictFromExperimentUnixGroupXML():
    expr_group_xml_file = "/var/log/cloudman/expr_unix.xml"
    try:
        xml_file_handle = open(expr_group_xml_file , 'r')
        xml_data = xml_file_handle.read()
        xml_file_handle.close()
    except:
        print "Wrong URL See if the EXPERIMENT Unix group XML Export URL is correct"
        exit()
    dict ={}
    dom = xml.dom.minidom.parseString(xml_data)
    for node in dom.getElementsByTagName("EXPERIMENT"):
        description = node.getAttribute("DESCRIPTION")
        experiment = node.getAttribute("NAME") #name of the experiment is same as the group name
        unix_group = node.getAttribute("UNIX_GROUP")
        admin_egroup = unix_group + "-admins"
        dict[experiment] = {'DESCRIPTION':description,'EGROUP':admin_egroup}
    return dict





#def addExprUnixGroup(request):
expr_group_xml_file = "/var/log/cloudman/expr_unix.xml"
success_log = "/var/log/cloudman/group_added"
error_log = "/var/log/cloudman/group_not_added"
duplicate_group_log_file = "/var/log/"
try:
    xml_file_handle = open(expr_group_xml_file , 'r')
    xml_data = xml_file_handle.read()
    xml_file_handle.close()
except:
    print "Wrong URL See if the EXPERIMENT Unix group XML Export URL is correct"
    exit()

#doc = xml.dom.minidom.parse(xml_data)
dom = xml.dom.minidom.parseString(xml_data)
for node in dom.getElementsByTagName("EXPERIMENT"):
    description = node.getAttribute("DESCRIPTION")
    experiment = node.getAttribute("NAME") #name of the experiment is same as the group name
    group_name = experiment + "_Batch"
    unix_group = node.getAttribute("UNIX_GROUP")
    admin_egroup = unix_group + "-admins"
    addNewGroup(group_name,description,admin_egroup,error_log,success_log)
    
    
    
    