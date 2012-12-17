from models import Region
from models import Zone
from models import Groups
from models import ResourceType
from models import Project
from models import TopLevelAllocation
from models import ProjectAllocation
from django.db.models import Count

def getRegionCount():
    regionCount = 0
    regionCount = Region.objects.count()
    return regionCount

def getZoneCount():
    zoneCount = 0
    zoneCount = Zone.objects.count()
    return zoneCount

def getGroupsCount():
    groupCount = 0
    groupCount = Groups.objects.count()
    return groupCount

def getResourceTypesCount():
    resourceTypesCount = 0
    resourceTypesCount = ResourceType.objects.count()
    return resourceTypesCount

def getProjectsCount():
    projectsCount = 0
    projectsCount = Project.objects.count()
    return projectsCount

def getTopLevelAllocationsCount():
    topLevelAllocationsCount = 0
    topLevelAllocationsCount = TopLevelAllocation.objects.count()
    return topLevelAllocationsCount

def getProjectAllocationsCount():
    projectAllocationsCount = 0
    projectAllocationsCount = ProjectAllocation.objects.count()
    return projectAllocationsCount
