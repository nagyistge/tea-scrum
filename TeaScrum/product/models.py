# -*- coding: utf-8 -*-
from django.db import models
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.log import getLogger
from TeaScrum import STATUS_CHOICES
from TeaScrum.staff.models import Team

logger = getLogger('TeaScrum')

class ProductManager(models.Manager):
    """ Manager class for model Product.
    """
    def query_by_user(self, usr):
        """ Query all products the user has participated, ie., 
            user is a member of the product team. The list is sorted by start date in descending order.
            @param usr: User instance
        """
        return Product.objects.filter(team__in=[g['id'] for g in usr.groups.values()]).order_by('-start')
        
class Product(models.Model):
    """ The model of a scrum product or project.
        TeaScrum can handle multiple products at the same time.
    """
    name = models.CharField(_('Product Name'), max_length=64, help_text=_('Name of the Product'))   #1st = verbose_name
    category = models.CharField(_('Category'), max_length=8, blank=True, help_text=_('Product category'))
    vision = models.TextField(_('Product Vision'), help_text=_('Product vision and mission'))
    owner = models.ForeignKey(User, related_name='products_owned', verbose_name=_('Product Owner'), help_text=_('Select a Product Owner')) #Product owner
    master = models.ForeignKey(User, related_name='products_mastered', verbose_name=_('Scrum Master'), help_text=_('Select a Scrum Master')) #ScrumMaster
    team = models.ForeignKey(Team, verbose_name=_('Team/Group'), help_text=_('Select a Team/Group'))
    start = models.DateTimeField(_('Start Date'), blank=True, null=True, db_index=True, help_text=_('Start datetime of the product development'))
    end = models.DateTimeField(_('End Date'), blank=True, null=True, help_text=_('End datetime of the product development'))
    timebox = models.IntegerField(_('Timebox'), default=10, help_text=_('Number of days per iteration/sprint'))    #5 days a week for sprint, 2 weeks
    status = models.CharField(_('Status'), max_length=8, choices=STATUS_CHOICES, default='Opened', help_text=_('Current state of the product'))

    objects = ProductManager()
    
    class Meta:
        db_table = 'scrum_product'
        verbose_name = _('Scrum Product')
        verbose_name_plural = _('Scrum Products')
        ordering = ('-start',)
        
    def __unicode__(self):
        return self.name
        
    def owner_or_master(self, user):
        """ Test whether user is the product owner or scrum master for this product.
        """
        return user == self.owner or user == self.master
    
    def has_member(self, user):
        """ Test whether user is a team member.
        """
        if not (self.team and user):
            return False
        return user.groups.get_query_set().filter(pk=self.team.pk)
    
class ProductForm(ModelForm):
    class Meta:
        model = Product
        exclude = ('owner')
        