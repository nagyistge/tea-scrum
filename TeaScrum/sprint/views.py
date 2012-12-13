# -*- coding: utf-8 -*-

from datetime import datetime
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext as _
from django.utils.log import getLogger
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from TeaScrum.product.models import Product
from TeaScrum.backlog.models import Backlog, Task
from TeaScrum.utils import render, get_active_product, error_response, get_velocity
from models import Sprint
from forms import SprintEditForm

logger = getLogger('TeaScrum')

class SprintListView(ListView):
    context_object_name = "sprint_list"
    template_name = "sprint/sprint_list.html"
    
    def get_queryset(self):
        """ Get a queryset of all sprints for a product.
            Product ID can be specified with either url kwargs['pid'] or GET parameter ?pid=n.
            If not given, current active product in session is used.
        """
        pid = self.kwargs.get('pid', None)
        if not pid:
            pid = self.request.GET.get('pid', None)
        if pid:
            self.product = get_object_or_404(Product, pk=pid)
        else:
            self.product = get_active_product(self.request)
        return self.product.sprint_set.get_query_set()
    
    def get_context_data(self, **kwargs):
        context = super(SprintListView, self).get_context_data(**kwargs)
        context['product'] = self.product
        return context
    
class SprintBacklogView(ListView):
    context_object_name = "backlog"
    template_name = "sprint/sprint_backlog.html"

    def get_queryset(self):
        #usr = self.request.user
        self.sprint = get_object_or_404(Sprint, pk=self.kwargs['pk'])
        return Backlog.objects.filter(sprint=self.sprint)

    def get_context_data(self, **kwargs):
        context = super(SprintBacklogView, self).get_context_data(**kwargs)
        context['sprint'] = self.sprint
        context['product'] = self.sprint.product
        context['velocity'] = get_velocity(self.sprint.product)
        return context

@permission_required('sprint.add_sprint')
def edit_sprint(request, sid=None, pid=None):
    """ Add a new Sprint entity or edit an existing one.
    """
    if pid:
        product = get_object_or_404(Product, pk=pid)
    else:
        product = get_active_product(request)
    if not product.owner_or_master(request.user):
        return render(request, 'error', {'err':_('Permission denied')})
    if sid:
        sprint = get_object_or_404(Sprint, pk=sid)
        if sprint.product != product:
            logger.error('edit_sprint, sprint %s not belong to active product'%sid)
            return render(request, 'error', {'err':_('Not active product')})
    else:
        sprint = None
    if request.method == 'POST':
        form = SprintEditForm(request.POST, instance=sprint)
        if form.is_valid():
            sp = form.save(commit=False)
            if not hasattr(sp, 'product'):
                setattr(sp, 'product', product)
            if not hasattr(sp, 'master'):
                setattr(sp, 'master', request.user)
            sp.save()
            form.save_m2m()
            return HttpResponseRedirect('/sprint/%s' % sid or form.cleaned_data['pk'])
        logger.debug('edit_sprint invalid form')
    else:
        form = SprintEditForm(instance=sprint)
    params = {'form':form, 'sid':sid, 'product':product, 'sprint':sprint}
    return render(request, 'sprint_edit', params, 'sprint/')
    
@permission_required('sprint.delete_sprint')
def remove_sprint(request, sid):
    """ Remove Sprint entity by ID.
        User permission: delete_sprint, and must also be scrum master for this sprint.
    """
    if not sid:
        return render(request, 'error', {'err':'No sid'})
    product = get_active_product(request)
    if not product.owner_or_master(request.user):
        return render(request, 'error', {'err':_('Permission denied')})
    try:
        sp = get_object_or_404(Sprint, pk=sid)
        if sp.product != product:
            logger.error('remove_sprint, sprint %s not belong to active product'%sid)
            return render(request, 'error', {'err':_('Not active product')})
        if sp.master != request.user:
            return render(request, 'error', {'err':_('Permission denied')})
        sp.delete()
    except Exception,e:
        logger.error('sprint.views.remove_sprint(%s) error: %s' % (sid, e))
    return HttpResponseRedirect('/sprint/')
        
