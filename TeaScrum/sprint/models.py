# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.log import getLogger
from TeaScrum import STATUS_CHOICES
from TeaScrum.product.models import Product

logger = getLogger('TeaScrum')

class Sprint(models.Model):
    """ Sprint or iteration about a timeboxed period for the team to implement a part of the product.
        number is the sequence of sprints from #1 onwards.
        goal is a short message about what to achieve at the end of this sprint.
        Default timebox is specified as 2 weeks (10 days).
        start date is given by master and end date equals start date plus timebox and weekends (2 days).
        demotime is a date and time at sprint review to show the product demo for the sprint.
        dailytime and room specify time and room for the daily scrum.
        estimate is the sum of all estimates of the stories collected to be done in this sprint.
        actual is the actual mandays calculated from tasks at the end of the sprint. These two will be used to calculate velocity of next sprint.
        retro contains a long text keeping what the team says about the good, bad and advice at retrospective meeting.
    """
    product = models.ForeignKey(Product, verbose_name=_('Product ID'))
    number = models.CharField(_('Number'), max_length=10, help_text=_('Sprint sequence number, a string up to 10 characters'))
    goal = models.CharField(_('Sprint goal'), max_length=128, help_text=_('A brief goal of this sprint'))   #describe the target result
    master = models.ForeignKey(User, related_name='sprints_mastered', verbose_name=_('Scrum Master'), help_text=_('Who is the scrum master of this sprint')) #scrum master
    timebox = models.IntegerField(_('Timebox'), default=10, help_text=_('Iteration timebox eg 10 days'))
    start = models.DateTimeField(_('Start date'), null=True, help_text=_('When this sprint starts, format: YY-mm-dd'))
    end = models.DateTimeField(_('End date'), null=True, help_text=_('Should be start + timebox + weekends'))
    demotime = models.DateTimeField(_('Demo datetime'), null=True, help_text=_('When to do sprint review and demo'))
    dailytime = models.CharField(_('Daily scrum time'), max_length=5, null=True, default='9:30', help_text=_('What time to hold daily scrum everyday'))
    dailyroom = models.CharField(_('Daily scrum room'), max_length=10, null=True, blank=True, help_text=_('Room for daily scrum'))
    estimate = models.FloatField(_('Estimates from backlog'), default=0, null=True, help_text=_('Estimated mandays of all story estimates in this sprint'))
    actual = models.FloatField(_('Actual mandays when done'), default=0, null=True, editable=False, help_text=_('Calculated mandays at the end of the sprint'))
    review = models.TextField(_('Review'), null=True, blank=True, help_text=_('Summary/minutes of the sprint review meeting'))
    retro = models.TextField(_('Retrospective'), null=True, blank=True, help_text=_('At review meeting, enter good, bad and advice from all members'))
    memo = models.TextField(_('Memo'), null=True, blank=True, help_text=_('Keep a record of item/task edits with mandays changes'))
    meeting = models.DateTimeField(_('Meeting start time'), editable=False, null=True, blank=True, help_text=_('Sprint meeting start time, NULL if ended'))
    status = models.CharField(_('Status'), max_length=8, choices=STATUS_CHOICES, default='OPENED', help_text=_('sprint status'))
    
    def __unicode__(self):
        return u'#%s' % self.number
        
    class Meta:
        db_table = 'scrum_sprint'
        verbose_name = _('Sprint')
        verbose_name_plural = _('Sprints')
        ordering = ('-start',)
    
    def gen_burndown_data(self):
        """ Generate burn-down dataset for the sprint.
            X-axis contains the dates from start of the sprint to the end or today.
            Weekends are excluded.  TODO: Public holidays should be excluded. Holidays should be available from a calendar
            Y-axis contains sum of remaining estimates of all backlog items up to the date on X-axis.
            Y-value@X-axis = sum of all backlog item estimates - sum of finished item estimates by this date
            Return dataset: [[month, day, Y-value],...]
        """
        # calculate sum of all backlog item estimates, and estimates of finished items on each date
        total_est = 0.0
        item_estimates = {} #{'2012-01-01': 12.5,...} #[['2012-01-01',4.5],...]
        for itm in self.backlog_set.get_query_set():
            itp = itm.date_points() #finished tasks ['2012-01-01', 4.5]
            total_est += itp[1]
            if itp[0] in item_estimates:
                item_estimates[itp[0]] += itp[1]
            else:
                item_estimates[itp[0]] = itp[1]
        # gen list of dates from self.start to self.end or today
        dt = self.start
        xdates = []
        while True:
            xdates.append([datetime.strftime(dt, '%Y-%m-%d')])
            dt += timedelta(days=1)
            if dt > datetime.now() or self.end and dt > self.end:
                break
        # populate xdates with remaining estimates
        remaining = total_est
        for xd in xdates:
            ie = item_estimates.get(xd, 0)
            
            
    def burndown_data(self):
        """ [[month,day,points_done],..] for the Sprint backlog items.
            Dates may repeat, ie, more tasks finish on the same day. 
            Dates must be sorted, and task points accumulated later for burnup chart.
        """
        pts = []
        # collect date and estimate points of each task in the backlog items.
        for itm in self.backlog_set.get_query_set():
            pts.extend(itm.date_points())
        if not pts:
            return []
        # sort by date
        logger.debug('Sprint.burndown_data():pts=%s'%pts)
        pts.sort()
        last = datetime.strptime(pts[-1][0],'%Y-%m-%d')
        # accumulate points and if date duplicated, merge points
        logger.debug('Sprint.burndown_data():last=%s'%last)
        ptd = {}
        n = 0
        for dt, pt in pts:
            n += pt
            ptd[dt] = self.estimate - n #for burndown chart
        # fill the whole x-axis from sprint.start to last
        d = self.start
        data = [[d.month,d.day,self.estimate]]
        logger.debug('Sprint.burndown_data():ptd=%s,d=%s,data=%s,end=%s' % (ptd,d,data,self.end))
        while d < self.end:
            logger.debug('d=%s, end=%s'%(d, self.end))
            d += timedelta(days=1)
            if d > last:
                n = -1
            else:
                n = ptd.get(str(d.date()), data[-1][2])
            data.append([d.month, d.day, n])
        logger.debug('Sprint.burndown_data():Leave burndown_data, data=%s'%data)
        return data or []
