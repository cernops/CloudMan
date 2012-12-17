import pprint
import sys
import ldap
import ldap.resiter
import time
from ldap.controls import SimplePagedResultsControl
import ldap.modlist as modlist
#from sets import Set


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


def checkEGroup(groupName):
    filterString = '(CN=%s)' % groupName
    resultset  = pagedLDAPSearch(base='OU=e-groups,OU=Workgroups,DC=cern,DC=ch', \
        filter= filterString, attributes=['cn'])
    lengthResult = len(resultset)
    if lengthResult == 0:
        return False
    
    return True

#This will give the egroup which contains the namecontain
def getEgroupListNameContain(namecontain):
    filterString = '(cn=*%s*)' % namecontain
    resultset  = pagedLDAPSearch(base='OU=e-groups,OU=Workgroups,DC=cern,DC=ch', \
        filter= filterString, attributes=['cn'])
    egrouplist = []
    for item in resultset:
        egrouplist.append(item[1]['cn'][0])
    
    return egrouplist




