from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from models import Project,ProjectAllocation,ProjectMetadata,Egroups
from forms import ProjectForm
from django.db import transaction
from getPrivileges import isSuperUser
from ldapSearch import checkEGroup
from django.db.models import Q
from commonFunctions import *
from validator import *
#import copy
import simplejson

def checkNameIgnoreCase(projectName):
    projectExists = False
    if Project.objects.filter(name__iexact=projectName).exists():
        projectExists = True
    return projectExists

def isAdminOfAnyProject(adminGroups):
    userIsAdmin = False
    if len(adminGroups) < 1:
       return userIsAdmin
    qset = Q(admin_group__exact=adminGroups[0])
    if len(adminGroups) > 1:
       for group in adminGroups[1:]:
         qset = qset | Q(admin_group__exact=group)
    if (Project.objects.filter(qset)).exists():
        userIsAdmin = True
    return userIsAdmin

def isAdminOfProject(adminGroups, projectName):
    userIsAdmin = False
    if len(adminGroups) < 1:
        return userIsAdmin
    try:
        prObject = Project.objects.get(name=projectName)
        prGroup = prObject.admin_group
        if prGroup in adminGroups:
            userIsAdmin = True
        else:
            userIsAdmin = False
    except Project.DoesNotExist:
        userIsAdmin = False
    return userIsAdmin

def isUserAllowedToUpdateOrDeleteProject(projectName,groupsList):
    userIsSuperUser = isSuperUser(groupsList)
    if userIsSuperUser:
        return True
    else:
        userIsAdmin = isAdminOfProject(groupsList,projectName)
        return userIsAdmin

@transaction.commit_on_success
def addnew(request):
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    ## add operation is allowed only if user has cloudman resource manager privileges
    userIsSuperUser = isSuperUser(groupsList)
    if not userIsSuperUser:
        message = "You don't have cloudman resource manager privileges. Hence you are not authorized to add new Projects";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)

    ## if the request if due to form submission, then add the project or else return to display the form for add
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        attr_name_array = request.POST.getlist('attribute_name');
        attr_value_array = request.POST.getlist('attribute_value');
        #Create dictionary of attr_name and attr_value with attr_name:attr_value as key:value pairs
        attr_list = createDictFromList(attr_name_array,attr_value_array)
        ## validate the form
        if form.is_valid():
            redirectURL = '/cloudman/message/?msg=' 
            name = form.cleaned_data['name']
            projectExists = checkNameIgnoreCase(name)
            if projectExists:
                msgAlreadyExists = 'Project ' + name + ' already exists. Hence Add Project Operation Stopped'
                return HttpResponseRedirect(redirectURL + msgAlreadyExists);
            description = form.cleaned_data['description']
            admin_group = form.cleaned_data['admin_group']
            comment = form.cleaned_data['comment']
            try:
                validate_attr(attr_list)
            except ValidationError as e:
                msg = 'Add Project Form  '+', '.join(e.messages)
                html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/project/list/\"></HEAD><body> %s.</body></html>" %msg
                return HttpResponse(html)
            ## check first whether the admin_group exists in the local egroup table
            ## if not, then in the remote egroup database through ldap. If exists here, then add to the local table
            egroup = None
            try:
                egroup = Egroups.objects.get(name=admin_group)
            except Egroups.DoesNotExist:
                if not (checkEGroup(admin_group)):
                    errorMessage = 'Admin E-Group Entered ' + admin_group + ' does not exists'
                    return HttpResponseRedirect(redirectURL + errorMessage)
                egroup = Egroups(name=admin_group)
                egroup.save()
            #Make Sure no attribute_name or attribute_value is empty
            ##Check if all the attribute name are distinct for this first convert all the attribute name to uppercase and 
            ## After converting to uppercase check for duplicate in the array
            if checkForEmptyStrInList(attr_name_array):
                errorMessage = 'Attribute Name Cannot be Empty. Hence Add Project Operation Stopped'
                return HttpResponseRedirect(redirectURL + errorMessage)
            ##Check if all the attribute name are distinct for this first convert all the attribute name to uppercase and 
            ## After converting to uppercase check for duplicate in the array
            new_attr_name_array = [x.upper() for x in attr_name_array];
            if len(new_attr_name_array) != len( set(new_attr_name_array) ):
                errorMessage = 'Duplicate values for the Attribute Name. Hence Add Project Operation Stopped#'
                return HttpResponseRedirect(redirectURL + errorMessage)
            ## add the project and return a success message to the user
            ##Also add the project_metadata
            try:
                projectObj = Project(name=name, description=description, admin_group=admin_group)			
                projectObj.save()
                proj=Project.objects.get(name=name)
                for attr_name,attr_value  in attr_list.items():
                    project_metadata = ProjectMetadata(attribute = attr_name,value = attr_value,project = proj)
                    project_metadata.save()
                    #Write the LOg               
                projectObj = Project.objects.get(name=name)
                if addLog(request,name,comment,projectObj,None,'project','add',True):
                    transaction.commit()          
                    msgSuccess = 'New Project ' +name  + ' added successfully'
                else:
                    transaction.rollback()
                    msgSuccess = 'Error in creating the Project ' + name
            except Exception:
                print traceback.format_exc()
                transaction.rollback()
                msgSuccess = 'Error in creating the Project ' + name

            html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/project/list/\"></HEAD><body> %s.</body></html>" % msgSuccess
            return HttpResponse(html)
    else:
        form = ProjectForm()
    return render_to_response('project/addnew.html',locals(),context_instance=RequestContext(request))


