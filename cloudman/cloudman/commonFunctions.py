from models import ChangeLog
from models import ZoneAllowedResourceType,GroupAllocation,ProjectAllocation
import sys, traceback
from django.db.models import Q
from django.conf import settings
from settings import  *
import ldap
import ldap.resiter
from ldap.controls import SimplePagedResultsControl
import ldap.modlist as modlist
from ldapSearch import *
from sys import *
from logQueries import *
import re


 ##This will add the Change Log
def addUpdateLog(request,name,objectId,comment,olddict,newdict,category,status):
    try:
        changedata = getChangeInfo(olddict,newdict)
        sys_comment = '<p class=currdata>%s</p><p class=olddata>%s</p>'%(changedata['new'],changedata['old']) 
        user = request.META.get('ADFS_FULLNAME','')     
        log = ChangeLog(category=category,object_id=objectId,name=name,operation='update',comment=comment,sys_comment=sys_comment,user=user,status=status)
        log.save()
        return True
    except Exception :
        print traceback.format_exc()
        return False
   
def addEgroupLog(request,egroup,category,operation,comment,status):
    try:
        if category =='egroup':
            if operation == 'update':
                sys_comment = "<p class=currdata>'%s'</p>"%comment
            elif operation == 'deleteCERN':
                sys_comment = '<p class=olddata>Egroup %s Deleted in CERN Egroup</p>'%egroup
            elif operation =='deleteCLOUDMAN':
                sys_comment = '<p class=olddata>Egroup %s Deleted in CLOUDMAN</p>'%egroup
            elif operation == 'emptyEgroup':
                sys_comment = "<p class=currdata>'%s'</p>"%comment
        user='CLOUDMAN CRON SCRIPT'
        if request :
            user = request.META.get('ADFS_FULLNAME','')
        log = ChangeLog(category=category,object_id=1,user=user,name=egroup,operation=operation,comment=comment,sys_comment=sys_comment,status=status)
        log.save()
        return True
    except Exception:
        print traceback.format_exc()
        return False
        

def addLog(request,name,comment,oldCategObj,newCategObj,category,operation,status):
    try:        
        object_id = oldCategObj.id
        if category =='group':
            if operation == 'add':
                sys_comment = "<p class=currdata>Added Group '%s'</p>"%oldCategObj.name
            elif operation == 'delete':
                sys_comment = '<p class=olddata>%s</p>'%formatObjectInfo(getGroupInfo(oldCategObj))
        elif category == 'resourcetype':
            if operation == 'add':
                sys_comment = "<p class=currdata>Added ResourceType '%s'</p>" %oldCategObj.name
            elif operation == 'delete':
                sys_comment = '<p class=olddata>%s</p>'%formatObjectInfo(getResourceTypeInfo(oldCategObj))
        elif category =='region':
            if operation == 'add':
                sys_comment = "<p class=currdata>Added Region '%s'</p>"%oldCategObj.name
            elif operation == 'delete':
                sys_comment = '<p class=olddata>%s</p>'%formatObjectInfo(getRegionInfo(oldCategObj))
        elif category =='zone':
            if operation == 'add':
                sys_comment = "<p class=currdata>Added Zone '%s'</p>"%oldCategObj.name
            elif operation == 'delete':
                sys_comment = '<p class=olddata>%s</p>'%formatObjectInfo(getZoneInfo(oldCategObj))
        elif category =='project':
            if operation == 'add':
                sys_comment = "<p class=currdata>Added Project '%s'</p>" %oldCategObj.name
            elif operation == 'delete':
                sys_comment = '<p class=olddata>%s</p>'%formatObjectInfo(getProjectInfo(oldCategObj))
        elif category =='topallocation':
            if operation == 'add':
                sys_comment = "<p class=currdata>Added TopLevelAllocation '%s'</p>" %oldCategObj.name
            elif operation == 'delete':
                sys_comment = '<p class=olddata>%s</p>'%formatObjectInfo(getTopAllocationInfo(oldCategObj))
        elif category =='projectallocation':
            if operation == 'add':
                sys_comment = "<p class=currdata>Added ProjectAllocation '%s'</p>" %oldCategObj.name
            elif operation == 'delete':
                sys_comment = '<p class=olddata>%s</p>'%formatObjectInfo(getProjectAllocationInfo(oldCategObj))
        elif category =='groupallocation':
            if operation == 'add':
                sys_comment = "<p class=currdata>Added GroupAllocation '%s'</p>" %oldCategObj.name
            elif operation == 'delete':
                sys_comment = '<p class=olddata>%s</p>'%formatObjectInfo(getGroupAllocationInfo(oldCategObj))

        user = request.META.get('ADFS_FULLNAME','')     
        log = ChangeLog(category=category,object_id=object_id,name=name,operation=operation,comment=comment,sys_comment=sys_comment,user=user,status=status)
        log.save()
        return True
    except Exception :
        print traceback.format_exc()
        return False
