import traceback
from models import ZoneAllowedResourceType
from models import ProjectMetadata
from models import TopLevelAllocationAllowedResourceType
from models import TopLevelAllocationByZone
from models import ProjectAllocationAllowedResourceType
from models import ProjectAllocationMetadata
from models import GroupAllocationAllowedResourceType
from models import GroupAllocationMetadata
from models import Region
from models import Project
from models import ChangeLog
from models import Groups
from models import Egroups
from django.db.models import Q
from django.template import RequestContext, loader, Context
from django.shortcuts import render_to_response
import types

def getGroupAllocationInfo(grAllocObj):
    value_dict = {}
    try:
        if  grAllocObj is not None:
            grpAllocName = grAllocObj.name
            groupName = grAllocObj.group.name
            prjAllocName = None
            parentGrpAllocName = None    
            if grAllocObj.project_allocation != None:
                prjAllocName = grAllocObj.project_allocation.name
            elif grAllocObj.parent_group_allocation != None:
                parentGrpAllocName = grAllocObj.parent_group_allocation.name
            hepspec = grAllocObj.hepspec
            memory = grAllocObj.memory
            storage = grAllocObj.storage
            bandwidth = grAllocObj.bandwidth            
            grpAllocAllowedRT = getDictFromQuerySet(GroupAllocationAllowedResourceType.objects.filter(group_allocation__name=grpAllocName).values_list('resource_type__name', flat=True))
            grpAllocMetaDataList = getDictFromQuerySet(GroupAllocationMetadata.objects.filter(group_allocation__name=grpAllocName).values('attribute','value'))
            value_dict = { 'Name':grpAllocName,'Group':groupName,'ProjectAllocation':prjAllocName,'ParentGroupAllocation':parentGrpAllocName,
                         'HepSpec':hepspec,'Memory':memory,'Storage':storage,'Bandwidth':bandwidth,'ResourceType':grpAllocAllowedRT,
                         'MetaData': grpAllocMetaDataList }
    except Exception:
        printStackTrace()     
    return value_dict

def getProjectAllocationInfo(prjAllocObj):
    value_dict = {}
    try:
        if  prjAllocObj is not None:
            prjAllocName = prjAllocObj.name
            tpAllocName = prjAllocObj.top_level_allocation.name
            projectName = prjAllocObj.project.name
            groupName = prjAllocObj.group.name
            hepspec = prjAllocObj.hepspec
            memory = prjAllocObj.memory
            storage = prjAllocObj.storage
            bandwidth = prjAllocObj.bandwidth            
            prjAllocAllowedRT = getDictFromQuerySet(ProjectAllocationAllowedResourceType.objects.filter(project_allocation__name=prjAllocName).values_list('resource_type__name', flat=True))
            prjAllocMetaDataList = getDictFromQuerySet(ProjectAllocationMetadata.objects.filter(project__name = projectName,project_allocation__name=prjAllocName).values('attribute','value'))
            value_dict = { 'Name':prjAllocName,'TopLevelAllocation':tpAllocName,'Project':projectName,'Group':groupName,
                         'HepSpec':hepspec,'Memory':memory,'Storage':storage,'Bandwidth':bandwidth,'ResourceType':prjAllocAllowedRT,
                         'MetaData': prjAllocMetaDataList }
    except Exception:
        printStackTrace()     
    return value_dict

def getTopAllocationInfo(tpAllocObj):
    value_dict = {}
    try:
        if  tpAllocObj is not None:
            tpAllocName = tpAllocObj.name
            groupName = tpAllocObj.group.name
            hepspec = tpAllocObj.hepspec
            memory = tpAllocObj.memory
            storage = tpAllocObj.storage
            bandwidth = tpAllocObj.bandwidth
            tpAllocAllowedRT = getDictFromQuerySet(TopLevelAllocationAllowedResourceType.objects.filter(top_level_allocation__name=tpAllocName).values('resource_type__name','zone__name' ))            
            zoneShareList = getDictFromQuerySet(TopLevelAllocationByZone.objects.filter(top_level_allocation__name__iexact = tpAllocName).values('zone__name','hepspec','memory','storage','bandwidth','zone__region__name'))
            value_dict = { 'Name':tpAllocName,'Group':groupName,'HepSpec':hepspec,'Memory':memory,
                         'Storage':storage,'Bandwidth':bandwidth,'ResourceType':tpAllocAllowedRT,'ZoneShare':zoneShareList  }
    except Exception:
        printStackTrace()     
    return value_dict
    