def listall(request):
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';') ;
    userIsSuperUser = isSuperUser(groupsList)
    projectsList = Project.objects.all().order_by('name')
    deleteDict = {}
    showMultiDeleteOption = False
    numManaged=0
    for prjObj in projectsList:
        deleteItem = isUserAllowedToUpdateOrDeleteProject(prjObj.name,groupsList)
        if deleteItem :
            showMultiDeleteOption = True
            numManaged  +=1
        deleteDict[prjObj.name] = deleteItem 

    return render_to_response('project/listall.html',locals(),context_instance=RequestContext(request))

@transaction.commit_on_success
def delete(request):
    projectName = request.REQUEST.get("name", "")
    comment = request.REQUEST.get("comment", "deleting")
    redirectURL = '/cloudman/message/?msg='
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';')
    ## update operation is allowed only if user has either cloudman resource manager privileges
    ## or user has membership of the administrative egroup selected for this project
    if not isUserAllowedToUpdateOrDeleteProject(projectName,groupsList):
       message = "You neither have membership of administrative group of Project " + projectName + " nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to Delete Project";
       html = "<html><body> %s.</body></html>" % message
       return HttpResponse(html)

    ## Get the Project Object
    projectObject = None
    try:
       projectObject = Project.objects.get(name=projectName)
    except Project.DoesNotExist:
       failureMessage = "Project with Name " + projectName + " could not be found"
       return HttpResponseRedirect(redirectURL+failureMessage)

    ## check if any project allocations has been made for this project
    prAllocNames = ProjectAllocation.objects.filter(project__name__iexact = projectName).values_list('name', flat=True).order_by('name')

    ## if so, then alert the user with the names of the project allocations
    finalMessage = ''
    prAllocNamesList = list(prAllocNames)
    if len(prAllocNamesList) > 0:
       finalMessage = finalMessage + "Project Allocation Names: " + (', '.join(prAllocNamesList)) + "<br/>"
    if not finalMessage == '':
       finalMessage = "Project with Name " + projectName + " Could not be deleted because it is being used in " + "<br/>" + finalMessage
       html = "<html><body> %s</body></html>" % finalMessage
       return HttpResponse(html)
   #Write the LOG
    status = addLog(request,projectName,comment,projectObject,None,'project','delete',False)           
    ## If no allocations made, then delete the project and return a success message to the user
    projectObject.delete()
    if status:
        message = "Project with Name " + projectName + " deleted successfully "
    else:
        transaction.rollback()
        message = "Error in deleting Project with Name " + projectName
    html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/project/list/\"></HEAD><body> %s.</body></html>" % message
    return HttpResponse(html)

