# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils.translation import ugettext as _
from django.utils.log import getLogger
from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from models import Product, ProductForm
from TeaScrum.utils import render

logger = getLogger('TeaScrum')

@permission_required('product.add_product')
def edit_product(request, pid=None):
    """ Show an edit form for a Product entity.
    """
    if not pid:
        pid = request.REQUEST.get('pid', None)
        
    if pid:
        product = get_object_or_404(Product, pk=pid)
        if not product.owner_or_master(request.user):
            return render(request, 'error', {'err':_('Permission denied')})
    else:
        product = None
        
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            pd = form.save(commit=False)
            if not hasattr(pd, 'owner'):
                setattr(pd, 'owner', request.user)
            pd.save()
            #form.save_m2m()
            return HttpResponseRedirect('/product/')
    else:
        if product:
            form = ProductForm(instance=product)
        else:
            form = ProductForm()
        
    return render(request, 'product_edit', {'form':form,'pid':pid}, 'product/')

@permission_required('product.delete_product')
def remove_product(request, pid=None):
    """ Remove a product/project by the owner.
    """
    if not pid:
        pid = request.REQUEST.get('pid', None)
    product = get_object_or_404(Product, pk=pid)
    if product.owner == request.user:
        product.delete()
        return HttpResponseRedirect('/products')
    else:
        return render(request, 'error', {'err':_('Permission denied')})
    
@login_required
def select_product(request, pid=None):
    """ Select a product into active session.
    """
    if not pid:
        pid = request.REQUEST.get('pid', None)
    product = get_object_or_404(Product, pk=pid)
    if not product.has_member(request.user):
        return render(request, 'error', {'err':_('Permission denied')})
    
    request.session['ActiveProduct'] = product.pk
    return HttpResponseRedirect('/')
