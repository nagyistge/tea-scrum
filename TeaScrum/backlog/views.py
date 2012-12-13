# -*- coding: utf-8 -*-

import time
from datetime import datetime
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils.translation import ugettext as _
from django.utils.log import getLogger
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from models import Backlog, Task
from forms import BacklogForm, TaskForm
from TeaScrum.product.models import Product
from TeaScrum.utils import render, get_active_product, error_response

logger = getLogger('TeaScrum')

def get_category_typeaheads():
    """ Load backlog category typeahead string array from database.
    """
#    terms = TermBase.objects.filter(group='ST') #all terms in Story group
#    return '[%s]'%','.join('"%s"'%t.term for t in terms)
    return '[]'

class BacklogListView(ListView):
    context_object_name = "items"
    template_name = "backlog/backlog_list.html"

    def get_queryset(self):
        """ Get a queryset of all backlogs for a product.
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
        return Backlog.objects.filter(product=self.product)

    def get_context_data(self, **kwargs):
        context = super(BacklogListView, self).get_context_data(**kwargs)
        context['product'] = self.product
        context['gcounts'] = Backlog.objects.group_by_status(self.product)
        context['can_add'] = self.request.user in [self.product.owner, self.product.master]
        return context

class TaskListView(ListView):
    context_object_name = "task_list"
    template_name = "backlog/backlog_tasks.html"
    
    def get_queryset(self):
        self.product = get_active_product(self.request)
        self.item = get_object_or_404(Backlog, pk=self.kwargs['bid'])
        return self.item.tasks.get_query_set()

    def get_context_data(self, **kwargs):
        context = super(TaskListView, self).get_context_data(**kwargs)
        context['product'] = self.product
        context['backlog'] = self.item
        context['can_add'] = self.request.user in [self.product.owner, self.product.master]
        return context

@permission_required('backlog.add_backlog')
def edit_story(request, bid=None, pid=None):
    """ Add a new or edit an existing backlog story.
        A HTTP Get request will return a form to edit a story, and a HTTP POST will save the form.
        If bid is given, the backlog item is loaded otherwise a new item is created.
        User permission required: add_backlog
    """
    nextpg = None
    if pid:
        product = get_object_or_404(Product, pk=pid)
    else:
        product = get_active_product(request)
    if request.method == 'POST':
        nextpg = request.POST.get('next','/backlog/')
        if bid:
            item = get_object_or_404(Backlog, pk=bid)
            if item.product != product:
                logger.error('Backlog.product %s is not active product %s' % (item.product, product))
                return render(request, 'error', {'err':_('Not current active product')})
            if request.user not in [item.product.owner, item.product.master]:
                logger.warning('Not scrum master or product owner')
                return render(request, 'error', {'err':_('Permission denied')})
            form = BacklogForm(request.POST, instance=item)
        else:
            form = BacklogForm(request.POST)
        if form.is_valid():
            blog = form.save(commit=False)
            if not bid:
                blog.product = product
            try:
                blog.save()
                #form.save_m2m()
            except Exception,e:
                logger.error('backlog.views.edit_story, form.save() error: %s'%e)
            return HttpResponseRedirect(nextpg)
    elif bid:
        item = get_object_or_404(Backlog, pk=bid)
        if item.product != product:
            logger.error('Backlog.product %s is not active product %s' % (item.product, product))
            return render(request, 'error', {'err':_('Not current active product')})
        form = BacklogForm(instance=item)
    else:
        form = BacklogForm()
    if not nextpg: nextpg = request.GET.get('next','/backlog/')
    params = {'form': form, 'product': product, 'cataheads': get_category_typeaheads(), 'next':nextpg, 'url':'/backlog/edit/%s' % (bid or '')}
    return render(request, 'story_edit', params, 'backlog/') 

@permission_required('backlog.add_backlog')
def bulkload_stories(request):
    """ Bulk input a list of stories into the product backlog.
        User permission required: add_backlog
    """
    product = get_active_product(request)
    if not product.owner_or_master(request.user):
        return render(request, 'error', {'err':_('Permission denied')})
    if request.method == 'POST':
        stories = request.POST.get('stories', None)
        if not stories:
            return render(request, 'error', {'err':_('No stories')})
        for story in stories.split('\n'):
            if story.strip():
                Backlog.objects.create(product=product,story=story.strip())
        return HttpResponseRedirect('/backlog/')
    else:
        params = {'product':product,'url':request.path, 'inputname':'stories'}
        params['subtitle'] = _('Bulk input user stories')
        return render(request, 'backlog_load', params, 'backlog/')

@permission_required('backlog.add_backlog')
def bulkload_tasks(request, bid):
    """ Bulk input a list of tasks for a backlog item/story.
        User permission required: add_backlog
    """
    if not bid:
        return render(request, 'error', {'err':_('No backlog item')})
    
    item = get_object_or_404(Backlog, pk=bid)
    product = item.product
    if not product.owner_or_master(request.user):
        return render(request, 'error', {'err':_('Permission denied')})
    
    if request.method == 'POST':
        tasks = request.POST.get('tasks', None)
        if not tasks:
            return render(request, 'error', {'err':_('No stories specified')})
        for task in tasks.split('\n'):
            if task.strip():
                Task.objects.create(item=item,name=task.strip())
        return HttpResponseRedirect('/backlog/%s/tasks'%bid)
    else:
        params = {'product':product,'backlog':item,'url':request.path, 'inputname':'tasks'}
        params['subtitle'] = _('Bulk input tasks for the backlog item')
        return render(request, 'backlog_load', params, 'backlog/')
    
@permission_required('backlog.delete_backlog')
def remove_story(request, bid=None):
    """ Remove a backlog item specified by ID.
        Only the product owner or scrum master can remove an item from the backlog.
        HTTP GET can be used instead of DELETE for REST framework.
        User permission required: delete_backlog
    """
    if bid:
        try:
            item = Backlog.objects.get(pk=bid)
        except Exception, e:
            logger.warning('scrum.remove_story: Backlog item %s not found: %s' % (bid, e))
            return render(request, 'error', {'err':_('Backlog item not found.')}, '')
        if request.user not in [item.product.owner, item.product.master]:
            return render(request, 'error', {'err':_('Permission denied')})
        try:
            item.delete()
        except Exception, e:
            logger.error('scrum.remove_story: Backlog item delete failed: %s' % e)
            return render(request, 'error', {'err':_('Backlog delete failed, please try again later.')}, '')
    return HttpResponseRedirect('/backlog/')

@permission_required('backlog.delete_backlog')
def bulk_remove(request):
    """ Remove a list of Backlog items.
        HTTP GET can be used instead of DELETE for REST framework.
        User permission required: delete_backlog
    """
    bids = request.REQUEST.get('bids',None)
    if not bids:
        return HttpResponseRedirect('/backlog/')
    try:
        qs = Backlog.objects.filter(pk__in=bids.split(','))
        if qs.count() > 0 and request.user in [qs[0].product.owner, qs[0].product.master]:
            qs.delete()
            return HttpResponseRedirect('/backlog/')
        else:
            return render(request, 'error', {'err':_('Permission denied')})
    except Exception,e:
        logger.error('backlog.views.bulk_remove(bids=%s): %s'%(bids,e))
        return render(request, 'error', {'err':_('Error deleting these items.')})
    
@permission_required('backlog.delete_backlog')
def bulk_remove_tasks(request, bid):
    """ Remove a list of tasks of a backlog item.
        HTTP GET can be used instead of DELETE for REST framework.
        User permission required: delete_backlog
    """
    tids = request.REQUEST.get('tids', None)
    if not (bid and tids):
        return HttpResponseRedirect('/backlog/')
    try:
        item = get_object_or_404(Backlog, pk=bid)
    except:
        logger.error('bulk_remove_tasks(bid=%s)'%bid)
        return render(request,'error',{'err':_('Record not found')})
    try:
        item.tasks.get_query_set().filter(pk__in=tids.split(',')).delete()
    except Exception, e:
        logger.error('bulk_remove_tasks(bid=%s,tids=%s) error:%s' % (bid, tids, e))
        return render(request,'error',{'err':_('Error deleting tasks')})
    return HttpResponseRedirect('/backlog/%s/tasks'%item.pk)
    
@permission_required('backlog.change_backlog')
def save_notes(request):
    """ The scrum master saves some notes about a backlog item.
        User permission required: change_backlog
    """
    if request.method=='POST':
        itemid = request.POST.get('item',None)
        notes = request.POST.get('notes','')
        try:
            item = Backlog.objects.get(pk=itemid)
            if request.user not in [item.product.owner, item.product.master]:
                logger.warning('Not scrum master or product owner')
                return render(request, 'error', {'err':_('Permission denied')})
            item.notes = notes
            item.save()
            return HttpResponse('{"status":"OK"}')
        except Exception,e:
            logger.exception('save_notes error: %s'%e)
            return error_response(_('Error saving notes'))
#            return HttpResponse('{"error":"Not saved"}')
        
@permission_required('backlog.change_backlog')
def save_estimate(request, tid):
    """ Get or Post/save Backlog(item).estimate. Only product scrum master can save.
        Query path: /task/<tid>/estimate[?est=4]
        User permission required: change_backlog
    """
    try:
        tsk = Task.objects.get(pk=tid)
    except Task.DoesNotExist:
        return error_response(_('Task not found'), fmt='json')
    
    if request.method == 'GET':
        return HttpResponse('{"status":"OK","estimate":"%s"}' % (tsk.estimate))
    else:
        # TODO: verify user is a product owner or scrum master
        tsk.estimate = float(request.POST.get('est'))
        try:
            tsk.save()
            # TODO: call Backlog.update_estimate to sum up all task estimates
            return HttpResponseRedirect('/backlog/%s/tasks'%tsk.item.pk)
#            return HttpResponse('{"status":"OK"}')
        except:
            return error_response(_('Failed to save task estimate.'))

@permission_required('backlog.add_backlog')
def edit_task(request, bid=None, tid=None):
    """ Edit/GET and save/POST a task entity for a backlog item.
        User permission required: add_backlog
    """
    if tid:
        task = get_object_or_404(Task, pk=tid)
        backlog = task.item
    elif bid:
        backlog = get_object_or_404(Backlog, pk=bid)
        task = None
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            tsk = form.save(commit=False)
            if not hasattr(tsk, 'item'):
                setattr(tsk, 'item', backlog)
            try:
                tsk.save()
                #form.save_m2m()
            except Exception,e:
                logger.error('edit_task form.save failure %s'%e)
            return HttpResponseRedirect('/backlog/%s/tasks'%backlog.pk)
    else:
        form = TaskForm(instance=task)
    params = {'form':form,'product':backlog.product,'backlog':backlog,'task':task}
    return render(request, 'task_edit', params,'backlog/')
        
@login_required
def save_task(request):
    """ Save a new task or update an old one.
    """
    tids = request.POST.get('t_id','')
    if '-' in tids:
        item, task = tids.split('-')
    else:
        item = tids
        task = None
    logger.debug('save_task: item=%s, task=%s'%(item,task))
    tname = request.POST.get('tname','')
    ttech = request.POST.get('ttech','')
#    est = request.POST.get('testimate','')
    notes = request.POST.get('tnotes','')
    if task:
        logger.debug('save_task: update SprintTask, id=%s'%task)
        t = Task.objects.get(pk=int(task))
    else:
        logger.debug('save_task: new SprintTask,item_id=%s'%item)
        try:
            itm = Backlog.objects.get(pk=item)
        except:
            logger.error('save_task: Backlog(%s) not found in db'%item)
            return HttpResponse('{"error":"%s"}'%_('Backlog item not found, please check.'))
        t = Task(item=itm)
    t.name = tname
    t.technology = ttech
    t.notes = notes
    t.number = int(time.time()) % 1000000000
    try:
        t.save()
        return HttpResponse('{"status":"OK","item":"%s","task":"%s"}' % (item, t.pk))
    except Exception,e:
        logger.error('save_task error: %s'%e)
        return HttpResponse('{"error":"%s"}'%_('Error saving task, retry later.'))
    

@permission_required('backlog.delete_backlog')
def remove_task(request, tid):
    """ Remove a task from Task.
        User permission required: delete_backlog
    """
    if not tid:
        tid = request.REQUEST.get('tid', None)
        if not tid:
            return render(request, 'error', {'err':_('No task ID')})
    task = get_object_or_404(Task, pk=tid)
    if not task.item.product.owner_or_master(request.user):
        return error_response(_('Permision denied'))
    try:
        task.delete()
        return HttpResponseRedirect('/backlog/%s/tasks'%task.item.pk)
    except:
        return error_response(_('Error deleting task'))

@login_required
def planning_poker(request, tid=None):
    """ Start planning poker page for backlog task tid.
        User permission: developer
    """
    if not tid:
        tid = request.REQUEST.get('tid', None)
        if not tid:
            return error_response(_('No task specified'))
    task = get_object_or_404(Task, pk=tid)
    item = task.item
    product = item.product
    if not product.has_member(request.user):
        return render(request, 'error', {'err':_('Permission denied')})
    params = {'product':product,'backlog':item,'task':task,'master':product.owner_or_master(request.user)}
    return render(request, 'poker', params,'backlog/')

@login_required
def finish_task(request, tid=None):
    """ Mark a Task as finished.
    """
    if not tid:
        tid = request.REQUEST.get('tid', None)
        if not tid:
            return render(request,'error',{'err':_('No task given')})
    task = get_object_or_404(Task, pk=tid)
    if task.doer == request.user:
        task.status = 'FINISHED'
        task.end = datetime.now()
        task.actual = (task.end - task.start).seconds / 86400.0
        task.save()
        return HttpResponseRedirect('/backlog/%s/tasks'%task.item.pk)
    return render(request,'error',{'err':_('Permission denied')})

@permission_required('backlog.add_backlog')
def import_stories(request):
    """ Upload a CSV file as stories into the specified product backlog.
        A list of fields can be selected to parse the rows in the CSV to match the Backlog metadata.
    """
    # TODO: implement importing backlog items from a CSV file from upload
    if request.method == 'POST':
        pass
    else:
        pass
    return error_response(_('Not implemented yet'))
    
@login_required
def export_stories(request):
    """ Download backlog items as CSV file
    """
    # TODO: implement exporting backlog items as a CSV file for download
    return error_response(_('Not implemented yet'))
