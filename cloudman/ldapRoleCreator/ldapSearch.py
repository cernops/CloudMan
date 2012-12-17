import pprint
import sys
import ldap
import ldap.resiter
import time
from ldap.controls import SimplePagedResultsControl
import ldap.modlist as modlist



def pagedLDAPSearch(base, filter, attributes, timeout=0, pageSize=100, server='xldap.cern.ch', who="", cred="", scope=ldap.SCOPE_SUBTREE):
    returnValue = []
    ldapServer = 'ldap://' + server
    try:
        ldapConnection = ldap.initialize(ldapServer)
    except ldap.LDAPError, err:
        sys.stderr.write('Error connecting to server ' + ldapServer + '\nReason - ' + str(err))
        return returnValue

    pagedResultsControl = SimplePagedResultsControl(ldap.LDAP_CONTROL_PAGE_OID, True, (pageSize, ''))

    results = []
    pageCounter = 0

    while True:
        #print 'LoopCounter----%d' % pageCounter
        serverControls = [pagedResultsControl]

        try:
            messageId = ldapConnection.search_ext(base, scope, filter, attributes, serverctrls = serverControls)
        except ldap.LDAPError, err:
            sys.stderr.write('Error performing user paged search: ' + str(err) + '\n')
            return returnValue

        try:
            resultCode, results, unusedMessageId, serverControls = ldapConnection.result3(messageId)
        except ldap.LDAPError, err:
            sys.stderr.write('Error getting user paged search results: ' + str(err) + '\n')
            return returnValue

        for result in results:
            pageCounter = pageCounter + 1
            returnValue.append(result)

        cookie = None

        for serverCtrl in serverControls:
            if serverCtrl.controlType == ldap.LDAP_CONTROL_PAGE_OID:
                unusedValue, cookie = serverCtrl.controlValue
                if cookie:
                    pagedResultsControl.controlValue = (pageSize, cookie)
                break
        if not cookie:
            break

    try:
        ldapConnection.unbind_s()
    except ldap.LDAPError, err:
        sys.stderr.write('Error while disconnecting from server ' + ldapServer + '... Reason ' + str(err) + '\n')
        return returnValue

    return returnValue



def searchLDAP(base, filter, attributes, timeout=0, server='xldap.cern.ch', who="", cred="", scope=ldap.SCOPE_SUBTREE ):

    returnvalue = list()

    try:
        #print "Connecting..."
        l = ldap.open(server)
        l.simple_bind_s(who, cred)
        print "Successfully connected..."
        
    except ldap.LDAPError, error_message:
        print "Error connecting... %s " % error_message
        return returnvalue

    resultset = []

    try:
        print "Searching...."
        result_id = l.search(base, scope, filter, attributes)
        #print result_id
        count = 0 

        while 1:
            result_type, result_data = l.result(result_id, timeout)
            #print result_data 

            if(result_data == []):
                #print "No data in result_data"
                break
            else:
                if (result_type == ldap.RES_SEARCH_ENTRY):
                    count = count + 1
                    print "Appending %d" %count
                    print result_data
                    resultset.append(result_data)
            #print "Helllo....."

        if len(resultset) == 0:
            print "Nothing found"
         
        print "Now preparing return value"       
        returnvalue = [resultset, result_type, result_data]
        print "Search completed ..."

    except:
        print "Exception while searching or parsing the result"

    return returnvalue

def getMembersInAGroup(groupName):
    returnValue = []
    filterString = '(memberOf:1.2.840.113556.1.4.1941:=CN=%s,OU=e-groups,OU=Workgroups,DC=cern,DC=ch)' % groupName
    print "%s" % filterString
    resultset  = pagedLDAPSearch(base='OU=Users,OU=Organic Units,DC=cern,DC=ch', \
        filter= filterString, attributes=['name'])

    lengthResult = len(resultset)
    count = 0

    if lengthResult == 0:
        print "No member in the group...Strange...Check group name..Or is it a new group"

    for entry in resultset:
        print entry
        try:
            memberName = entry[1]['name'][0]
            returnValue.append(memberName)
            count = count + 1
            print "%d. %s" %(count, memberName)

        except:
            print "In exception...."
    print "Group %s contains %d members " % (groupName, count)
    return returnValue


