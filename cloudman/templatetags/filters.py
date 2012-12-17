from django import template
from settings import *
register = template.Library()

#This will display the undefined on the GUI if value is None it will print '' else value
@register.filter
def displayNone(value):
    if value is None:
        return '-'
    else:
        return value

displayNone = register.simple_tag(displayNone)


##This will display the undefined on the GUI this is used as templatetag
@register.simple_tag
def displayUndefined():
    return '-'

displayUndefined = register.simple_tag(displayUndefined)


#This will display the undefined on the GUI if value is None it will print '' else value
@register.filter()
def truncchar(value, arg):
    """
    Truncates a string after a certain number of characters.

    Argument: Number of characters to truncate after.
    """
    if len(value) < arg:
        return value
    else:
        return value[:arg] + '...'

register.filter('truncchar', truncchar)



@register.filter
def dictvalue(dictionary, key):
    try:
        return dictionary[key]
    except:
        return None
    
register.filter('dictvalue', dictvalue)


@register.simple_tag
def convertFunction():
    jscript = ''
    index=0
    for cpu_unit in CPU_UNIT_NAME:
        jscript  += "if(unit =='%s')\n" %cpu_unit
        jscript  += "return value / %s\n" %CPU_UNIT_CONVERSION_FACTOR[index]
        index = index+1
    return jscript

convertFunction = register.simple_tag(convertFunction)


@register.simple_tag
def convertStorageFunction():
    jscript = ""
    index=0
    for storage_unit in STORAGE_UNIT_NAME:
        jscript  += "if(unit =='%s')\n" %storage_unit
        jscript  += "return value * %s\n" %STORAGE_UNIT_CONVERSION_FACTOR[index]
        index = index+1
    return jscript

convertFunction = register.simple_tag(convertFunction)



@register.simple_tag
def displayHepSpecUnit():
    start = "<select   name=selhepspecsunit id=selhepspecsunit>"
    end = '</select>'
#    option ="<option value=%s>%s</option>" %(DEFAULT_CPU_UNIT,DEFAULT_CPU_UNIT)
    option = ''
    for unit in CPU_UNIT_NAME:        
        if unit == DEFAULT_CPU_UNIT:
            option = option +"<option selected value=%s>%s</option>" %(unit,unit)
        else:
            option = option +"<option value=%s>%s</option>" %(unit,unit)

    return start+option+end

displayHepSpecUnit = register.simple_tag(displayHepSpecUnit)

@register.simple_tag
def displayStorageUnit():
    start = "<select  name=selstorageunit id=selstorageunit>"
    end = '</select>'
#    option ="<option selected value=%s>%s</option>" %(DEFAULT_STORAGE_UNIT,DEFAULT_STORAGE_UNIT)
    option = ''
    for unit in STORAGE_UNIT_NAME:        
        if unit == DEFAULT_STORAGE_UNIT:
            option = option +"<option selected value=%s>%s</option>" %(unit,unit)
        else:
            option = option +"<option  value=%s>%s</option>" %(unit,unit)
    return start+option+end
    
displayStorageUnit = register.simple_tag(displayStorageUnit)














