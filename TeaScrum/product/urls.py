from django.conf.urls.defaults import patterns, url
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from models import Product
from views import edit_product, select_product, remove_product
from TeaScrum.sprint.views import SprintListView, edit_sprint
from TeaScrum.backlog.views import BacklogListView, edit_story

urlpatterns = patterns('',
    url(r'^$', login_required(ListView.as_view(model=Product, 
                                               template_name="product/product_list.html",
                                               context_object_name="product_list"))),
    url(r'^(?P<pk>\d+)$', login_required(DetailView.as_view(model=Product, 
                                                              template_name="product/product_detail.html",
                                                              context_object_name="product"))),
    url(r'^add/?$', edit_product), #/products/add GET only to edit a new product
    url(r'^edit/(?P<pid>\d*)$', edit_product), #/product/edit/[pid] add new or edit an existing product, GET/POST
    url(r'^(?P<pid>\d+)/edit/?$', edit_product), #/product/<pid>/edit edit an existing product GET/POST
    url(r'^(?P<pid>\d+)/remove/?$', remove_product), #/product[s]/<pid>/remove delete product pid
    url(r'remove/(?P<pid>\d+)$', remove_product), #/products/remove/<pid> as alternative path
    url(r'^select/(?P<pid>\d+)$', select_product), #/product[s]/select/<pid> select pid as active product
    
    #product.sprints access via sprint app
    url(r'^(?P<pid>\d+)/sprints/?$', login_required(SprintListView.as_view())),
    url(r'^(?P<pid>\d+)/sprints/add/?$', edit_sprint),

    #product.backlog items access via backlog app
    url(r'^(?P<pid>\d+)/backlog/?$', login_required(BacklogListView.as_view())),
    url(r'^(?P<pid>\d+)/backlog/add/?$', edit_story),
)
