from settings import SUPER_USER_GROUPS

def isSuperUser(usersGroups):
    groupsSet = set(usersGroups)
    suSet = set(SUPER_USER_GROUPS)
    intersectionSet = groupsSet.intersection(suSet)
    if len(intersectionSet) <= 0:
        return False
    return True
    """if groupsSet.isdisjoint(SUPER_USER_GROUPS):
        return True 
    return False"""
