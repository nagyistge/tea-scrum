from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.conf.urls.static import static

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'TeaScrum.views.home'),
    url(r'^staff/', include('staff.urls')),
    url(r'^products?/', include('product.urls')),
    url(r'^sprint/', include('sprint.urls')),
    url(r'^daily/', include('daily.urls')),
    url(r'^backlog/', include('backlog.urls')),
    url(r'^task/', include('backlog.task-urls')),
    url(r'^poker/', include('poker.urls')), #for all vote/start ..
    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG and settings.MEDIA_ROOT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