@transaction.commit_on_success
def deleteMultiple(request):
    projectNameList = request.REQUEST.get("name_list", "")
    comment = request.REQUEST.get("comment", "deleting")
    printArray = []
    title = "Delete multiple Project message"
    projectNameArray = projectNameList.split("%%")
    for projectName in projectNameArray:
        ##Get the Project Object
        projectObject = None
        try:
            projectObject = Project.objects.get(name=projectName)
        except Project.DoesNotExist:
            printArray.append( "Project with Name " + projectName + " could not be found")
            continue
        ## check if any project allocations has been made for this project
        prAllocNames = ProjectAllocation.objects.filter(project__name__iexact = projectName).values_list('name', flat=True).order_by('name')
        ## if so, then alert the user with the names of the project allocations
        finalMessage = ''
        prAllocNamesList = list(prAllocNames)
        if len(prAllocNamesList) > 0:
            finalMessage = finalMessage + "Project Allocation Names: " + (', '.join(prAllocNamesList)) + "  "
        if not finalMessage == '':
            finalMessage = "Project with Name " + projectName + " Could not be deleted because it is being used in " + " " + finalMessage
            printArray.append(finalMessage)
        else:
            addLog(request,projectName,comment,projectObject,None,'project','delete',False)
            ## If no allocations made, then delete the project and return a success message to the user
            projectObject.delete()
            printArray.append("Project with Name " + projectName + " deleted successfully ")
    return render_to_response('base/deleteMultipleMsg.html',locals(),context_instance=RequestContext(request))	

def getdetails(request):
    projectName = request.REQUEST.get("name", "")
    redirectURL = '/cloudman/message/?msg='

    ## Get the Project Object
    projectInfo = None
    try:
       projectInfo = Project.objects.get(name=projectName)
    except Project.DoesNotExist:
       errorMessage = 'Project with Name ' + projectName + ' does not exists'
       return HttpResponseRedirect(redirectURL + errorMessage)
    ##Get all the project attribute for the project
    prMetadata = ProjectMetadata.objects.filter(project__name__iexact = projectName).values('attribute','value').order_by('attribute')
 
    ## Get the names of project allocations for this project
    prAllocNames = ProjectAllocation.objects.filter(project__name__iexact = projectName).values_list('name', flat=True).order_by('name')
    object_id = projectInfo.id
    changeLogList = getLog('project',projectName,object_id,None)
    return render_to_response('project/getdetails.html',locals(),context_instance=RequestContext(request))

def getAttrInfo(request):
        redirectURL = '/cloudman/message/?msg='
    ## if the request is through ajax, then return the json object, otherwise return status 400 - BAD REQUEST
    #if request.is_ajax():
        format = 'json'
        mimetype = 'application/javascript'
        projectName = request.REQUEST.get("name", "")
        attribute_list = []
        prjMetadataList = ProjectMetadata.objects.filter(project__name__iexact = projectName)

        for metadata in prjMetadataList:               
               attr_name =  metadata.attribute               
               attr_value = metadata.value
               attribute_list.append({'attribute':attr_name,'value':attr_value})               
        data = simplejson.dumps(attribute_list)
        return HttpResponse(data,mimetype)


