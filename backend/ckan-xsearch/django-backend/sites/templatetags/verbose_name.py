from django import template
register = template.Library()


@register.simple_tag
def verbose_name(object, fieldname):
    return object._meta.get_field(fieldname).verbose_name
