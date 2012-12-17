from django import template

register = template.Library()

@register.filter
def choiceval(inputfield): 
    value = inputfield.data or None 
    if value is None: 
        return u'' 
    return dict(inputfield.field.choices).get(value, u'') 
