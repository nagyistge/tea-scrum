# -*- coding: utf-8 -*-

""" Declaration of global Constants and utility routines. 
"""
from django.utils.translation import ugettext_lazy as _

STATUS_CHOICES = (
    ('OPENED',_('Opened')), ('STARTED',_('Started')), 
    ('RELEASED',_('Released')), ('CLOSED',_('Closed')), ('CANCELED',_('Canceled'))
    )

BACKLOG_STATUS_CHOICES = (
    ('NEW',_('New')), ('PRIORITIZED',_('Prioritized')),
    ('ESTIMATED',_('Estimated')), ('ASSIGNED',_('Assigned')),
    ('FINISHED',_('Finished')),
    )
