# -*- coding: utf-8 -*-
#from datetime import datetime, timedelta
from django.db import models
#from django.forms.extras.widgets import SelectDateWidget
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.log import getLogger
from TeaScrum.product.models import Product
from TeaScrum.sprint.models import Sprint
#from TeaScrum.backlog.models import Backlog
#from TeaScrum import BACKLOG_STATUS_CHOICES
#from managers import TaskManager

logger = getLogger('TeaScrum')
        
class Daily(models.Model):
    """ Collection of daily scrum.
        This table can be used to let team members write a diary before daily scrum about the summary
        of what has been done yesterday, and what to do today, and what problem there is and how serious.
    """
    product = models.ForeignKey(Product, verbose_name=_('Product ID'))
    member = models.ForeignKey(User, verbose_name=_('Team member'))
    sprint = models.ForeignKey(Sprint, verbose_name=_('Sprint ID'))
    scrumdate = models.DateTimeField(_('Todays date'), auto_now_add=True, help_text=_('Auto added date'))
    yesterday = models.TextField(_('Done yesterday'), blank=True, help_text=_('What has been done yesterday?'))
    today = models.TextField(_('Will do today'), blank=True, help_text=_('What to do today?'))
    problem = models.TextField(_('Problem'), blank=True, help_text=('Any difficulties?'))
    serious = models.IntegerField(_('Severity'), default=3, help_text=_('How serious the problem is? 1-5'))
    
    class Meta:
        db_table = 'scrum_daily'
        verbose_name = _('Daily Scrum')
        verbose_name_plural = _('Daily Scrums')
        ordering = ('-scrumdate',)
        
    def __unicode__(self):
        return 'DailyScrum %s' % (self.scrumdate)
    
class ScrumEvent(models.Model):
    """ General events as notifications about task assignment etc.
    """
    user = models.ForeignKey(User, verbose_name=_('User ID'), help_text=_('Who posted this event'))
    etype = models.CharField(_('EventType'), max_length=10, default='PICK', help_text=_('Type of event or action'))
    tstamp = models.DateTimeField(_('Timestamp'), auto_now_add=True, help_text=_('Exact time of event'))
    object = models.CharField(_('Object'), max_length=16, blank=True, help_text=_('Object like task_id'))

    class Meta:
        ordering = ('-tstamp',)
