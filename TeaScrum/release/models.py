# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from TeaScrum.product.models import Product

class ReleasePlan(models.Model):
    """ Release planning based on MuSCow specification. Each release has a record.
        release end date is calculated, but needs a discussion with the team.
        After a release is planned, a date countdown will be started on the product page, & wall.
        A release number has three parts: major.minor.build, eg. 0.8.123, 1.2.0.
        The estimates field keeps the sum of estimates of all selected items in the Backlog. This number may change if sprint backlog is modified.
        The progress field saves a history of date and points done by the system. It is saved with each sprint and used to produce burndown chart.
    """
    product = models.ForeignKey(Product, verbose_name=_('Product ID'))
    version = models.CharField(_('Version'), max_length=32, help_text=_('Major.Minor, eg. 1.18'))
    must = models.IntegerField(_('Must have'), help_text=_('Estimate > this number MUST be included'))
    should = models.IntegerField(_('Should have'), help_text=_('Estimate > this SHOULD be included'))
    could = models.IntegerField(_('Could have'), help_text=_('Estimate > this COULD be included'))
    wont = models.IntegerField(_('Wont have'), help_text=_('Estimate < this WONT be considered'))
    major = models.CharField(_('Major number'), max_length=10, help_text=_('Current major release number'))
    minor = models.CharField(_('Minor number'), max_length=10, help_text=_('Current minor release number'))
    build = models.CharField(_('Build number'), max_length=10, help_text=_('Current build number'))
    start = models.DateField(_('Start date'), blank=True, null=True, help_text=_('Start date of this release plan'))
    release = models.DateField(_('Release Date'), blank=True, null=True, help_text=_('Calculated release date based the above'))
    estimates = models.IntegerField(_('Total estimates'), default=0, help_text=_('Sum of all estimates for the selected items'))
    progress = models.TextField(_('Progress'), blank=True, help_text=_('Keep a record of date,estimates done'))

    class Meta:
        db_table = 'scrum_releaseplan'
        verbose_name = _('ReleasePlan')
        verbose_name_plural = _('ReleasePlans')
        ordering = ('-start',)
        
    def __unicode__(self):
        return '[Release Plan v%s] %s' % (self.version, self.product.name)
    