# -*- coding: utf-8 -*-

from django.db import models
from django.utils.log import getLogger
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

logger = getLogger('TeaScrum')

SEX_CHOICES = (('M',_('Male')),('F',_('Female')))
ROLE_CHOICES = (('D',_('Developer')), ('M', _('Scrum Master')), ('O', _('Product Owner')), ('A', _('Admin')))

class Staff(models.Model):
    """ User profile model.
    """
    user = models.OneToOneField(User, verbose_name=_('User ID'), primary_key=True)
    gender = models.CharField(_('Sex'), max_length=1, choices=SEX_CHOICES, default='M')
    birthday = models.DateField(_('Birthday'), blank=True, null=True)
    mobile = models.CharField(_('Mobile'), max_length=11, blank=True, null=True)
    address = models.CharField(_('Address'), max_length=64, blank=True, null=True)
    im = models.CharField(_('Instant Messenger'), max_length=16, blank=True, null=True)
    headshot = models.ImageField(upload_to='/tmp', null=True, blank=True, verbose_name=_('Thumbnail photo'))
    role = models.CharField(_('Role'), max_length=3, choices=ROLE_CHOICES, default='D')
    product = models.IntegerField(_('Active Product'), default=0, help_text=_('Selected active product'))
    level = models.IntegerField(_('Level'), default=0, help_text=_('Gamified indicator'))
    points = models.IntegerField(_('Points'), default=0, help_text=_('XP points for sth, gamification'))
    stars = models.IntegerField(_('Stars'), default=0, help_text=_('Stars the company gave'))
    credits = models.IntegerField(_('Credits'), default=0, help_text=_('Credits earned from contribution and spendable'))
    hearts = models.IntegerField(_('Hearts'), default=0, help_text=_('Number of hearts others gave'))
    notes = models.TextField(_('Notes'), blank=True, null=True, help_text=_('A sticky note for writing anything'))
    online = models.BooleanField(_('Online'), editable=False, default=False, help_text=_('Whether this user is online'))
    skills = models.ManyToManyField('Skill')

    def __unicode__(self):
        return '%s %s(%s)' % (self.user.first_name, self.user.last_name, self.user.username)

    def is_owner(self):
        return 'O' in self.role
    
    def is_master(self):
        return 'M' in self.role
    
    def is_owner_or_master(self):
        return 'O' in self.role or 'M' in self.role

# this will ensure a Staff entity is created automatically when calling User.profile property.
User.profile = property(lambda u: Staff.objects.get_or_create(user=u)[0])

class Team(models.Model):
    """ A Team entity matches a Group entity.
    """
    group = models.OneToOneField(Group, verbose_name=_('Group Link'), primary_key=True)
    velocity = models.FloatField(_('Velocity'), default=10)
    points = models.IntegerField(_('Points'), default=0, help_text=_('Points'))
    stars = models.IntegerField(_('Stars'), default=0, help_text=_('Stars the company gave to the team'))
    credits = models.IntegerField(_('Credits'), default=0, help_text=_('Credits earned from contribution and spendable'))
    intro = models.TextField(_('Introduction'), blank=True, null=True)
    
    def __unicode__(self):
        return 'Team %s' % self.group.name
    
    @property
    def name(self):
        return self.group.name
    
    @property
    def members(self):
        return self.group.user_set
    
Group.profile = property(lambda g: Team.objects.get_or_create(group=g)[0])

class Skill(models.Model):
    """ Skill.
    """
    name = models.CharField(_('Skill name'), max_length=40)
    intro = models.TextField(_('Introduction'), null=True, blank=True)
    
    def __unicode__(self):
        return '%s' % self.name
    