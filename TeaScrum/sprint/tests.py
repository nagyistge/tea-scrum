from django.contrib.auth.models import User, Group, Permission
from django.test import TestCase
from views import *

def add_permissions(group, codenames):
    """ Add a permission to the group """
    if isinstance(codenames, basestring):
        codenames = [codenames]
    for codename in codenames:
        perm = get_object_or_404(Permission, codename=codename)
        group.permissions.add(perm)
    
class SprintTest(TestCase):
    def setUp(self):
        """ data preparation """
        self.user1 = User.objects.create_user('user_1', 'user1@example.com', 'pass_1')
        self.team1 = Group.objects.create(name='Team 1')
        self.user1.groups.add(self.team1)
        self.product = Product.objects.create(name='Product_1',owner=self.user1,master=self.user1,team=self.team1)
        self.client.login(username='user_1', password='pass_1')
        
    def tearDown(self):
        self.product.delete()
        self.user1.delete()
        self.team1.delete()
        Sprint.objects.all().delete()
        Backlog.objects.all().delete()
        
    def test_edit_sprint(self):
        # new sprint
        r = self.client.get('/sprint/edit/')
        self.assertEqual(r.status_code, 302) #redirect to login.html
        self.assertTrue(r._headers.get('location',[''])[1].find('/login/')>0)
        # add permission
        add_permissions(self.team1, ['add_sprint'])
        r = self.client.get('/sprint/edit/')    #return sprint_edit.html
        self.assertTrue(r.content.find('id_goal')>0)
        # post new sprint
        data = {'product':self.product.pk,'number':'1','goal':'First sprint',
                'timebox':'10','dailytime':'9:30','estimate':0,'actual':0,'start':'2012-12-01','end':'2012-12-31',
                'demotime':'2012-12-31','status':'OPENED'}
        r = self.client.post('/sprint/edit/', data) #redirect to /sprint/product.pk
        if r.content.find('errorlist')>0:
            i = r.content.find('errorlist')
            s = r.content[r.content.rfind('<td>',0, i):r.content.find('</td>',i)]
            self.fail(s)
        self.assertEqual(r.status_code, 302)
        sp = Sprint.objects.all()
        self.assertEqual(sp.count(), 1)
        # post update
        data['goal'] = 'Modified sprint goal'
        r = self.client.post('/sprint/edit/%s'%sp[0].pk, data)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Sprint.objects.count(), 1)
        sp = Sprint.objects.get(pk=sp[0].pk)
        self.assertEqual(sp.goal, data['goal'])
        
    def test_remove_sprint(self):
        add_permissions(self.team1, ['add_sprint'])
        data = {'product':self.product.pk,'number':'1','goal':'First sprint','master':self.user1.pk,
                'timebox':'10','dailytime':'9:30','estimate':0,'actual':0,'start':'2012-12-01','end':'2012-12-31',
                'demotime':'2012-12-31','status':'OPENED'}
        r = self.client.post('/sprint/edit/', data) #redirect to /sprint/product.pk
        if r.status_code != 302:
            if r.content.find('errorlist')>0:
                i = r.content.find('errorlist')
                s = r.content[r.content.rfind('<td>',0, i):r.content.find('</td>',i)]
                self.fail(s)
        self.assertEqual(Sprint.objects.all().count(),1)
        sp = Sprint.objects.all()[0]
        add_permissions(self.team1, ['delete_sprint'])
        r = self.client.get('/sprint/remove/%s'%sp.pk)
        self.assertEqual(r.status_code, 302)
        sps = Sprint.objects.all()
        self.assertEqual(sps.count(), 0)
    
    def add_backlog(self,N=10):
        for i in xrange(N):
            Backlog.objects.create(product=self.product,story='Story-%s'%i,priority=i,estimate=4)
        self.assertEqual(Backlog.objects.count(), N)
        
    def test_backlog_view(self):
        self.test_edit_sprint()
        sp = Sprint.objects.all()[0]
        # test get sprint detail
        r = self.client.get('/sprint/%s'%sp.pk)
        self.assertTrue(r.content.find('sp_detail_tab')>0)
        # backlog view
        add_permissions(self.team1, ['change_sprint'])
        self.add_backlog()
        r = self.client.get('/sprint/%s/backlog'%sp.pk)
        self.assertTrue(r.content.find('sp_backlog_tab')>0)
        
    def test_select_backlog(self):
        self.test_backlog_view()
        sp = Sprint.objects.all()[0]
        add_permissions(self.team1, ['change_sprint'])
        r = self.client.get('/sprint/%s/backlog/select'%sp.pk, {'v':20})
        cnt = r.content
        est = 0
        N = 10 - 1  # add_backlog()
        for i in xrange(N):
            x = N - i
            est += 4
            if est > 20:
                self.assertFalse(cnt.find('Story-%s'%x)>0)
                break
            else:
                self.assertTrue(cnt.find('Story-%s'%x)>0)
        self.assertEqual(Backlog.objects.filter(sprint=sp).count(), 5)
    
    def test_include_backlog(self):
        self.test_edit_sprint()
        sp = Sprint.objects.all()[0]
        add_permissions(self.team1, ['change_sprint'])
        self.add_backlog(10)
        items = Backlog.objects.all()
        r = self.client.get('/sprint/%s/backlog/include/%s' % (sp.pk, items[0].pk))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r._headers.get('location',[''])[1].endswith('/sprint/%s/backlog'%sp.pk))
        
    def test_exclude_backlog(self):
        self.test_select_backlog()
        sp = Sprint.objects.all()[0]
        for bi in Backlog.objects.filter(sprint=sp):
            r = self.client.get('/sprint/%s/backlog/exclude/%s'%(sp.pk, bi.pk))
            self.assertEqual(r.status_code, 302)
        self.assertEqual(Backlog.objects.filter(sprint=sp).count(), 0)
        
    def test_sprint_tasks(self):
        self.test_select_backlog()
        sp = Sprint.objects.all()[0]
        bs = sp.backlog_set.get_query_set()
        from TeaScrum.backlog.models import Task
        t1 = Task.objects.create(item=bs[0],order=0,name='Task-1')
        t2 = Task.objects.create(item=bs[1],order=1,name='Task-2')
        r = self.client.get('/sprint/%s/tasks'%sp.pk)
        self.assertEqual(r.template[0].name, 'sprint/sprint_tasks.html')
        import re
        self.assertEqual(len(re.findall(r'<tr class="task_', r.content)), 2)

    def test_sprint_retro(self):
        self.test_edit_sprint()
        sp = Sprint.objects.all()[0]
        r = self.client.get('/sprint/%s/retro'%sp.pk)
        self.assertEqual(r.template[0].name, 'sprint/retro.html')
        
    def test_submit_retro(self):
        self.test_edit_sprint()
        sp = Sprint.objects.all()[0]
        add_permissions(self.team1, ['change_sprint'])
        data = {'good':'what\'s well done', 'bad':'what needs improvement', 'next':'what to do next', 'sid':sp.pk}
        r = self.client.post('/sprint/retro/submit', data)
        self.assertEqual(r.content, '{"status":"OK"}')
        r = self.client.get('/sprint/%s/retro'%sp.pk)
        self.assertTrue(r.content.find('what needs improvement</textarea>')>0, r.content)
        