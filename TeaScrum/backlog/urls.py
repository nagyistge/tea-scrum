from django.conf.urls.defaults import patterns, url
from views import *

urlpatterns = patterns('',
    url(r'^$', login_required(BacklogListView.as_view())),
    url(r'^(?P<pk>\d+)$', login_required(DetailView.as_view(model=Backlog, template_name='backlog/backlog_detail.html'))),
    url(r'^edit/(?P<bid>\d*)$', edit_story), #/backlog/edit/
    url(r'^(?P<bid>\d+)/edit/?$', edit_story),
    url(r'^bulkload/?$', bulkload_stories), #bulk-input 
    url(r'^upload/?$', import_stories), #upload CSV format files with given fields
    url(r'^export/?$', export_stories), #download items into a CSV file
    url(r'^remove/(?P<bid>\d+)$', remove_story),
    url(r'^(?P<bid>\d+)/remove/?$', remove_story),
    url(r'^remove/selected$', bulk_remove),
    url(r'^(?P<bid>\d+)/tasks/?$', login_required(TaskListView.as_view())),
    url(r'^(?P<bid>\d+)/tasks/add/?$', edit_task),
    url(r'^(?P<bid>\d+)/tasks/bulkload/?$', bulkload_tasks),
    url(r'^(?P<bid>\d+)/tasks/bulkremove/?$', bulk_remove_tasks),
)
