from getEGroupRoles import getRolesList

def getCloudmanEGroups(rolesList):
    cloudmanEGroups = set()
    for entry in rolesList:
        cloudmanEGroups.add(entry[0])
    return cloudmanEGroups

 
def getUserRoles(eGroupList):
    rolesList = getRolesList()
    cloudmanEGroups = getCloudmanEGroups(rolesList)
    
    #eGroupList.sort()
    userEGroups = set(eGroupList)
    userRoles = []
    groupUser = set()
    groupManager = set()
    projectManager = set()
    regionManager = set()
    for entry in rolesList:
        if entry[0] in userEGroups:
            if entry[1] == 'group':
                if entry[3] == 'user':
                    groupUser.add(entry[2])
                elif entry[3] == 'manager':
                    groupManager.add(entry[2])
            elif entry[1] == 'project':
                if entry[3] == 'manager':
                    projectManager.add(entry[2])
            elif entry[1] == 'region':
                if entry[3] == 'manager':
                    regionManager.add(entry[2])

    userRoles.append(['group', 'user', groupUser])
    userRoles.append(['group', 'manager', groupManager])
    userRoles.append(['project', 'manager', projectManager])
    userRoles.append(['region', 'manager', regionManager])

    return userRoles
 
                        

