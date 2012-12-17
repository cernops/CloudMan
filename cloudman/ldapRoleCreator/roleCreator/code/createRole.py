import MySQLdb
import getConfigParameters 
import manageUsersAndGroups
import ldapSearch

def insertRoles(roleList):
    noOfEntries = len(roleList)

    if noOfEntries <= 0: 
        return 0

    dbHost, dbUser, dbPassword, dbName = getConfigParameters.getDBConnectionParameters()
    maxRecordsInOneCommit = getConfigParameters.getMaxInsertsInOneCommit()

    try:
        mysqlDB = MySQLdb.connect(dbHost, dbUser, dbPassword, dbName)
        mysqlDB.autocommit(False)
        cursor = mysqlDB.cursor()
    except:
        print 'Cannot open connection to database '
        return 0
        pass

    savepointStmt = "SAVEPOINT A" 
    count = 0
    noOfCommits = 0

    for entry in roleList:
        userName = entry[0]
        sphereType = entry[1]
        sphereName = entry[2]
        role = entry[3]

        SQLStatement = "INSERT INTO user_roles (user_name, sphere_type, sphere_name, role) VALUES ('" \
                            + userName + "', '" \
                            + sphereType + "', '"\
                            + sphereName + "', '" \
                            + role + "')"
        #print SQLStatement

        try:
            cursor.execute(SQLStatement)
            cursor.execute(savepointStmt)
            count = count + 1
        except MySQLdb.IntegrityError, message:
            #print 'Role exists for user(%s %s %s %s)' %(userName, sphereType, sphereName, role)
            pass

        if count >= maxRecordsInOneCommit:
            count = 0
            try:
                mysqlDB.commit()
                noOfCommits = noOfCommits + 1
            except:
                continue

    try:
        cursor.close()
        if count > 0:
            mysqlDB.commit()
            noOfCommits = noOfCommits + 1
    except:
        count = 0  #No insertions in the last attempt
        #print 'Error committing the last set \n'
        pass

    if noOfCommits > 0:
        returnValue = (noOfCommits - 1)*maxRecordsInOneCommit + count
    else: 
        returnValue = count

    print 'Total no. of commits: %d' %noOfCommits
    print 'Total no. of roles: %d' %returnValue

    try:
        mysqlDB.close()
    except:
        print 'Error while closing the mysql connection'
        pass

    return returnValue


def getGroupAdminGroups():
    returnValue = []
    dbHost, dbUser, dbPassword, dbName = getConfigParameters.getDBConnectionParameters()

    try:
        mysqlDB = MySQLdb.connect(dbHost, dbUser, dbPassword, dbName)
        cursor = mysqlDB.cursor()
    except:
        print 'Cannot open connection to database '
        return returnValue
        pass

    sqlStatement = "SELECT name, admin_group FROM groups"

    try:
        cursor.execute(sqlStatement)
        resultset = cursor.fetchall()

        for record in resultset:
            try:
                groupName = record[0]
                adminGroupName = record[1]

                if adminGroupName != None:
                    oneEntry = [groupName, adminGroupName]
                    returnValue.append(oneEntry)
            except:
                print 'Error reading one record'
                continue

    except:
        print 'Error while executing query to find group admin groups'
        return returnValue

    try:
        cursor.close()
        mysqlDB.close()
    except:
        pass

    for entry in returnValue:
        print entry

    return returnValue


def getProjectAdminGroups():
    returnValue = []
    dbHost, dbUser, dbPassword, dbName = getConfigParameters.getDBConnectionParameters()

    try:
        mysqlDB = MySQLdb.connect(dbHost, dbUser, dbPassword, dbName)
        cursor = mysqlDB.cursor()
    except:
        print 'Cannot open connection to database '
        return returnValue
        pass

    sqlStatement = "SELECT name, admin_group FROM project"

    try:
        cursor.execute(sqlStatement)
        resultset = cursor.fetchall()

        for record in resultset:
            try:
                projectName = record[0]
                adminGroupName = record[1]

                if adminGroupName != None:
                    oneEntry = [projectName, adminGroupName]
                    returnValue.append(oneEntry)
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



def getRegionAdminGroups():
    returnValue = []
    dbHost, dbUser, dbPassword, dbName = getConfigParameters.getDBConnectionParameters()

    try:
        mysqlDB = MySQLdb.connect(dbHost, dbUser, dbPassword, dbName)
        cursor = mysqlDB.cursor()
    except:
        print 'Cannot open connection to database '
        return returnValue
        pass

    sqlStatement = "SELECT name, admin_group FROM region"

    try:
        cursor.execute(sqlStatement)
        resultset = cursor.fetchall()
 
        for record in resultset:
            try:
                regionName = record[0]
                adminGroupName = record[1]

                if adminGroupName != None:
                    oneEntry = [regionName, adminGroupName]
                    returnValue.append(oneEntry)
            except:
                print 'Error reading one record'
                continue
    except:
        print 'Error while executing query'
        return returnValue

    try:
        cursor.close()
        mysqlDB.close()
    except:
        pass

    for entry in returnValue:
        print entry

    return returnValue


