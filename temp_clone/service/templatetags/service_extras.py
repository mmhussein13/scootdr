from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """
    Splits the value on arg and returns a list
    Usage: {{ value|split:"," }}
    """
    return value.split(arg)

@register.filter
def get_range(value):
    """
    Returns a range of numbers from 1 to value
    Usage: {% for i in 5|get_range %}
    """
    return range(1, int(value) + 1)

@register.filter
def truncate_words_start(value, arg):
    """
    Truncates a string after specified number of words from the start
    Usage: {{ value|truncate_words_start:5 }}
    """
    words = value.split()
    try:
        limit = int(arg)
    except ValueError:
        limit = 5
    
    if len(words) <= limit:
        return value
    
    return ' '.join(words[:limit])

@register.filter
def truncate_words_middle(value, arg):
    """
    Returns a portion of text from the middle of a string
    Usage: {{ value|truncate_words_middle:5 }}
    """
    words = value.split()
    try:
        limit = int(arg)
        start = limit
    except ValueError:
        limit = 5
        start = 5
    
    if len(words) <= start + limit:
        return ''
    
    return ' '.join(words[start:start+limit])

@register.filter
def truncate_words_end(value, arg):
    """
    Returns a portion of text from the end of a string
    Usage: {{ value|truncate_words_end:5 }}
    """
    words = value.split()
    try:
        limit = int(arg)
    except ValueError:
        limit = 5
    
    if len(words) <= limit * 2:
        return ''
    
    return ' '.join(words[-limit:])