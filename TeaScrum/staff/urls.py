from django.conf.urls.defaults import patterns, url
from django.views.generic import DetailView
from views import *

urlpatterns = patterns('',
    url(r'^$', 'django.contrib.auth.views.login', {'template_name': 'staff/login.html'}),
    url(r'^register/?$', register),
    url(r'^login/?$', 'django.contrib.auth.views.login', {'template_name': 'staff/login.html'}),
    url(r'^logout/?$', 'django.contrib.auth.views.logout'),
    url(r'^changepwd/?$', 'django.contrib.auth.views.password_change', {'template_name': 'staff/changepwd.html','post_change_redirect':'/'}),
    url(r'^(?P<pk>\d+)$', login_required(DetailView.as_view(model=Staff, template_name='staff/profile.html'))),
    url(r'^profile/edit/?$', edit_staff),
    url(r'^team/add/?$', edit_team),
    url(r'^team/edit/(?P<tid>\d*)$', edit_team),
)
