# -*- coding: utf-8 -*-

"""
    Voting interface for the planning poker game.
    
    During the planning meeting, the scrum master can start a voting session to collect the estimates
    from the team for a particular topic (backlog item).
    
    start - [scrum master] start a new session for voting
    status - [team members] get voting status, started or closed
    vote - [team members] send a vote choice 0-20
    collect - [team members] get all values from the voters, return either '*' or the vote value
    stop - [scrum master] get the last result and stop the session, then collect will return values
    
    return dataset: {"uid":n,..} where n=* while session is on, n=vote value after session stops.
"""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.utils.log import getLogger

from models import Vote
from TeaScrum.utils import is_scrum_master, error_response, is_team_member, get_params, json_response

logger = getLogger('TeaScrum')
    
@login_required
def start(request):
    """ Start a new voting session.
        @return: {"sid":"a343545d4454.."}
    """
    usr = request.user
    pid = request.GET.get('pid', None)
    if not pid:
        return error_response(_('No Product ID'), fmt='json')
    if not is_scrum_master(request, pid):
        return error_response(_('Scrum Master required'), fmt='json')
    return json_response(Vote.objects.start(usr,pid))
    
@login_required
def status(request):
    """ Check status of voting and get sid if started.
    """
    pid = request.GET.get('pid', None)
    if not pid:
        return error_response(_('No Product ID'), fmt='json')
    return json_response(Vote.objects.status(pid))

@login_required
def vote(request):
    """ Submit a value for the voting session.
    """
    try:
        sid, pid, vote = get_params(request, ['sid','pid','vote'])
    except KeyError, e:
        logger.error('poker.vote() request.get error: %s' % e)
        return error_response(_('Not enough parameters'), fmt='json')
    
    if not is_team_member(request, pid):
        return error_response(_('Team member required'), fmt='json')
    
    v, created = Vote.objects.get_or_create(session=sid, product=pid, voter=request.user)
    try:
        v.vote = vote
        v.save()
        return HttpResponse('{"status":"OK"}', content_type='application/json')
    except Exception, e:
        logger.error('poker.vote() error: %s' % e)
        return error_response(_('Error saving your vote'), fmt='json')

@login_required
def collect(request):
    """ Collect all submitted votes.
        @return: {"status":"STARTED","votes":{"<uid>":"<vote>","1":3,..}}
    """
    try:
        sid, pid = get_params(request, ['sid','pid'])
    except KeyError, e:
        logger.error('poker.collect() error: %s' % e)
        return error_response(_('Not enough parameters'), fmt='json')
    
    vs = Vote.objects.collect(pid, sid)
    ret = {'status':vs[0].status, 'votes':dict(('%s'%v.voter.pk, '*' if v.status=='STARTED' else v.vote) for v in vs)}
#    vs = dict(('%s'%v.user.pk, v.vote) for v in Vote.objects.collect(pid, sid))
#    ret = {'votes':{}}
#    for v in Vote.objects.collect(pid, sid):
#        ret['votes']['%s'%v.voter.pk] = v.vote
#        if v.chair:
#            ret['status'] = v.status
    return json_response(ret)
    
@login_required
def stop(request):
    """ Stop the session.
    """
    try:
        sid, pid = get_params(request, ['sid','pid'])
    except KeyError, e:
        logger.error('poker.stop() error: %s' % e)
        return error_response(_('Not enough parameters'), fmt='json')
    
    if not is_scrum_master(request, pid):
        return error_response(_('Scrum Master required'), fmt='json')
    
    try:
        Vote.objects.stop(pid, sid)
        return HttpResponse('{"status":"OK"}', content_type='application/json')
    except:
        return json_response({"error":u"%s" % _('Failed to stop the session')})
    