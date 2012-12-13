# -*- coding: utf-8 -*-

from datetime import datetime
from django.db import models
from django.db.models import Count
#from django.utils.translation import ugettext_lazy as _

class BacklogManager(models.Manager):
    """ Manager of Backlog entities.
    """
    def update_sprint(self, spid, items):
        self.get_query_set().filter(pk__in=items).update(sprint=spid)
        
    def group_by_status(self, product):
        """ Group by status.
            @return: [{"status":"NEW","id__count":10},..]
        """
        return self.get_query_set().filter(product=product).values('status').annotate(Count('id'))
    
class TaskManager(models.Manager):
    """ Manager of model SprintTask
    """
    def query_by_user(self, user, product=None):
        """ Query by user and product.
        """
        if product:
            return self.get_query_set().filter(doer=user,item__product=product).order_by('-start')
        return self.get_query_set().filter(doer=user).order_by('-start')
    
#    def get_tasks3(self):
    def group_by_status(self, product):
        """ Get all tasks and separate them into a list of undone, doing, and done list.
        """
        cs = [[],[],[]]
        for t in self.tasks.get_query_set():
            if t.end:
                cs[2].append(t)
            elif t.start:
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
            if t.end:
                pts.append([datetime.strftime(t.end,'%Y-%m-%d'), t.estimate])
        return pts

class HierarchyManager(models.Manager):
    """ Manager of model Hierarchy.
    """
    def query_root(self, product):
        return self.get_query_set().filter(product=product,parent=None)
    
    def query_children(self, parent):
        return self.get_query_set().filter(parent=parent)
    