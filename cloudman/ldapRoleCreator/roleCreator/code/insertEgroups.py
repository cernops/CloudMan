import MySQLdb
import getConfigParameters
import manageUsersAndGroups
import ldapSearchNEW
import ldapSearch

def insertEGroups(eGroupList):
    noOfEntries = len(eGroupList)

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

    for groupName in eGroupList:

        SQLStatement = "INSERT INTO egroups(name) VALUES ('" \
                            + groupName + "')"
        #print SQLStatement

        try:
            cursor.execute(SQLStatement)
            cursor.execute(savepointStmt)
            count = count + 1
        except MySQLdb.IntegrityError, message:
            #print 'E-group %s exists..' %(groupName)
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


allUsers = ldapSearchNEW.getMembersInAGroup('myall-cern')
allGroups = []
count = 0
maxCommitSize = 100
for userName in allUsers:
    print "Finding groups of user %s " %userName
    oneUsersGroups = ldapSearchNEW.getGroupsFromMemberName(userName)
    allGroups.extend(oneUsersGroups)
    print allGroups
    allDistinctGroups = set(allGroups)
    initialSize = len(allGroups)
    distinctSize = len(allDistinctGroups)
    print "Size compressed from %d to %d ... Commit at %d " %(initialSize, distinctSize, maxCommitSize)
    if distinctSize >= maxCommitSize:
        finalGroupsList = list(allDistinctGroups)
        insertRoles(finalGroupsList)
        #allGroups = []
        #allDistinct = Set()
    
    #for oneGroup in oneUsersGroups:
    #    allGroups.append(oneGroup)
    #print "Currently we know %d groups" % len(allGroups)
#allDistinctGroups = set(allGroups)
#initialSize = len(allGroups)
#distinctSize = len(allDistinctGroups)
#count = 0
#for group in allDistinctGroups:
#    count = count + 1
#    print "%d. %s" %(count, group)
#print "Compressed %d groups into %d" % (initialSize, distinctSize)

#finalGroupsList = list(allDistinctGroups)
#insertRoles(finalGroupsList)
