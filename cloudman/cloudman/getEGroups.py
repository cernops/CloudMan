from models import Egroups


def getAllEGroups():
    returnValue = []
    allEGroups = Egroups.objects.all().order_by('name')
    for entry in allEGroups:
        returnValue.append(entry.name)
    return returnValue