def createGroupManageRoles():
    dbHost, dbUser, dbPassword, dbName = getConfigParameters.getDBConnectionParameters()

    try:
        mysqlDB = MySQLdb.connect(dbHost, dbUser, dbPassword, dbName)
        cursor = mysqlDB.cursor()
    except:
        print 'Cannot open connection to database '
        return returnValue
        pass

    groupsAndAdminGroups = getGroupAdminGroups()
    roleList = []

    for entry in groupsAndAdminGroups:
        groupName = entry[0]
        adminGroup = entry[1]
        print 'group %s admin group %s' %(groupName, adminGroup)
        if adminGroup != '':
            usersList = manageUsersAndGroups.getGroupMembersFromDatabase([adminGroup])
            for userGroupMapping in usersList:
                #groupName = userGroupMapping[0]
                userName = userGroupMapping[1]
                roleList.append([userName, 'group', groupName, 'manager'])
        else:
            pass

    for entry in roleList:
        print entry

    insertRoles(roleList)

    try:
        cursor.close()
        mysqlDB.close()
    except:
        pass


def createRegionManageRoles():
    dbHost, dbUser, dbPassword, dbName = getConfigParameters.getDBConnectionParameters()

    try:
        mysqlDB = MySQLdb.connect(dbHost, dbUser, dbPassword, dbName)
        cursor = mysqlDB.cursor()
    except:
        print 'Cannot open connection to database '
        return returnValue
        pass

    regionsAndAdminGroups = getRegionAdminGroups()
    roleList = []

    for entry in regionsAndAdminGroups:
        regionName = entry[0]
        adminGroup = entry[1]
        if adminGroup != '':
            usersList = manageUsersAndGroups.getGroupMembersFromDatabase([adminGroup])
            for userGroupMapping in usersList:
                groupName = userGroupMapping[0]
                userName = userGroupMapping[1]
                roleList.append([userName, 'region', regionName, 'manager'])
        else:
            pass

    for entry in roleList:
        print entry

    insertRoles(roleList)

    try:
        cursor.close()
        mysqlDB.close()
    except:
        pass



def createProjectManageRoles():
    dbHost, dbUser, dbPassword, dbName = getConfigParameters.getDBConnectionParameters()

    try:
        mysqlDB = MySQLdb.connect(dbHost, dbUser, dbPassword, dbName)
        cursor = mysqlDB.cursor()
    except:
        print 'Cannot open connection to database '
        return returnValue
        pass

    projectsAndAdminGroups = getProjectAdminGroups()
    roleList = []

    for entry in projectsAndAdminGroups:
        projectName = entry[0]
        adminGroup = entry[1]

        if adminGroup != '':
            usersList = manageUsersAndGroups.getGroupMembersFromDatabase([adminGroup])
            for userGroupMapping in usersList:
                groupName = userGroupMapping[0]
                userName = userGroupMapping[1]
                roleList.append([userName, 'project', projectName, 'manager'])
        else:
            pass

    for entry in roleList:
        print entry

    insertRoles(roleList)

    try:
        cursor.close()
        mysqlDB.close()
    except:
        pass


#createRegionManageRoles() 
#createProjectManageRoles()
#getGroupMembersFromDatabase(['it-dep-pes-ps','it-dep-pes',''])
#getRegionAdminGroups()
#insertRoles([['visharma','group','123','user'],['visharma','project','321','manager']]) 

def main():
    print 'Creating list of groups in database...'
    groupsList = manageUsersAndGroups.createGroupList()
    print 'Making LDAP request to find the members of the known groups...'
    userGroupMapping = ldapSearch.getUserGroupMapping(groupsList)
    print 'Inserting the user-group pairs in database...'
    manageUsersAndGroups.insertUserGroupMapping(userGroupMapping)
    print 'Inserting roles for region management...'
    createRegionManageRoles() 
    print 'Inserting roles for project management...'
    createProjectManageRoles()
    print 'Inserting roles for group management...'
    createGroupManageRoles()




if __name__ == "__main__":
    main()



"""
def getGroupMembersFromDatabase(groupNames):
    returnValue = []
    noOfEntries = len(groupNames)

    if noOfEntries <= 0: 
        return returnValue

    dbHost, dbUser, dbPassword, dbName = getConfigParameters.getDBConnectionParameters()

    try:
        mysqlDB = MySQLdb.connect(dbHost, dbUser, dbPassword, dbName)
        mysqlDB.autocommit(False)
        cursor = mysqlDB.cursor()        
    except:
        print 'Cannot open connection to database '
        return returnValue
        pass

    sqlStmtPrefix = "SELECT user_name FROM user_group_mapping WHERE group_name = '"

    for oneGroup in groupNames:
        if oneGroup != '':
           sqlStmt = sqlStmtPrefix + oneGroup + "'"
        else:
           continue

        try:
            cursor.execute(sqlStmt)
            resultset = cursor.fetchall()
        except:
            continue
 
        for entry in resultset:
            userName = entry[0]
            if userName != None:
                newReturnEntry = [oneGroup, userName]
                returnValue.append(newReturnEntry)

    try:
        cursor.close()
        mysqlDB.close()
    except:
        pass

    for entry in returnValue:
        print entry

    return returnValue
"""
