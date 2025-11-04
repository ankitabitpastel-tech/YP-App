from django import template
import hashlib

register = template.Library()

@register.filter
def md5(value):
    return hashlib.md5(str(value).encode()).hexdigest()