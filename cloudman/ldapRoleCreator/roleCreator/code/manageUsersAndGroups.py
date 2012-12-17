import MySQLdb
from ldapSearch import getUserGroupMapping
import getConfigParameters 


def insertUserGroupMapping(userGroupList):
    dbHost, dbUser, dbPassword, dbName = getConfigParameters.getDBConnectionParameters()
    maxRecordsInOneCommit = getConfigParameters.getMaxInsertsInOneCommit()

    userName = ""
    groupName = ""
    count = 0

    listSize = len(userGroupList)

    if listSize <= 0:
        return 0

    savepointStmt = "SAVEPOINT A"
    try:
        mysqlDB = MySQLdb.connect(dbHost, dbUser, dbPassword, dbName)
        mysqlDB.autocommit(False)
        cursor = mysqlDB.cursor()
    except:
        return 0
    noOfCommits = 0

    cursor.execute(savepointStmt)

    for tuple in userGroupList:
        groupName = tuple[0]
        userName = tuple[1]

        SQLStatement = "INSERT INTO user_group_mapping (user_name, group_name) VALUES ('" \
                           + userName + "', '" \
                           + groupName + "')"

        try:
            cursor.execute(SQLStatement)
            cursor.execute(savepointStmt)
            count = count + 1
        except MySQLdb.IntegrityError, message:
            #print 'User %s is already present in group %s' % (userName, groupName)
            pass

        if count >= maxRecordsInOneCommit:
            count = 0
            try:
                mysqlDB.commit()
                noOfCommits = noOfCommits + 1
            except:
                continue 


    #print "All insertions done... time to commit"

    try:
        cursor.close()
        if count > 0:
            mysqlDB.commit()
            noOfCommits = noOfCommits + 1
    except:
        count = 0  #No insertions in the last attempt
        #print 'Error committing the last set \n'
        pass

    if count > 0:
        returnValue = (noOfCommits - 1)*maxRecordsInOneCommit + count
    else:
        returnValue = count

    print 'Total no. of commits: %d' %noOfCommits
    print 'No. of mappings: %d' %returnValue

    try:
        mysqlDB.close() 
    except:
        print 'Error while closing the mysql connection'
        pass

    return returnValue


def createGroupList():
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

    #for entry in returnValue:
    #    print entry

    return returnValue


#mappingList = getUserGroupMapping(['it-dep-pes-ps','it-dep-pes','it-dep-full','young-at-cern'])
#mappingList = createGroupList()
#insertUserGroupMapping(mappingList)
