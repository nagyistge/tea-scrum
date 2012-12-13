# -*- coding: utf-8 -*-

from datetime import datetime
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.decorators import login_required, permission_required
from TeaScrum.utils import error_response, render
from models import Staff, Team
from forms import RegisterForm, StaffForm, TeamForm

def register(request):
    """ Register a new user.
        Developers register themselves here and optionally choose to join a team.
        A super user is responsible to promote a user to a product owner or a scrum master.
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')
    else:
        form = RegisterForm()
    return render(request, 'register', {'form':form}, 'staff/')

@login_required
def edit_staff(request):
    """ Edit user profile. """
    staff = request.user.profile
    if request.method == 'POST':
        form = StaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            data = form.cleaned_data
            if data['team']:
                try:
                    team = Group.objects.get(pk=data['team'])
                    request.user.groups.add(team)
                except:
                    pass
            return HttpResponseRedirect('/staff/%s'%staff.pk)
    else:
        form = StaffForm(instance=staff)
    return render(request, 'staff_edit', {'form':form}, 'staff/')

@login_required
def promote(request):
    """ Promote a user to a product owner or scrum master.
        The permissions are updated for this user accordingly.
    """
    if not request.user.is_superuser():
        return error_response(_('Permission denied'))
    uid = request.REQUEST.get('uid')
    usr = get_object_or_404(User, pk=uid)
    staff = usr.get_profile()
    role = request.REQUEST.get('role', '')
    if role not in ['D','M','O']:
        return error_response(_('Invalid role'))
    staff.role = role
    staff.save()
    # change permission
    # product owner permissions: add,change,delete product, backlog, releaseplan
    # scrum master permissions: add,change,delete backlog, sprint, task, releaseplan
    if role == 'D':
        usr.permissions.clear()
    else:
        perms = {'O':['product','backlog','releaseplan'],'M':['sprint','backlog','releaseplan']}
        for p in perms[role]:
            for act in ['add','change','delete']:
                cname = '%s_%s' % (act, p)
                usr.permissions.add(Permission.objects.get(codename=cname))
    return HttpResponseRedirect('/')

@permission_required('staff.add_staff')
def edit_team(request, tid=None):
    """ Add a new Group entity or edit an existing one, and a Team entity is saved along with it.
    """
    if not tid:
        tid = request.REQUEST.get('tid', None)

    if tid:
        team = get_object_or_404(Group, pk=tid)
    else:
        team = None
    
    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')
    else:
        form = TeamForm(instance=team)
    return render(request, 'team_edit', {'form':form, 'team':team}, 'staff/')
