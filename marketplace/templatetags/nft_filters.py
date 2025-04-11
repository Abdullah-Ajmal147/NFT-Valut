from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    
@register.filter
def format_crypto(value):
    try:
        value = float(value)
        if value >= 1:
            return f"{value:.2f}".rstrip('0').rstrip('.')
        else:
            return f"{value:.4f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return str(value)