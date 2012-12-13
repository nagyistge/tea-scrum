from django import template

register = template.Library()

def rolename(role):
    """ Return the name of a role id.
        (('D',_('Developer')), ('M', _('Scrum Master')), ('O', _('Product Owner')), ('A', _('Admin')))
        If role not found, return role.
    """
    from TeaScrum.staff.models import ROLE_CHOICES
    for rid, name in ROLE_CHOICES:
        if rid == role:
            return name
    return role

def sexname(sex):
    """ Return the sex name for the code M|F. """
    from TeaScrum.staff.models import SEX_CHOICES
    for sid, name in SEX_CHOICES:
        if sid == sex:
            return name
    return sex

register.filter('rolename', rolename)
register.filter('sexname', sexname)
