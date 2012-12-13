from django.conf.urls.defaults import patterns, url
from views import *

urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)$', login_required(DetailView.as_view(model=Task, 
                                                            context_object_name='task',
                                                            template_name='backlog/task_detail.html'))), #/task/<tid>
    url(r'^edit/(?P<tid>\d*)$', edit_task), #/task/edit/<tid>
    url(r'^(?P<tid>\d+)/edit/?$', edit_task), #/task/<tid>/edit
    url(r'^remove/(?P<tid>\d+)$', remove_task), #/task/remove/<tid>
    url(r'^(?P<tid>\d+)/remove/?$', remove_task), #/task/<tid>/remove
    url(r'^remove/selected/?$', bulk_remove_tasks), #/task/remove/selected
    url(r'^bulkload/?$', bulkload_tasks), #/task/bulkload
    url(r'^(?P<tid>\d+)/poker/?$', planning_poker), #/task/<tid>/poker
    url(r'^(?P<tid>\d+)/estimate/?$', save_estimate), #/task/<tid>/estimate?est=value for POST
    url(r'^(?P<tid>\d+)/finish/?$', finish_task), #/task/<tid>/finish
)