@transaction.commit_on_success
def update(request):
    projectName = request.REQUEST.get("name", "")
    redirectURL = '/cloudman/message/?msg='
    groups = request.META.get('ADFS_GROUP','')
    groupsList = groups.split(';')
    userIsSuperUser = isSuperUser(groupsList)
    ## update operation is allowed only if user has either cloudman resource manager privileges
    ## or user has membership of the administrative egroup selected for this project
    if not isUserAllowedToUpdateOrDeleteProject(projectName,groupsList):
        message = "You neither have membership of administrative group of Project " + projectName + " nor possess Cloudman Resource Manager Privileges. Hence you are not authorized to Edit Project";
        html = "<html><body> %s.</body></html>" % message
        return HttpResponse(html)
    ## Get the Project Object
    projectObject = None
    try:
        projectObject = Project.objects.get(name=projectName)       
    except Project.DoesNotExist:
        failureMessage = "Project with Name " + projectName + " could not be found"
        return HttpResponseRedirect(redirectURL+failureMessage)
    oldProjectInfo = getProjectInfo(projectObject)
    ##Get the Project Attribute
    Metadata = ProjectMetadata.objects.filter(project__name__iexact = projectName).values('attribute','value').order_by('attribute')
    ## if the request is through form submission, then update the values or else present a form for update
    if request.method == 'POST':
        ## Existing values 
        currName = projectObject.name
        currDescription = projectObject.description
        currAdmin_group = projectObject.admin_group
        ## New values
        newName = request.POST['newname']
        newDescription = request.POST['description']
        newAdmin_group = request.POST['admin_group']
        comment = request.POST['comment']
        ## New values for Project metadata
        new_attr_name_list = request.POST.getlist('attribute_name');
        new_attr_value_list = request.POST.getlist('attribute_value');
        #Create dictionary of attr_name and attr_value with attr_name:attr_value as key:value pairs
        attr_list = createDictFromList(new_attr_name_list,new_attr_value_list) 
        
        try:
            validate_name(newName)
            validate_descr(newDescription)
            validate_name(newAdmin_group)
            validate_comment(comment)
            validate_attr(attr_list)
        except ValidationError as e:
            msg = 'Edit Project Form  '+', '.join(e.messages)
            html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/project/list/\"></HEAD><body> %s.</body></html>" %msg
            return HttpResponse(html)
        #Make Sure no attribute_name or attribute_value is empty
        if checkForEmptyStrInList(new_attr_name_list):
            errorMessage = 'Attribute Name Cannot be Empty. Hence Update Project Operation Stopped'
            return HttpResponseRedirect(redirectURL + errorMessage)
        ##Make Sure that all the attribute_name are distinct
        if checkForDuplicateStrInList(new_attr_name_list): 
            errorMessage = 'Duplicate values for the Attribute Name. Hence Update Project Operation Stopped'
            return HttpResponseRedirect(redirectURL + errorMessage)
        ## if name has been changed, validate it, then assign the new name
        if (currName != newName):
            if (newName == ''):
                errorMsg = 'Project name field cannot be left blank. So Edit Project operation stopped'
                return HttpResponseRedirect(redirectURL + errorMsg)
            projectExists = checkNameIgnoreCase(newName)
            if projectExists:
                msgAlreadyExists = 'Project ' + newName + ' already exists. Hence Edit Project Operation Stopped'
                return HttpResponseRedirect(redirectURL + msgAlreadyExists);
            projectObject.name = newName       
        ## if description has been changed, assign the new value
        if (currDescription != newDescription):
            projectObject.description = newDescription        
        ## if admin_group value changed, check first whether the new admin_group exists in the local egroup table
        ## if not, then in the remote egroup database through ldap. If exists here, then add to the local table   
        egroup = None
        if (currAdmin_group != newAdmin_group):
            if (newAdmin_group == ''):
                errorMsg = 'Admin E-Group field cannot be left blank. So Edit Project operation stopped'
                return HttpResponseRedirect(redirectURL + errorMsg)
            try:
                egroup = Egroups.objects.get(name=newAdmin_group)
            except Egroups.DoesNotExist:
                if not (checkEGroup(newAdmin_group)):
                    errorMessage = 'Selected Admin E-Group ' + newAdmin_group + ' does not exists'
                    return HttpResponseRedirect(redirectURL + errorMessage)
                egroup = Egroups(name=newAdmin_group)
                egroup.save()
            projectObject.admin_group = egroup
        ## finally save all the changes and return a success message to the user
        projectObject.save()
        old_attr_name_list =[]
        oldprMetaObj = ProjectMetadata.objects.filter(project = projectObject).values('attribute')
        for item in oldprMetaObj:
            old_attr_name_list.append(item['attribute'])
        ProjectMetadata.objects.filter(project = projectObject).delete()
        new_attr_list =[]
        for attr_name,attr_value  in attr_list.items(): 
            project_metadata = ProjectMetadata(attribute = attr_name,value = attr_value,project = projectObject)
            new_attr_list.append(attr_name)
            project_metadata.save()
        ##delete the obselete Atribute Name:value pair from projectAllocatioNMetadata
        obsolete_attr_list = set(old_attr_name_list) - set(new_attr_list) 
        #delete the Attribute from the ProjectAllocationMetadata
        ProjectAllocationMetadata.objects.filter(project = projectObject, attribute__in=list(obsolete_attr_list)).delete() 
        newProjectInfo = getProjectInfo(projectObject)
        objectId = projectObject.id 
        if addUpdateLog(request,newName,objectId,comment,oldProjectInfo,newProjectInfo,'project',True):
            message = 'Project ' + projectName + ' Successfully Updated'
            transaction.commit()
        else:
            transaction.rollback() 
            message = 'Error while updating Project ' + projectName
        html = "<html><HEAD><meta HTTP-EQUIV=\"REFRESH\" content=\"4; url=/cloudman/project/list/\"></HEAD><body> %s.</body></html>" % message
        return HttpResponse(html)    
    return render_to_response('project/update.html',locals(),context_instance=RequestContext(request))
