# -*- coding: utf-8 -*-

from datetime import datetime
from django.db import models
from django.db.models import Count
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.log import getLogger
from TeaScrum import BACKLOG_STATUS_CHOICES
from TeaScrum.product.models import Product
from TeaScrum.sprint.models import Sprint
from managers import BacklogManager, TaskManager, HierarchyManager

logger = getLogger('TeaScrum')

MUSCOW_CHOICES = (('M',_('Must')),('S',_('Should')),('C',_('Could')),('W',_('Would')))

class Backlog(models.Model):
    """ Product/Sprint backlog contains a collection of user stories built by the product manager from customers.
        Initial data include story - a short sentence to describe the requirement, priority -
        importance of the requirement from lowest 0 up with an interval of 10, ie., 0, 10, 20, .. 100, ..
        Product backlog items are displayed with highest priority on the top and should be picked to
        be implemented first by the team.
        Discussions on priority,points be done later.
        category can be any segmentation of the features, such as 'CORE','Bug', etc.
    """
    product = models.ForeignKey(Product, verbose_name=_('Product ID'))
    story = models.CharField(_('User Story'), max_length=80, help_text=_('A brief statement of the required feature'))
    category = models.CharField(_('Category'), max_length=16, null=True, blank=True, help_text=_('Like core, extra, bugfix, alternative, improvement, etc'))
    priority = models.IntegerField(_('Priority'), default=50, help_text=_('Priority from 10, 20, .. larger means higher'))
    muscow = models.CharField(_('MuSCoW'), max_length=1, default='M', choices=MUSCOW_CHOICES, help_text=_('Must, Should, Could, Would'))
    parent = models.ForeignKey('Hierarchy', verbose_name=_('Group Node'), null=True, editable=False, help_text=_('Group stories into hierarchical structure'))
    logtime = models.DateTimeField(_('Log time'), editable=False, auto_now_add=True, help_text=_('Date and time this feature is added'))
    requestor = models.CharField(_('Requestor'), max_length=16, null=True, blank=True, help_text=_('Who requested this feature'))
    estimate = models.FloatField(_('Estimated mandays'), default=0, help_text=_('Estimated story points/mandays or sum of its task estimates'))
    status = models.CharField(_('Status'), max_length=12, choices=BACKLOG_STATUS_CHOICES, default='NEW', help_text=_('Current Status of implementation'))
    notes = models.TextField(_('Notes'), null=True, blank=True, help_text=_('Details and notes about the user story, result of planning'))
    sprint = models.ForeignKey(Sprint, verbose_name=_('Sprint ID'), editable=False, null=True, help_text=_('Which sprint this item is assigned to'))
    start = models.DateTimeField(_('Start time'), editable=False, null=True, help_text=_('Start date of this item, 1st task picked'))
    end = models.DateTimeField(_('End time'), editable=False, null=True, help_text=_('End date of this item, last task done'))
    demos = models.TextField(_('Demo How-To'), null=True, blank=True, help_text=_('Specify how to demo this feature for Sprint review'))
    percent = models.FloatField(_('Percent complete'), editable=False, default=0, null=True, help_text=_('How much finished, calculated based on task points'))
    actual = models.FloatField(_('Actual mandays'), editable=False, default=0, null=True, help_text=_('How much mandays actually used, calculated at end from tasks'))

    objects = BacklogManager()

    class Meta:
        db_table = 'scrum_backlog'
        verbose_name = _('Backlog')
        verbose_name_plural = _('Backlogs')
        ordering = ('-priority',)
        
    def __unicode__(self):
        return self.story
    
    def get_tasks3(self):
        """ Get all tasks and separate them into a list of undone, doing, and done list.
            The status values are NEW, ASSIGNED, and FINISHED respectively.
        """
        cs = [[],[],[]]
        for t in self.tasks.get_query_set():
            if t.status == 'FINISHED':
                cs[2].append(t)
            elif t.status == 'ASSIGNED':
                cs[1].append(t)
            else:
                cs[0].append(t)
        return cs
    
    def date_points(self):
        """ [['date',task_pts],..] for the finished tasks in SprintTask.
            Dates may repeat, ie, more tasks finish on the same day. task points need accumulate later for burnup chart.
        """
        pts = []
        for t in self.tasks.get_query_set():
            if t.status == 'FINISHED':
                pts.append([datetime.strftime(t.end,'%Y-%m-%d'), t.estimate])
        return pts

class Task(models.Model):
    """ Task model for a Backlog item.
        A backlog item (user story) can have a list of tasks for developers to implement.
        The technologies should be predefined so that the team can build their skill experiences based on this.
    """
    item = models.ForeignKey(Backlog, related_name='tasks', verbose_name=_('Product/Sprint backlog item ID'))
    order = models.FloatField(_('Sequence number'), default=0, help_text=_('Task sequence number'))
    name = models.CharField(_('Task name'), max_length=80, help_text=_('Brief task sentence'))
    technology = models.CharField(_('Technology'), max_length=64, null=True, blank=True, help_text=_('Technology such as HTML, Python, etc'))
    notes = models.TextField(_('Task details'), null=True, blank=True, help_text=_('A detailed description of the task'))
    estimate = models.FloatField(_('Estimated mandays'), null=True, help_text=_('Estimated story points/mandays'))
    doer = models.ForeignKey(User, verbose_name=_('Developer'), editable=False, null=True, help_text=_('Team member who picks this task to do'))
    status = models.CharField(_('Status'), max_length=10, default='NEW', choices=BACKLOG_STATUS_CHOICES, help_text=_('Estimated, Started, Finished, Reviewed'))
    start = models.DateTimeField(_('Start time'), null=True, help_text=_('Start time of this task picked'))
    end = models.DateTimeField(_('End time'), null=True, help_text=_('End time of this task done'))
    actual = models.FloatField(_('Actual mandays'), editable=False, default=0, null=True, help_text=_('Calculated mandays at end'))
    
    objects = TaskManager()
    
    def __unicode__(self):
        return self.name
    
    def assign(self, user, save=True):
        """ Assign user as the task doer/developer.
        """
        product = self.item.product
        if not product.has_member(user):
            raise Exception(_('Not a team member'))
        self.doer = user
        self.start = datetime.now()
        self.status = 'ASSIGNED'
        if save:
            self.save()

    def unassign(self, user, save=True):
        """ Remove assigned doer by herself.
        """
        if self.doer != user:
            raise Exception(_('Permission denied'))
        self.doer = None
        self.status = 'ESTIMATED'
        if save:
            self.save()
            
    class Meta:
        db_table = 'scrum_task'
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')
        ordering = ('order',)

class Hierarchy(models.Model):
    """ A tree structure to organise the backlog items for hierarchical manipulation.
        Every backlog item has a node field to point to a record in this dataset, and
        each entity in Hierarchy has a parent link to form the tree structure.
        The root node has a NULL parent.
    """
    product = models.ForeignKey(Product, verbose_name=_('Product ID'))
    name = models.CharField(_('Group Name'), max_length=80, help_text=_('Name of this group of backlog items'))
    order = models.CharField(_('Display order'), max_length=8, null=True, blank=True, help_text=_('Like 1, 1.5, 1.5.1, 2, 3, ..'))
    style = models.CharField(_('Display style'), max_length=128, null=True, blank=True, help_text=_('can be CSS styles'))
    parent = models.ForeignKey('self', verbose_name=_('Parent node'), null=True, help_text=_('Can be NULL for root node'))

    objects = HierarchyManager()
    
    def __unicode__(self):
        return '%s' % self.name
    
    class Meta:
        ordering = ('order',)
        