import re
from django import template

register = template.Library()


@register.filter
def clean_text(value):
    return re.sub(r'\[[^\]]*\]', '', str(value)).strip()