##This will return the Change log             

def getLog(category,name,object_id,operation):
    if  object_id is None:        
        qset = Q(name__iexact=name)
    else:
        qset = Q(object_id=object_id)
    qsetcateg = Q(category__iexact=category)
    #if the operation is add delete update then generate the Q objects
    if operation in ['add','delete','update']: 
        qsetopr = Q(operation__iexact=operation)
    else:
        qsetopr =Q()
    changeLogList = ChangeLog.objects.filter(qsetcateg & qset & qsetopr).order_by('-datetime')
    return changeLogList




##This will get the user list from ldap
def getUserListfromEgroup(egroup):
    ldap_filter = '(&(objectClass=user)(memberof=CN=%s,OU=e-groups,OU=Workgroups,DC=cern,DC=ch))' %egroup
    attributes = ["name"]
    timeout =0
    pageSize =100
    result_set = pagedLDAPSearch(LDAP_BASE, ldap_filter, attributes, timeout, pageSize, LDAP_SERVER)
    user_list = ''
    for entry in result_set:                 
        try:            
            user = entry[1]['name'][0]
            user_list += user + ' '     
        except ldap.LDAPError, error_message:
            print error_message

    return user_list.strip()

def checkAttributeValues(hepspec, memory, storage, bandwidth):
    errorMsg = ''
    if hepspec == '':
       hepspec = -1
    if memory == '':
       memory = -1
    if storage == '':
       storage = -1
    if bandwidth == '':
       bandwidth = -1

    try:
       hepspec = float(hepspec)
       memory = float(memory)
       storage = float(storage)
       bandwidth = float(bandwidth)
    except Exception, err:
       errorMsg = "Hepspec, memory, storage and bandwidth only takes number values, reason : %s" % str(err)
       return errorMsg

    if ( (hepspec <= 0) and (storage <= 0) ):
       errorMsg = "One or both Hepspec and Storage value, if entered, should have a positive float value (greater than 0). "

    if hepspec < -1:
       errorMsg = errorMsg + "One or both Hepspec and Storage value, if entered, should have a positive float value (greater than 0). "

    if storage < -1:
       errorMsg = errorMsg + "One or both Hepspec and Storage value, if entered, should have a positive float value (greater than 0). "

    if memory < -1:
       errorMsg = errorMsg + "Memory value should be blank or greater than or equal to 0. "

    if bandwidth < -1:
       errorMsg = errorMsg + "Bandwidth value should be blank or greater than or equal to 0. "

    return errorMsg


#This will give the Allowed depth of Group allocation
def groupAllocLevel(prjAllocObj,parentGrpAllocObj):
    try:
        level = 0
        if prjAllocObj :            
            try:
                prjMetaData = ProjectMetadata.objects.get(project = prjAllocObj.project,attribute='SUBGROUPLEVEL')
                level = int(prjMetaData.value)
            except ProjectMetadata.DoesNotExist:
                level=GROUP_ALLOC_DEPTH
        else:
            level = int(groupAllocLevel(parentGrpAllocObj.project_allocation, parentGrpAllocObj.parent_group_allocation )) -1
    except Exception:
        printStackTrace()
        pass
    return level




#get the ksi2k from hepspec if it is not none
def getKSI2K(hepspec):
    if hepspec:
        return hepspec * float(KSI2K)
    else:
        return hepspec

def getPercent(value,total):
    if value and total:
        return float(value)*100/float(total)
    else:
        return None
    

def scaleTopAllocationHepSpec(tpAllocName,scalefactor,scale=True):
    try:
        prjAllocObjList = ProjectAllocation.objects.filter(top_level_allocation__name = tpAllocName)
        for prjAlloc in prjAllocObjList:
            prjAlloc.hepspec = float(prjAlloc.hepspec)*scalefactor
            prjAlloc.save()
            scaleGroupAllocationHepSpec(prjAlloc.name,scalefactor,scale=True)
    except Exception:
        printStackTrace()
    return


def scaleGroupAllocationHepSpec(prjAllocName,scalefactor,scale=True):
    try:
        grpAllocObjList = GroupAllocation.objects.filter(project_allocation__name = prjAllocName)
        for grpAlloc in grpAllocObjList:
            grpAlloc.hepspec = float(grpAlloc.hepspec)*scalefactor
            grpAlloc.save()
            scaleSubGroupAllocationHepSpec(grpAlloc.name,scalefactor,scale=True)
    except Exception:
        printStackTrace()
    return