def getProjectInfo(projObj):
    value_dict = {}
    try:
        if projObj is not None:
            projName = projObj.name
            description = projObj.description
            admin_group = projObj.admin_group
            prjMetaDataList = getDictFromQuerySet(ProjectMetadata.objects.filter(project__name = projName).values('attribute','value'))
            value_dict ={'Name':projName,'Description':description,'AdminGroup':admin_group,'MetaData':prjMetaDataList}
    except Exception:
        printStackTrace() 
    return value_dict

def getZoneInfo(zoneObj):
    value_dict = {}
    try:
        if  zoneObj is not None:
            zoneName = zoneObj.name
            description = zoneObj.description
            hepspecs = zoneObj.hepspecs
            memory = zoneObj.memory
            storage = zoneObj.storage
            bandwidth = zoneObj.bandwidth
            hepspec_overcommit = zoneObj.hepspec_overcommit
            memory_overcommit = zoneObj.memory_overcommit
            region_name = zoneObj.region.name
            zoneAllowedRT = getDictFromQuerySet(ZoneAllowedResourceType.objects.filter(zone__name = zoneName).values_list('resource_type__name', flat=True))
            value_dict = { 'Name':zoneName,'Description':description,'HepSpec':hepspecs,'Memory':memory,
                         'Storage':storage,'Bandwidth':bandwidth,'HepSpecOverCommit':hepspec_overcommit,
                         'MemoryOverCommit':memory_overcommit,'Region':region_name,'ResourceType':zoneAllowedRT  }
    except Exception:
        printStackTrace() 
    return value_dict

def getRegionInfo(regionObj):
    value_dict = {}
    try:
        if regionObj is not None:
            name = regionObj.name
            description = regionObj.description
            admin_group = regionObj.admin_group
            value_dict ={'Name':name,'Description':description,'AdminGroup':admin_group}
    except Exception:
        printStackTrace() 
    return value_dict

def getResourceTypeInfo(rtObj):
    value_dict = {}
    try:
        if rtObj is not None:
            name = rtObj.name
            resource_class = rtObj.resource_class
            hepspecs = rtObj.hepspecs
            memory = rtObj.memory
            storage = rtObj.storage
            bandwidth = rtObj.bandwidth
            value_dict ={'Name':name,'ResourceClass':resource_class,'HepSpec':hepspecs,'Memory':memory,'Storage':storage,'Bandwidth':bandwidth}
    except Exception:
        printStackTrace() 
    return value_dict

def getGroupInfo(grpObj):
    value_dict = {}
    try:
        if grpObj is not None:
            name = grpObj.name
            description = grpObj.description
            admin_group = grpObj.admin_group
            value_dict ={'Name':name,'Description':description,'AdminGroup':admin_group}
    except Exception:
        printStackTrace() 
    return value_dict

#This dictionary will get the changes
def getChangeInfo(oldDict,newDict):
    inOld= {}
    inNew= {}
    keyList = []
    keyList.extend(list(oldDict.keys()))
    keyList.extend(list(newDict.keys()))
    for key in keyList:
        if key in oldDict and key in newDict:
            oldvalue = oldDict[key]
            newvalue = newDict[key]
            if isinstance(oldvalue ,types.ListType):
                #check if list elements are dictionary
                if len(oldvalue) >=1 and isinstance(oldvalue[0],types.DictType):
                    diff_dict = getDiffFromListDict(oldvalue,newvalue)
                    if len(diff_dict['old'])>=1:
                        inOld[key] = diff_dict['old']
                    if len(diff_dict['new'])>=1:
                        inNew[key] = diff_dict['new']
                elif len(oldvalue) >=1 and  set(oldvalue) != set(newvalue):
                    inOld[key] = oldvalue
                    inNew[key] = newvalue 
            elif isinstance( oldvalue,types.FloatType) or isinstance( oldvalue,types.StringType) or isinstance( oldvalue,types.UnicodeType) or isinstance( oldvalue,types.NoneType):
                if oldvalue != newvalue:
                    inOld[key] = oldvalue
                    inNew[key] = newvalue 
        elif key in oldDict:
            inOld[key] = oldDict[key]
        elif key in newDict:
            inNew[key] = newDict[key]
    return {'old':formatObjectInfo(inOld),'new':formatObjectInfo(inNew)}

