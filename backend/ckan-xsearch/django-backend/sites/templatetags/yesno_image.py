from django.template import Variable, VariableDoesNotExist
from django import template
register = template.Library()


@register.inclusion_tag('sites/yesno_image.html')
def yesno_image(object, fieldname):
    pseudo_context = {'object': object}
    try:
        value = Variable('object.%s' % fieldname).resolve(pseudo_context)
    except VariableDoesNotExist:
        value = None

    return {'value': value}
