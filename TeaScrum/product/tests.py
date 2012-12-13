from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission
from views import *

def add_permissions(group, codenames):
    """ Add a permission to the group """
    if isinstance(codenames, basestring):
        codenames = [codenames]
    for codename in codenames:
        perm = get_object_or_404(Permission, codename=codename)
        group.permissions.add(perm)

class ProductTest(TestCase):
    def setUp(self):
        self.team = Group.objects.create(name='Team_0')
        add_permissions(self.team, ['add_product','change_product','delete_product'])
        self.users = []
        for x in xrange(2):
            u = User.objects.create_user('user_%d'%x, 'user_0@example.com', 'pass_%d'%x)
            u.groups.add(self.team)
            self.users.append(u)
            
    def tearDown(self):
        Product.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        
    def add_products(self):
        N = 10
        self.products = []
        for x in xrange(N):
            prod = Product.objects.create(name='Product-%d'%x,owner=self.users[0],master=self.users[1],team=self.team)
            self.products.append(prod)
            
    def test_edit_product(self):
        self.client.login(username='user_0', password='pass_0')
        # add new
        r = self.client.get('/products/add')
        self.assertEqual(r.template[0].name, 'product/product_edit.html')
        pdata = {'name':'Product-x', 'owner':self.users[0].pk, 'master':self.users[1].pk, 'team':self.team.pk, 
                 'vision':'vision', 'timebox':10, 'status':'OPENED'}
        r = self.client.post('/products/add', pdata)
        if r.content.find('errorlist')>0:
            i = r.content.find('errorlist')
            s = r.content[r.content.rfind('<td>',0, i):r.content.find('</td>',i)]
            self.fail(s)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r._headers.get('location',[''])[1].endswith('/product/'))
        ps = Product.objects.all()
        self.assertEqual(ps.count(), 1)
        self.assertEqual(ps[0].name, 'Product-x')
        # edit existing
        pdata['name'] = 'Product-y'
        pdata['product'] = ps[0].pk
        r = self.client.post('/products/edit/%s'%ps[0].pk, pdata)
        self.assertEqual(r.status_code, 302)
        p = Product.objects.get(name='Product-y')
        self.assertTrue(p)
        
    def test_remove_product(self):
        self.add_products()
        self.client.login(username='user_0', password='pass_0')
        qs = Product.objects.all()
        self.assertEqual(qs.count(), 10)
        for p in qs:
            r = self.client.get('/product/remove/%s'%p.pk)
            self.assertEqual(r.status_code, 302)
        self.assertEqual(Product.objects.all().count(), 0)
        
    def test_select_product(self):
        self.add_products()
        self.client.login(username='user_0', password='pass_0')
        pd = Product.objects.get(name='Product-5')
        r = self.client.get('/product/select/%s'%pd.pk)
        self.assertEqual(r.status_code, 302)
        
    def test_product_sprints(self):
        self.add_products()
        self.client.login(username='user_0', password='pass_0')
        pd = Product.objects.get(name='Product-5')
        r = self.client.get('/product/%s/sprints'%pd.pk)
#        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.template[0].name, 'sprint/sprint_list.html')
        
    def test_product_backlog(self):
        self.add_products()
        self.client.login(username='user_0', password='pass_0')
        pd = Product.objects.get(name='Product-5')
        r = self.client.get('/product/%s/backlog'%pd.pk)
        self.assertEqual(r.template[0].name, "backlog/backlog_list.html")
        