from ldapSearch import searchLDAP

searchLDAP(base='OU=Workgroups,DC=cern,DC=ch',\
      filter='(member:1.2.840.113556.1.4.1941:=cn=visharma,ou=users,ou=organic units,DC=cern,dc=ch)',\
      attributes=['cn'])




