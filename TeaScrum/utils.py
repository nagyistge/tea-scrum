# -*- coding: utf-8 -*-

from django.template import RequestContext
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.utils import simplejson
from django.utils.log import getLogger
from TeaScrum.product.models import Product
from TeaScrum.backlog.models import Task

logger = getLogger('TeaScrum')

def get_params(request, params):
    """ Get all values for the keys in the params list.
        e.g. id, name = get_params(request, ['id','name'])
        @param request: HttpRequest instance
        @param params: list of keys or a single key string
        @return: value or a list of values for the key(s) in the params.
    """
    if isinstance(params, list):
        vs = []
        for p in params:
            vs.append(request.REQUEST[p]) #raise KeyError if p not found
        return vs
    else:
        return request.REQUEST[params]
    
def render(request, page, data, prefix=''):
    """ Render a template using render_to_response with the given request context.
        @param request: HttpRequest instance
        @param page: HTML template filename without .html or path
        @param data: Python dict containing key-value pairs of variables to be used in the template
        @param prefix: app name such as 'product/' (always ends with a slash), default to ''
    """
    return render_to_response('%s%s.html'%(prefix,page), data, 
                              context_instance=RequestContext(request))

def json_response(obj):
    """ Return a JSON HttpResponse stream for the obj object.
        @param obj: a Python dict or list, or a string.
        @return: HttpResponse object
    """
    if isinstance(obj, dict) or isinstance(obj, list):
        return HttpResponse(simplejson.dumps(obj), content_type='application/json')
    return HttpResponse(obj)

def error_response(errors, errpage='404.html', fmt='html'):
    """ Return a JSON HttpResponse (when fmt=json) or 404.html stream.
        @param errors: error string
        @param errpage: error html page, default to 404.html
        @param fmt: output format such as html, json
        @return: HttpResponse stream
    """
    if fmt == 'json':
        return HttpResponse(u'{"error":"%s"}' % errors, content_type="application/json")
    else:
        return render_to_response(errpage, {"error":errors})

def get_active_product(request):
    """ Get the current product from the session['ActiveProduct'].
        If session record not found, it tries the user_profile to get a product field.
        If user_profile not found or product is zero, it gets the latest Product entity in the database for request.user, and store its pk in session.
        If the product stored in the session is not found in the database, it throws a Http404 error.
        @return: instance of Product
        @raise Http404: if no product is found
    """
    apk = request.session.get('ActiveProduct', None)
    if apk:
        return get_object_or_404(Product, pk=apk)

    try:
        up = request.user.get_profile()
        if up and hasattr(up, 'product') and up.product > 0:
            ap = get_object_or_404(Product, pk=up.product)
            request.session['ActiveProduct'] = ap.pk
            return ap
    except:
        pass
    
    ps = Product.objects.query_by_user(request.user) #request.user in Product.team.user_set
    if ps.count() > 0:
        ap = ps[0]
        request.session['ActiveProduct'] = ap.pk
        return ap
    
    raise Http404
    #return None

def get_active_sprint(product):
    """ Get the currently started active sprint for the product.
        The active sprint has a status of 'STARTED'.
        This routine returns the first sprint entity with status of 'STARTED'.
    """
    if not product:
        return None
    sps = product.sprint_set.get_query_set().filter(status='STARTED')
    if sps.count() > 0:
        return sps[0]
    return None

def get_my_tasks(user, product):
    """ Get a list of Task entities belonging to the product and user is the doer.
    """
    return Task.objects.query_by_user(user, product)

def get_my_products(user):
    """ Get a list of Product entities the user participated.
    """
    return Product.objects.query_by_user(user)

def is_scrum_role(request, role, product=None):
    """ Check whether request.user is a scrum master or product owner for the specified or active product.
        @param request: HttpRequest
        @param product: Product instance, Product pk, or None
    """
    if not product:
        product = get_active_product(request)
    elif not isinstance(product, Product):
        try:
            product = Product.objects.get(pk=product)
        except:
            return False
    if isinstance(product, Product):
        if role == 'master':
            return request.user == product.master
        elif role == 'owner':
            return request.user == product.owner
        elif role == 'both':
            return request.user in [product.master, product.owner]
        elif role == 'developer': #team member
            return request.user.pk in [d['id'] for d in product.team.user_set.values()]
        else:
            logger.error('Unknown role %s'%role)
    return False

def is_scrum_master(request, product=None):
    return is_scrum_role(request, 'master', product)

def is_product_owner(request, product=None):
    return is_scrum_role(request, 'owner', product)

def is_owner_or_master(request, product=None):
    return is_scrum_role(request, 'both', product)

def is_team_member(request, product=None):
    return is_scrum_role(request, 'developer', product)

def get_velocity(product):
    """ Get the velocity from the product team.
        If no Team entity is associated with the Product.team (Group), settings.VELOCITY is used.
        If settings.VELOCITY not found, returns a default value of 10.
    """
    from TeaScrum.staff.models import Team
    try:
        team = Team.objects.get(group=product.team)
        return team.velocity
    except:
        import settings
        if hasattr(settings, 'VELOCITY'):
            return float(settings.VELOCITY)
        return 10
    
def add_permissions(group_or_user, models):
    """ Add all permissions on models to the given Group or User entity.
        @param group_or_user: an instance of Group or User class
        @param models: a single model name like 'product' or a list of model names (in lowercase)
    """
    from django.contrib.auth.models import Permission
    if isinstance(models, basestring):
        models = [models]
    group_or_user.permissions = Permission.objects.filter(codename__endswith=models)


def init_super_groups(user):
    """ Create two groups: "Product Owners" and "Scrum Masters" and set appropriate permissions on datasets.
    """
    from django.contrib.auth.models import Group
    pos = Group.objects.filter(name='Product Owners')
    if pos.count() < 1:
        po = Group.objects.create(name='Product Owners')
        sm = Group.objects.create(name='Scrum Masters')
        add_permissions(po, ['product','backlog','releaseplan'])
        add_permissions(sm, ['product','backlog','releaseplan','sprint'])
