# -*- coding: utf-8 -*-

from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.utils.log import getLogger
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from TeaScrum.sprint.models import Sprint
from TeaScrum.backlog.models import Backlog, Task
from models import Daily, ScrumEvent
from TeaScrum.utils import get_active_product, get_active_sprint, render, error_response

logger = getLogger('TeaScrum')

@login_required
def taskboard(request):
    """ Prepare for /daily/taskboard/ page.
        Team members view the sprint backlog items and their detailed tasks.
        The page consists of three columns: undone item tasks, on-hand tasks, finished tasks.
        Each row is an item, with tasks as labels (story, points,[who]).
        There is a burndown chart on the right-hand side of the page.
    """
    product = get_active_product(request)
    sprint = get_active_sprint(product)
    if not sprint:
        sps = product.sprint_set.get_query_set().filter(start__lte=datetime.now())
        if sps.count() > 0:
            sprint = sps[0]
    if sprint:
        sbacklog = sprint.backlog_set.get_query_set()
    else:
        sbacklog = None
    data = {'product': product, 'sprint': sprint, 'items': sbacklog}
    return render(request, 'taskboard', data, 'daily/')

@login_required
def dailyscrum(request):
    """ Prepare for /daily/scrum/ page.
        This is the interface for the daily scrum meeting.
        Before the meeting, team members can visit this page to enter the answers to the three typical questions as a reminder.
        During the meeting, the team can sit in front of their monitor looking at their answers to talk one by one.
        When anybody needs to select a task to do, she can switch to the tasks page and click on the interested task.
        Once selected, only the scrum master can make changes. The answers are saved in the Daily table.
    """
    product = get_active_product(request)
    if not product:
        return render(request, 'error', {'err':_('No product for you.')}, '')
    # get the latest active sprint
    sprint = get_active_sprint(product)
    if not sprint:
        sps = product.sprint_set.get_query_set().filter(start__lte=datetime.now())
        if sps.count() > 0:
            sprint = sps[0]
        else:
            return render(request, 'error', {'err':_('No sprint for the product.')}, '')
    daily = None
    dailys = Daily.objects.filter(sprint=sprint.pk,member=request.user)   #latest on top
    if len(dailys) > 0:
        daily = dailys[0]
    sbacklog = Backlog.objects.filter(sprint=sprint)
    data = {'product': product, 'sprint': sprint, 'daily': daily, 'items':sbacklog}
    return render(request, 'daily', data, 'daily/')

@login_required
def submit_daily(request):
    """ Team members submit daily questions for reminder.
        If daily record exists for today, update its content, else create a new record.
        Parameters: yesterday, today, problem, serious, spid.
    """
    spid = request.POST.get('spid', None)
    yesterday = request.POST.get('yesterday', '')
    today = request.POST.get('today','')
    problem = request.POST.get('problem','')
    serious = request.POST.get('serious', '3')
    try:
        sprint = Sprint.objects.get(pk=spid)
        product = sprint.product
        if not product.has_member(request.user):
            return HttpResponse('{"error":"%s"}' % _('Not a team member'))
        dailys = Daily.objects.filter(sprint=sprint,member=request.user)
        daily = None
        if len(dailys) > 0:
            daily = dailys[0]
            if daily.scrumdate.date() != datetime.now().date():
                daily = None
        if not daily:
            daily = Daily(product=product,sprint=sprint,member=request.user)
        daily.yesterday = yesterday
        daily.today = today
        daily.problem = problem
        daily.serious = int(serious)
        daily.save()
        return HttpResponseRedirect('/daily')
#        return HttpResponse('{"status":"OK"}')
    except Exception,e:
        logger.exception(e)
        return render(request, 'error', {"err":_('Save failed, retry later.')})
    
@login_required
def pick_task(request, tid=None):
    """ A team member picks a task to work on. This is an Ajax call.
        There should be a way to notify others that somebody picked a task.
        A simple way is to save this operation in a database table, and others
        using the same page will check it up and once applied will put a mark there
        so as not to repeat it. This can be done using a timestamp. Operations with timestamp
        later than the last visit time, will be applied, or else ignored.
    """
    if not tid:
        tid = request.REQUEST.get('tid', None)
    if tid:
        task = get_object_or_404(Task, pk=tid)
    else:
        logger.error('pick_task tid not given')
        return error_response(_('Task ID error'))
    if task.doer:
        return error_response(_('This task has been assigned to another member.'))
    try:
        task.assign(request.user)
    except Exception,e:
        logger.error('pick_task save() failed: %s'%e)
        return error_response(_('Failed to save, retry later.'))
    # notify others
    evt = ScrumEvent(user=request.user,object=tid)
    evt.save()
    return HttpResponseRedirect('/daily')

@login_required
def unpick_task(request, tid=None):
    """ Delevepor unselect a task and put it back to the unassigned status.
    """
    if not tid:
        tid = request.REQUEST.get('tid', None)
    task = get_object_or_404(Task, pk=tid)
    if not task.doer:
        logger.error('unpick_task(tid=%s), task.doer is None'%tid)
        return error_response(_('Task not assigned to anybody'))
    if task.doer != request.user:
        logger.warning('unpick_task(tid=%s), task.doer != request.user'%tid)
        return error_response(_('Not task doer'))
    try:
        task.unassign(request.user)
        return HttpResponseRedirect('/daily')
    except Exception,e:
        logger.error('unpick_task.save() failed: %s'%e)
        return error_response(_('Failed to save, retry later.'))
    
def check_event(timestamp, event_type='PICK'):
    evts = ScrumEvent.objects.filter(etype=event_type).filter(tstamp__gte=timestamp)
    return evts

def check_pick(request):
    """ daily page refreshes to see who picked a task to do.
        @return: [{"task":"taskid","user":"username"},..]
    """
    ts = request.session.get('CheckPickTime', datetime.now())
    evts = check_event(ts)
    request.session['CheckPickTime'] = datetime.now()
    rs = []
    for evt in evts:
        rs.append('{"task":"%s","user":"%s"}' % (evt.object, evt.user.username))
    return HttpResponse('[%s]' % ','.join(rs))

