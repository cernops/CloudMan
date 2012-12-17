from models import Region
from models import Project
from models import Groups
from models import Egroups


def getAllEGroups():
    returnValue = []
    allEGroups = Egroups.objects.all().order_by('name')
    for entry in allEGroups:
        returnValue.append(entry.name)
    return returnValue

def getRegionRoleList():
    returnValue = []
    regionDetails = Region.objects.all().order_by('admin_group')
    for entry in regionDetails:
        oneEntry = [entry.admin_group, 'region', entry.name, 'manager']
        returnValue.append(oneEntry)
    return returnValue
    
def getProjectRoleList():
    returnValue = []
    projectDetails = Project.objects.all().order_by('admin_group')
    for entry in projectDetails:
        oneEntry = [entry.admin_group, 'project', entry.name, 'manager']
        returnValue.append(oneEntry)
    return returnValue
    
def getGroupRoleList():
    returnValue = []
    groupDetails = Groups.objects.all().order_by('admin_group')
    for entry in groupDetails:
        oneEntry = [entry.admin_group, 'group', entry.name, 'manager']
        returnValue.append(oneEntry)
        oneEntry = [entry.name, 'group', entry.name, 'user']
        returnValue.append(oneEntry)
    return returnValue

def getGroupManagerList():
    returnValue = []
    groupDetails = Groups.objects.all().order_by('admin_group')
    for entry in groupDetails:
        oneEntry = [entry.admin_group, 'group', entry.name, 'manager']
        returnValue.append(oneEntry)
    return returnValue
    
def getGroupUserList():
    returnValue = []
    groupDetails = Groups.objects.all().order_by('admin_group')
    for entry in groupDetails:
        oneEntry = [entry.name, 'group', entry.name, 'user']
        returnValue.append(oneEntry)
    return returnValue


def getRolesList():
    returnValue = []
    returnValue.extend(getRegionRoleList())
    returnValue.extend(getProjectRoleList())
    returnValue.extend(getGroupRoleList())
    returnValue.sort(key=lambda tup: tup[0])
    return returnValue

"""
def createManagerGroupList():
    dbHost, dbUser, dbPassword, dbName = getConfigParameters.getDBConnectionParameters()
    returnValue = []

    try:
        mysqlDB = MySQLdb.connect(dbHost, dbUser, dbPassword, dbName)
        cursor = mysqlDB.cursor()
    except:
        return 0

    sqlStatement = " SELECT admin_group AS all_groups FROM groups UNION "\
                       "SELECT admin_group AS all_groups FROM project UNION "\
                       "SELECT admin_group AS all_groups FROM region "

    try:
        cursor.execute(sqlStatement)
        resultset = cursor.fetchall()

        for record in resultset:
            try:
                groupName = record[0]

                if groupName != None:
                    returnValue.append(groupName)
            except:
                print 'Error reading one record'
                continue
    except:
        print 'Error while executing query to find project admin groups'
        return returnValue

    try:
        cursor.close()
        mysqlDB.close()
    except:
        pass

    for entry in returnValue:
        print entry

    return returnValue
"""

