# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from managers import VoteManager

VOTING_CHOICES = (('IDLE',_('Not Voting')), ('STARTED',_('Voting')), ('CLOSED', _('Voting closed')))

class Vote(models.Model):
    """ Vote entity for a voting session of the planning poker game.
        This is a temporary dataset valid for a particular session.
        When a new session is started, the old data should be deleted.
    """
    session = models.CharField(_('Session ID'), max_length=32) # use session to associate a topic with a session_id
    product = models.IntegerField(_('Product ID'))
    voter = models.ForeignKey(User, verbose_name=_('Voter User ID'))
    chair = models.BooleanField(_('Chairperson or not'), default=False)
    status = models.CharField(_('Status'), max_length=8, default='STARTED', choices=VOTING_CHOICES)
    vote = models.CharField(_('Vote number'), max_length=8, default='*')
    tstamp = models.DateTimeField(_('Timestamp'), auto_now_add=True)
    
    objects = VoteManager()
    
    class Meta:
        db_table = 'scrum_vote'
        verbose_name = _('Vote')
        verbose_name_plural = _('Votes')
        ordering = ('-tstamp',)

    def closed(self):
        return self.status == 'CLOSED'

    def expired(self):
        """ If timestamp of this vote is 24 hours ago, it is regarded as expired.
        """
        from datetime import datetime
        return (datetime.now() - self.tstamp).days > 0
    