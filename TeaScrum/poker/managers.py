# -*- coding: utf-8 -*-

from django.db import models
from django.utils.log import getLogger

logger = getLogger('TeaScrum')

class VoteManager(models.Manager):
    """ Manager class for Vote.
    """
    def get_queryset(self, product=None):
        """ Get a list of Vote entities for the specified product.
            Return all if product is None.
        """
        if not product:
            return self.get_query_set()
        else:
            return self.get_query_set().filter(product=product)
        
    def clear(self, product=None):
        """ Delete all records in Vote.
        """
        self.get_queryset(product).delete()
        
    def start(self, user, product=None):
        """ Start a new voting session. Returning a session id.
        """
        import uuid
        self.clear(product)
        sid = uuid.uuid4().hex
        self.get_query_set().create(session=sid, product=product, voter=user, chair=True)
        return {'sid':sid}
    
    def stop(self, product, session):
        """ Stop the session.
        """
        self.get_query_set().filter(product=product,session=session).update(status='CLOSED')

    def status(self, product=None):
        """ Get the voting status of the product.
            Status is determined by the session creator whose chair is True.
            @return: Session not started: {"status":"IDLE"}
                Session expired: {"status":"EXPIRED"} after 24 hours
                Session started: {"status":"STARTED"}
                Session closed: {"status":"CLOSED"}
        """
        qs = self.get_queryset(product).filter(chair=True)
        if qs.count() == 0:
            return {'status':'IDLE'}
        q = qs[0]
        if q.expired():
            return {'status':'EXPIRED'}
        return {'status':q.status,'sid':q.session}
    
    def count(self, product=None, session=None):
        """ Count number of voters for the session.
        """
        if not session:
            return self.get_queryset(product).count()
        else:
            return self.get_queryset(product).filter(session=session).count()
        
    def collect(self, product=None, session=None):
        """ Collect all user votes for the session.
        """
        if not session:
            return self.get_queryset(product)
        else:
            return self.get_queryset(product).filter(session=session)
        
    def average(self, product=None, session=None):
        """ Average the votes for the session.
            @return: {'vote__avg': 0}
        """
        from django.db.models import Avg
        if not session:
            return self.get_queryset(product).filter(session=session).aggregate(Avg('vote'))
        else:
            return self.get_queryset(product).aggregate(Avg('vote'))
    