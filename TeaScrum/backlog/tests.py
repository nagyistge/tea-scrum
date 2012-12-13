import re
from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission
from django.utils import simplejson
from django.shortcuts import get_object_or_404
from TeaScrum.product.models import Product
from views import *

def add_permissions(group, codenames):
    """ Add a permission to the group """
    if isinstance(codenames, basestring):
        codenames = [codenames]
    for codename in codenames:
        perm = get_object_or_404(Permission, codename=codename)
        group.permissions.add(perm)
    
class BacklogTest(TestCase):
    def setUp(self):
        N = 5
        self.users = []
        self.team = Group.objects.create(name='Team_1')
        add_permissions(self.team, ['add_backlog','change_backlog','delete_backlog'])
        for i in xrange(N):
            u = User.objects.create_user('user_%d'%i, 'user%d@example.com', 'pass_%d'%i)
            u.groups.add(self.team)
            self.users.append(u)
        self.product = Product.objects.create(name='Product_1',owner=self.users[0],master=self.users[0],team=self.team)
        
    def tearDown(self):
        Product.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        Backlog.objects.all().delete()
        
    def test_edit_story(self):
        self.client.login(username='user_0', password='pass_0')
        r = self.client.get('/backlog/')
#        if r.content.find('Add New Story')<0:
#            self.assertEqual(r.content,'*')
#        self.assertTrue(r.content.find('Add New Story')>0)
        r = self.client.get('/backlog/edit/')
        self.assertTrue(r.content.find('<form method="POST" action="/backlog/edit/')>0)
#        csrftoken=re.findall(r'name=["\']?csrfmiddlewaretoken["\']? value=["\'](\w+)["\']',r.content)[0]
        data = {'product':'%s'%self.product.pk,
                'story':'Backlog User story #1','category':'core','priority':'1','muscow':'M',
                'requestor':'','estimate':'0','status':'NEW','notes':'Notes of this story',
                'demos':'','next':'/backlog/' }
        r = self.client.post('/backlog/edit/', data)    #new entity
        self.assertEqual(r.status_code, 302)
        bs = Backlog.objects.all()
        self.assertEqual(bs.count(), 1)
        r = self.client.get('/backlog/edit/%s'%bs[0].pk)
        self.assertTrue(r.content.find('Notes of this story')>0)
        data['notes'] = 'Modified notes of the story'
        r = self.client.post('/backlog/edit/%s'%bs[0].pk, data) #update
        b = Backlog.objects.get(pk=bs[0].pk)
        self.assertEqual(b.notes, 'Modified notes of the story')
        
    def test_bulkload_stories(self):
        self.client.login(username='user_0', password='pass_0')
        r = self.client.get('/backlog/bulkload')
        if r.content.find('textarea name="stories"')<0:
            self.fail(r.content)
        self.assertTrue(r.content.find('textarea name="stories"')>0)
        stories = ['story-1','story2','story3','story4','story5']
        r = self.client.post('/backlog/bulkload', {'stories':'\n'.join(stories)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Backlog.objects.count(), 5)
        
    def test_remove_story(self):
        self.client.login(username='user_0', password='pass_0')
        bl = Backlog.objects.create(product=self.product,story='User story 1',priority=2)
        self.assertEqual(Backlog.objects.count(), 1)
        r = self.client.post('/backlog/remove/%s'%bl.pk)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Backlog.objects.count(), 0)
        
    def test_bulk_remove(self):
        self.client.login(username='user_0', password='pass_0')
        ids = []
        for i in xrange(5):
            bl = Backlog.objects.create(product=self.product,story='User story %s'%i,priority=i)
            ids.append('%s'%bl.pk)
        self.assertEqual(Backlog.objects.count(), 5)
        r = self.client.get('/backlog/remove/selected', {'bids':','.join(ids)})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Backlog.objects.count(), 0)
        
