# -*- coding: utf-8 -*-
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.utils.log import getLogger
from utils import render, get_active_product, get_active_sprint, get_my_tasks, get_my_products, init_super_groups

logger = getLogger('TeaScrum')

@login_required
def home(request):
    """ Home view to render the index.html page.
        If user not authenticated, a login page is shown.
        Permissions used in template as {% if perms.product.add_product %}
    """
    try:
        product = get_active_product(request)
    except:
        # if superuser and first time, create groups for PO and SM
        if request.user.is_superuser:
            init_super_groups(request.user)
        return render(request, 'index', {})

    data = {'product':product, 'myproducts':get_my_products(request.user)}

    # get active sprint
    sprint = get_active_sprint(product)
    if sprint:
        data['sprint'] = sprint
    
    # get list of sprints, return top 3 if more
    data['sprints'] = product.sprint_set.get_query_set().filter(start__lt=datetime.now())[:3]
#    logger.debug('views.home: sprint=%s, sprints=%s'%(sprint,data['sprints']))
    
    # get my tasks
    mytasks = get_my_tasks(request.user, product)
    if mytasks:
        data['tasks'] = mytasks
    
    data['is_master'] = product.owner_or_master(request.user)
    
    return render(request, 'index', data)
