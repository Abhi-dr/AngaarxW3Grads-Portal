from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Retrieve an item from a dictionary."""
    return dictionary.get(key)


@register.filter
def get_status_color(status):
    if status == 'Accepted':
        return 'success'  # Bootstrap success color
    elif status == 'Wrong Answer':
        return 'danger'  # Bootstrap danger color
    elif status == 'Pending':
        return 'warning'  # Bootstrap warning color
    elif status == 'Compilation Error':
        return 'danger'
    else:
        return 'secondary'  # Default color for other statuses
    
@register.filter
def is_solved_by_user(pod, user):
    
    if pod.is_solved_by_user(user):
        return True
    else:
        return False