## This will get the differnece between two list when list elements are Dictionary
##here i create list by appending attributename attributevalue with &&
def getDiffFromListDict(oldList,newList):
    inNew = [] 
    inOld = []
    oldListStr=[]
    for item in oldList:
        tmp_str=''
        for key,value in item.items():
            tmp_str += '%s&&%s&&' %(key,value)
        oldListStr.append(tmp_str[:-2])#Remove the last two character
    newListStr=[]    
    for item in newList:
        tmp_str =''
        for key,value in item.items():
            tmp_str += '%s&&%s&&' %(key,value)
        newListStr.append(tmp_str[:-2])
    ##check if attrname and attrvalue are only in newList
    for item in newListStr:
        if item not in oldListStr:
            item_array=item.split('&&')
            inNew.append({item_array[0]:item_array[1],item_array[2]:item_array[3]})        
    ##check if attrname and attrvalue are only in oldList
    for item in oldListStr:
        if item not in newListStr:
            item_array=item.split('&&')
            inOld.append({item_array[0]:item_array[1],item_array[2]:item_array[3]})
    return {'old':inOld,'new':inNew}
            
#here we can format to display it nicely
def formatObjectInfo(value_dict):
    msg =''
    try:
        if value_dict is not None:
            for name,value in value_dict.items():
                msg += "%s <b>%s</b> " %(name,value)
#                if isinstance(value,types.UnicodeType):
#                    print name ,value
#                elif isinstance(value,types.StringType):
#                    print name ,value
#                elif isinstance( value,types.FloatType):
#                    print name , value
#                elif isinstance(value,types.NoneType):
#                    print name ,value
#                elif isinstance(value,types.ListType):
#                    print name ,value
    except Exception:
        printStackTrace()     
    return msg

#this will make dict form QuerySetObj
def getDictFromQuerySet(qSetObj):
    return [item for item in qSetObj]

def formatList(itemList):
    newString = '[]'
    if itemList is not None:
        newString = ",".join(itemList)
    return '[%s]'%newString

def  printStackTrace():
    print traceback.format_exc()
#This is used for Showing the Log on the Homepage only 10 Logs will be shown.    
def logpanel(request):
    changeLogList = ChangeLog.objects.order_by('-datetime')[:10]
    return render_to_response('log/logpanel.html',locals(),context_instance=RequestContext(request))
 
#This is used for Showing The Issues in the Cloudman
def issuepanel(request):
    issueList =[]
    qsetStatus = Q(status=False)
    qsetEmpty = Q(empty=True)
    egroupList = Egroups.objects.filter(qsetStatus|qsetEmpty).values_list('name',flat=True)
    for egroup in egroupList:
        grpList = Groups.objects.filter(admin_group=egroup).values_list('name',flat=True)
        prjList = Project.objects.filter(admin_group=egroup).values_list('name',flat=True)
        regionList = Region.objects.filter(admin_group=egroup).values_list('name',flat=True)
        #changeLog = ChangeLog.objects.filter(category='egroup',name=egroup,operation='delete').order_by('-datetime')
        changeLog = ChangeLog.objects.filter(category='egroup',name=egroup).order_by('-datetime')
        print  changeLog
        description = ''        
        date = ''        
        if changeLog :
            description = changeLog[0].comment
            date = changeLog[0].datetime
        if not grpList and not prjList and not regionList:
            level ='WARNING'
        else:
            level ='ERROR'
        issueList.append({'level':level,'egroup':egroup,'group':grpList,'project':prjList,'region':regionList ,'description':description,'date':date})    
    return render_to_response('log/issuepanel.html',locals(),context_instance=RequestContext(request))

def listChangeLog(request):
    changeLogList = ChangeLog.objects.order_by('-datetime')
    return render_to_response('log/logpanel.html',locals(),context_instance=RequestContext(request))
    


    


 
    