@permission_required('sprint.change_sprint')
def select_backlog(request, sid):
    """ Select a group of backlog items to fit in the sprint timebox based on the team velocity.
        Velocity is passed as argument or fetched from the team or global settings.
    """
    vs = request.GET.get('v', None)
    if not vs:
        velocity = get_velocity(get_active_product(request))
    else:
        velocity = float(vs)
    est = 0.0
    items = []
    sp = get_object_or_404(Sprint, pk=sid)
    # collect existing sprint backlog items
    for itm in sp.backlog_set.get_query_set():
        est += itm.estimate
        if est > velocity:
            # remove if overruns velocity
            itm.sprint = None
            itm.save()
        else:
            items.append(itm)
    if est < velocity:
        # add more if velocity allows
        for itm in Backlog.objects.filter(sprint=None):
            est += itm.estimate
            if est > velocity:
                break
            items.append(itm)
            itm.sprint = sp
            itm.save()
    data = {'backlog':items, 'sprint':sp, 'product':sp.product}
    return render(request, 'sprint_backlog', data, 'sprint/')

@permission_required('sprint.change_sprint')
def include_backlog(request, sid, bid):
    """ Include a backlog item into this sprint.
        If this item is assigned to another sprint, returns an error.
        User permission: change_sprint and must be scrum master of the sprint.
    """
    try:
        bitem = get_object_or_404(Backlog, pk=bid)
        if bitem.sprint:
            logger.error('include_backlog(sid=%s,bid=%s), item already assigned to %s'%bitem.sprint)
            return error_response(_('This item is already assigned to another sprint'))
        sprint = get_object_or_404(Sprint, pk=sid)
        if sprint.master != request.user:
            logger.error('include_backlog() user Not sprint master')
            return error_response(_('Permission denied'))
        bitem.sprint = sprint
        bitem.save()
    except Exception, e:
        logger.error('include_backlog(sid=%s,bid=%s) failed:%s' % (sid,bid,e))
        return error_response(_('Error saving backlog item in the sprint.'))
    return HttpResponseRedirect('/sprint/%s/backlog'%sid)

@permission_required('sprint.change_sprint')
def exclude_backlog(request, sid, bid):
    """ Remove a backlog item from this sprint.
        User permission: change_sprint, and must be scrum master of the sprint.
    """
    try:
#        sprint = get_object_or_404(Sprint, pk=sid)
        bitem = get_object_or_404(Backlog, pk=bid)
        if str(bitem.sprint.pk) == sid and request.user == bitem.sprint.master:
            bitem.sprint = None
            bitem.save()
        else:
            logger.error('remove_backlog(sid=%s,bid=%s),Backlog.sprint.id=%s,master=%s,request.user=%s'%(sid,bid,bitem.sprint.pk,bitem.sprint.master,request.user))
            return render(request, 'error', {'err':_('Permission denied')})
    except Exception,e:
        logger.error('sprint.remove_backlog: %s'%e)
    return HttpResponseRedirect('/sprint/%s/backlog'%sid)
    
@login_required
def sprint_tasks(request, sid):
    """ Show a list of all tasks grouped by backlog items for the sprint.
    """
    sprint = get_object_or_404(Sprint, pk=sid)
    tasks = Task.objects.filter(item__sprint=sprint)
    return render(request, 'sprint_tasks', {'tasks':tasks,'sprint':sprint,'product':sprint.product}, 'sprint/')

def jsonstr(st):
    """ Convert double quote marks into HTML encoding &quot;
    """
    return st.replace('"', '&quot;')

@permission_required('sprint.change_sprint')
def submit_retro(request):
    """ The scrum master submits the retrospectives for the sprint review.
        request.path: /sprint/retro/submit
        This is done through Ajax call and pass data in JSON.
        User permission: change_sprint
    """
    if request.method == 'POST':
        good = request.POST.get('good','')
        bad = request.POST.get('bad','')
        advice = request.POST.get('next','')
        sid = request.POST.get('sid')
        try:
            sp = Sprint.objects.get(pk=sid)
            if sp.master != request.user: 
                return render(request, 'error', {'err':_('Permission denied')}, fmt='json')
            sp.retro = '{"good":"%s","bad":"%s","next":"%s"}' % (jsonstr(good), jsonstr(bad), jsonstr(advice))
            sp.save()
            return HttpResponse('{"status":"OK"}')
        except Exception,e:
            logger.error('submit_retro failed: %s' % e)
            return error_response(_('Error saving submits, retry later.'), fmt='json')
    else:
        return error_response(_('POST only'))
        