def scaleSubGroupAllocationHepSpec(grpAllocName,scalefactor,scale=True):
    try:
        grpAllocObjList = GroupAllocation.objects.filter(parent_group_allocation__name = grpAllocName)
        for grpAlloc in grpAllocObjList:
            grpAlloc.hepspec = float(grpAlloc.hepspec)*scalefactor
            grpAlloc.save()
            scaleSubGroupAllocationHepSpec(grpAlloc.name,scalefactor,scale=True)
    except Exception:
        printStackTrace()
    return


def scaleTopAllocationStorage(tpAllocName,scalefactor,scale=True):
    try:
        prjAllocObjList = ProjectAllocation.objects.filter(top_level_allocation__name = tpAllocName)
        for prjAlloc in prjAllocObjList:
            prjAlloc.storage = float(prjAlloc.storage)*scalefactor
            prjAlloc.save()
            scaleGroupAllocationStorage(prjAlloc.name,scalefactor,scale=True)
    except Exception:
        printStackTrace()
    return


def scaleGroupAllocationStorage(prjAllocName,scalefactor,scale=True):
    try:
        grpAllocObjList = GroupAllocation.objects.filter(project_allocation__name = prjAllocName)
        for grpAlloc in grpAllocObjList:
            grpAlloc.storage = float(grpAlloc.storage)*scalefactor
            grpAlloc.save()
            scaleSubGroupAllocationHepSpec(grpAlloc.name,scalefactor,scale=True)
    except Exception:
        printStackTrace()
    return

def scaleSubGroupAllocationStorage(grpAllocName,scalefactor,scale=True):
    try:
        grpAllocObjList = GroupAllocation.objects.filter(parent_group_allocation__name = grpAllocName)
        for grpAlloc in grpAllocObjList:
            grpAlloc.storage = float(grpAlloc.storage)*scalefactor
            grpAlloc.save()
            scaleSubGroupAllocationHepSpec(grpAlloc.name,scalefactor,scale=True)
    except Exception:
        printStackTrace()
    return

##This will check if empty string is present in the list of string
def checkForEmptyStrInList(string_list):
    for str in string_list:
        if  not str:
            return True
    return False

## This will check for Duplicate String in the list of String First convert list to uppercase after that remove the duplicate and compare
##the length of the list with the length of the original list
# return true if duplicate is found else false
def checkForDuplicateStrInList(string_list):
    new_list = [x.upper() for x in string_list];
    if len(new_list) != len( set(new_list) ):
       return True
    return False

##This will check if two lists are equal means that they contain same element.
##Return True if both the list are equal else return False
def checkForStringEquality(list1,list2):
   new_list = set(list1) & set(list2)
   if len(new_list) == len(list1):
      return True 
   return False  


##This will create dictionary from two list First argument will be key second will be the value

def createDictFromList(list1,list2):
    #list1 is the attribute name so remove all whitespaces from the attribute name
    #list2 contains the attribute value so replace multiple spaces with single space
    pattern = re.compile(r'\s+')
    newlist1 =([pattern.sub('', x) for x in list1])#Remove the whitespaces from the list element
    newlist2 =([pattern.sub(' ', x).strip() for x in list2])#Remove the whitespaces from the list element
    attr_dict = dict(zip(newlist1,newlist2))#Create dict from the list
    return   attr_dict

##Check for dictionary equality it will match for the key-value pairs
#Return True if both the dictionary matches Else false it will check for key-Value pairs
def checkForDictionaryEquality(dicta,dictb):
    for key,value in dicta.iteritems():
        if key in dictb.keys():
               if value == dictb[key]:
                     del dictb[key]
               else:
                     return False
        else:
             return False
    if not dictb:
        return True
    else:
        return False

##Return 1 if any of oldVal or newval is None or oldVal is 0

def getScaleFactor(newVal,oldVal):
    try:
        return float(newVal)/float(oldVal)
    except Exception:
        return 1

    
##This will set the member of Object to '' when it is None the member list is provided in objMemberList
def formatUndefinedInObj(objList , objMemberList):
    tmp_list =[]
    for obj in objList:
        for member in objMemberList:
            try:
                if obj.__dict__[member]  == None:
                    obj. __dict__[member] = ''
            except Exception:
                printStackTrace()
        tmp_list.append(obj)
    return tmp_list

#This is used for printing the generated SQL Query
def printQuery(querylist):
    for item in querylist:
        print item
    
    
    

