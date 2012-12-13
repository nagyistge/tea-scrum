from django.conf.urls.defaults import patterns, url
#from django.views.generic import DetailView
#from django.contrib.auth.decorators import login_required
from views import *
#from models import Sprint

urlpatterns = patterns('',
    url(r'^$', login_required(SprintListView.as_view())),
    url(r'^edit/(?P<sid>\d*)$', edit_sprint), #/sprint/edit/[<sid>]
    url(r'^(?P<sid>\d+)/edit/?$', edit_sprint), #/sprint/<sid>/edit
    url(r'^remove/(?P<sid>\d+)$', remove_sprint), #/sprint/remove/<sid>
    url(r'^(?P<sid>\d+)/remove/?$', remove_sprint), #/sprint/<sid/remove
    url(r'^(?P<pk>\d+)$', login_required(DetailView.as_view(model=Sprint,template_name='sprint/sprint_detail.html'))),
    url(r'^(?P<pk>\d+)/backlog/?$', login_required(SprintBacklogView.as_view())),
    url(r'^(?P<sid>\d+)/backlog/select/?$', select_backlog),
    url(r'^(?P<sid>\d+)/backlog/include/(?P<bid>\d+)$', include_backlog), #/sprint/<sid>/backlog/include/<bid> set backlog.sprint to this sprint
    url(r'^(?P<sid>\d+)/backlog/exclude/(?P<bid>\d+)$', exclude_backlog), #/sprint/<sid>/backlog/exclude/<bid> set this backlog.sprint to None
    url(r'^(?P<sid>\d+)/tasks/?$', sprint_tasks), #/sprint/<sid>/tasks show all tasks for this sprint, grouped by backlog items
    
    url(r'^(?P<pk>\d+)/retro/?$', login_required(DetailView.as_view(model=Sprint,
                                                                    template_name='sprint/retro.html', 
                                                                    context_object_name="sprint"))), #/sprint/<sid>/retro
    url(r'^retro/submit/?$', submit_retro),
)