def getGroupsFromMemberName(memberName):
    returnValue = []
    filterString = '(member:1.2.840.113556.1.4.1941:=cn=%s,ou=users,ou=organic units,DC=cern,dc=ch)' % memberName
    #print "%s" % filterString
    resultset = pagedLDAPSearch(base='OU=Workgroups,DC=cern,DC=ch', \
        filter= filterString, attributes=['name'])

    lengthResult = len(resultset)
    count = 0

    if lengthResult == 0:
        print "Not a member of any group...Strange...Check name..Or a new member??"

    for entry in resultset:
        try:
            groupName = entry[1]['name'][0]
            returnValue.append(groupName)
            count = count + 1
            print "%d. %s" %(count, groupName)

        except:
            print "In exception...."
    print "User %s belongs to %d groups " % (memberName, count)
    return returnValue


def getUserGroupMapping(groupNames):

    returnValue = []
    #returnMemberNames = []
    #returnGroupNames = []
    oneReturnTuple = []
    oneGroupsMembers = []
    noOfGroups = len(groupNames)
    if (noOfGroups == 0):
        return returnValue

    for oneGroup in groupNames:
        print oneGroup
        oneGroupMembers = []
        try:
            oneGroupMembers = getMembersInAGroup(oneGroup)
            for memberName in oneGroupMembers:
                oneReturnTuple = [oneGroup, memberName]
                #print oneReturnTuple
                returnValue.append(oneReturnTuple)
        except: 
            print "Exception while searching for the members of the group %s " %oneGroup

    for data in returnValue:
        print data
    return returnValue

    



getMembersInAGroup('it-dep-pes')    
#getGroupsFromMemberName('visharma')
#getGroupsFromMemberName('uschwick')
#getGroupsFromMemberName('schwicke')
#getUserGroupMapping(['myall-cern','young-at-cern','it-dep-pes'])
#getUserGroupMapping(['young-at-cern'])

#searchLDAPWithPaging("OU=Users,OU=Organic Units,DC=cern,DC=ch", "(memberOf:1.2.840.113556.1.4.1941:=CN=young-at-cern,OU=e-groups,OU=Workgroups,DC=cern,DC=ch)" ,['name'])




"""
def searchLDAPWithPaging(base, filter, attributes, timeout=0, pageSize=100, server='xldap.cern.ch', who="", cred="", scope=ldap.SCOPE_SUBTREE):

    returnValue = []
    ldapUrl = "ldap://" + server

    ldapConn = MyLDAPObject(ldapUrl)
    messageId = ldapConn.search(base, scope, filter, attributes)

    counter = 0
    for result_type, result, result_msgid, result_controls in ldapConn.allresults(messageId):
        if counter >= pageSize:
            counter = 0

        for rdn, ldapObject in result:
            print "RDN: " + rdn 
            pprint.pprint(ldapObject)

        counter = counter + 1
"""

"""
def getMembersInAGroup(groupName):
    returnValue = []
    filterString = '(memberOf:1.2.840.113556.1.4.1941:=CN=%s,OU=e-groups,OU=Workgroups,DC=cern,DC=ch)' % groupName
    print "%s" % filterString
    resultset, resultType, resultData = pagedLDAPSearch(base='OU=Users,OU=Organic Units,DC=cern,DC=ch', \
        filter= filterString, attributes=['name'])

    lengthResult = len(resultset)
    count = 0

    if lengthResult == 0:
        print "No member in the group...Strange...Check group name..Or is it a new group"

    for input in range(lengthResult):
        print input
        for entry in resultset[input]:
            print entry
            try:
                memberName = entry[1]['name'][0]
                returnValue.append(memberName)
                count = count + 1
                print "%d. %s" %(count, memberName)

            except:
                print "In exception...."
    print "Group %s contains %d members " % (groupName, count)
    return returnValue
"""
