import ldap
import pprint
import ldap.resiter
import sys
 
ldap_uri = "ldap://xldap.cern.ch"
ldap_base = "OU=Users,OU=Organic Units,DC=cern,DC=ch"
page_entry_num =100 
 
class MyLDAPObject(ldap.ldapobject.LDAPObject,ldap.resiter.ResultProcessor):
    pass
 
ldapconn = MyLDAPObject(ldap_uri)
msg_id = ldapconn.search(ldap_base, ldap.SCOPE_SUBTREE, "(memberOf:1.2.840.113556.1.4.1941:=CN=young-at-cern,OU=e-groups,OU=Workgroups,DC=cern,DC=ch)",['name'])
 
i = 0
for res_type, res_data, res_msgid,res_controls in ldapconn.allresults(msg_id):
    for dn, entry in res_data:
        print dn, entry['name']

"""
for res_type,result,res_msgid,res_controls in ldapconn.allresults(msg_id):
    if i >= page_entry_num:
        try:
            raw_input('Press Enter for next page or CTRL-C to interrupt:')
        except KeyboardInterrupt:
            ldapconn.abandon(msg_id)
            print "..Bye."
            sys.exit()
 
        i = 0
 
    for rdn, ldap_obj in result:
        print "***********************"
        print "RDN: " + rdn
        print "***********************"
        pprint.pprint(ldap_obj)
        print "***********************"
        print ""
 
    i = i + 1
"""