#    def test_item_estimate(self):
#        self.client.login(username='user_0', password='pass_0')
#        bl = Backlog.objects.create(product=self.product,story='User story 1',priority=2)
#        self.assertEqual(Backlog.objects.count(), 1)
#        r = self.client.post('/backlog/estimate',{'item':bl.pk,'est':10.5})
#        self.assertEqual(r.content,'{"status":"OK"}')
#        bi = get_object_or_404(Backlog, pk=bl.pk)
#        self.assertEqual(bi.estimate, 10.5)
        
    def test_backlog_list(self):
        self.client.login(username='user_0', password='pass_0')
        bs = [Backlog.objects.create(product=self.product,story='User story 1',priority=2),
              Backlog.objects.create(product=self.product,story='User story 2',priority=3)]
        self.assertEqual(Backlog.objects.count(), 2)
        r = self.client.get('/backlog/')
        cnt = r.content
        self.assertTrue(cnt.find('bl_tab')>0)
        self.assertTrue(cnt.find('User story 1')>0)
        self.assertTrue(cnt.find('User story 2')>0)
        
    def test_backlog_detail(self):
        self.client.login(username='user_0', password='pass_0')
        bi = Backlog.objects.create(product=self.product,story='User story 1',priority=2)
        r = self.client.get('/backlog/%s'%bi.pk)
        cnt = r.content
        self.assertTrue(cnt.find('bl_detail_tab')>0)
        self.assertTrue(cnt.find('User story 1')>0)
    
    def test_bulkload_tasks(self):
        self.client.login(username='user_0', password='pass_0')
        bi = Backlog.objects.create(product=self.product,story='User story 1',priority=2)
        tasks = ['task-1','task-2','task-3']
        data = {'tasks':'\n'.join(tasks)}
        r = self.client.get('/backlog/%s/tasks/bulkload'%bi.pk)
        self.assertEqual(r.template[0].name, 'backlog/backlog_load.html')
        r = self.client.post('/backlog/%s/tasks/bulkload'%bi.pk,data)
        if r.status_code != 302:
            self.fail(r.template[0].name)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r._headers.get('location',[''])[-1].endswith('backlog/%s/tasks'%bi.pk))
        self.assertEqual(Task.objects.all().count(), 3)
        
    def test_bulkremove_tasks(self):
        self.test_bulkload_tasks()
        bi = Backlog.objects.all()[0]
        tids = ['%s'%t.pk for t in Task.objects.all()]
        r = self.client.get('/backlog/%s/tasks/bulkremove'%bi.pk,{'tids':','.join(tids)})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r._headers.get('location',[''])[-1].endswith('/backlog/%s/tasks'%bi.pk))
        self.assertEqual(Task.objects.count(), 0)
            
class TaskTest(TestCase):
    def setUp(self):
        N = 5
        self.users = []
        self.team = Group.objects.create(name='Team_1')
        add_permissions(self.team, ['add_backlog','change_backlog','delete_backlog'])
        for i in xrange(N):
            u = User.objects.create_user('user_%d'%i, 'user%d@example.com', 'pass_%d'%i)
            u.groups.add(self.team)
            self.users.append(u)
        self.product = Product.objects.create(name='Product_1',owner=self.users[0],master=self.users[0],team=self.team)
        self.backlog = Backlog.objects.create(product=self.product,story='Story-1',priority=1)
        
    def tearDown(self):
        Product.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        Task.objects.all().delete()
        Backlog.objects.all().delete()
        
    def test_edit_task(self):
        self.client.login(username='user_0', password='pass_0')
        r = self.client.get('/backlog/%s/tasks/add'%self.backlog.pk)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.template[0].name, 'backlog/task_edit.html')
        data = {'order':'1','name':'Task-1','technology':'web',
                'notes':'notes','estimate':'3','doer':None,'status':'NEW','start':'2012-01-01','end':'2012-01-20'}
        r = self.client.post('/backlog/%s/tasks/add'%self.backlog.pk, data)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(re.match(r'.+/backlog/\d+/tasks', r._headers.get('location',[''])[-1]), r._headers['location'])
        self.assertEqual(Task.objects.all().count(), 1)
        # edit it
        tsk = Task.objects.all()[0]
        data['order'] = '2'
        r = self.client.post('/task/%s/edit'%tsk.pk, data)
        tsk2 = Task.objects.get(pk=tsk.pk)
        self.assertEqual(tsk2.order, 2.0)
        
    def test_remove_task(self):
        self.test_edit_task()
        tsk = Task.objects.all()[0]
        r = self.client.get('/task/%s/remove'%tsk.pk)
        self.assertEqual(Task.objects.all().count(), 0)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(re.match(r'.+/backlog/\d+/tasks$', r._headers.get('location',[''])[-1]), r._headers['location'])
        
    def test_finish_task(self):
        self.test_edit_task()
        tsk = Task.objects.all()[0]
        tsk.assign(self.users[0])
        r = self.client.get('/task/%s/finish'%tsk.pk)
        self.assertEqual(r.status_code, 302)
        tsk2 = Task.objects.get(pk=tsk.pk)
        self.assertEqual(tsk2.status, 'FINISHED')
        
    def test_planning_poker(self):
        self.test_edit_task()
        tsk = Task.objects.all()[0]
        r = self.client.get('/task/%s/poker'%tsk.pk)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.template[0].name, 'backlog/poker.html')
    
class HierarchyTest(TestCase):
    # TODO: to be implemented
    pass
