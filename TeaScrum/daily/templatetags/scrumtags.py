'''
Created on 6 Jul 2012

@author: Ted
'''
from django import template

register = template.Library()

def percents(v):
    """ Convert a decimal into a percentage string like 98%
    """
    return '%3.0f%%' % (100. * v)

register.filter('percents', percents)
