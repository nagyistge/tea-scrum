'''
Created on 6 Jul 2012

@author: Ted
'''
from django import template

register = template.Library()

def parseretro(retro, sec):
    """ Return a section of the sprint retro text.
        @param retro: Sprint.retro as JSON text: {"good":"...","bad":"...","next":"..."}
        @param sec: which section, good, bad, or next. Can be 1,2, or 3 respectively.
        @return: string matching sec.
    """
    if not retro:
        return ''
    from django.utils import simplejson
    objs = simplejson.loads(retro)
    return objs.get({'1':'good','2':'bad','3':'next'}.get(sec,sec), '')

register.filter('parseretro', parseretro)
