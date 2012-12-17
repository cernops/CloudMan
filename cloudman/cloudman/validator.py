'''
Created on May 25, 2012
@author:Malik Ehsanullah
'''
from django.core import validators
import re
from django.core.exceptions import ValidationError

#This will validate name check for char A-Z a-Z 0-9 and space and - 
def validate_name(valueStr):
    if not re.match(r'^[0-9a-z_.A-Z\s-]*$', valueStr):                      
        raise ValidationError('Name contains illegal character!!!')
    
#This will validate description  check for char A-Z a-Z 0-9 and space and - 
def validate_descr(valueStr):
    if not re.match(r'^[0-9a-z_.A-Z\s-]*$', valueStr):                      
        raise ValidationError('Description contains illegal character!!!')
#This will validate comment  check for char A-Z a-Z 0-9 and space and - 
def validate_comment(valueStr):
    if not re.match(r'^[0-9a-z_.A-Z\s-]*$', valueStr):                      
        raise ValidationError('Comment contains illegal character!!!')


def validate_int(valueStr):
    if valueStr !='':
        try:
            int(valueStr)
        except:
            raise ValidationError('IntValue contains illegal character!!!')
def validate_float(valueStr):
    if valueStr !='':
        try:
            float(valueStr)
        except:
            raise ValidationError('Float contains illegal character!!!')

def validate_attrValue(valueStr):
    if not re.match(r'^[0-9a-z_.,A-Z\s-]*$', valueStr):                      
        raise ValidationError('Attribute value contains illegal character!!!')


def validate_attr(attrDict):
    try:
        for name,value in attrDict.items():
            validate_attrValue(name)
            validate_attrValue(value)
    except:
        raise ValidationError('Attribute Value contains illegal character!!!')
