from datetime import datetime
from django.contrib.auth.models import User, Group
from django.test import TestCase
from TeaScrum.product.models import Product
from TeaScrum.sprint.models import Sprint
from TeaScrum.backlog.models import Backlog, Task
from models import Daily

def get_err(cnt):
    n1 = cnt.find('<h3>')
    if n1 > 0:
        n2 = cnt.find('</h3>', n1)
        return cnt[n1+4:n2]
    return '<h3> not found in html'

class DailyViewTest(TestCase):
    def setUp(self):
        self.user0 = User.objects.create_user('user_0', 'user_0@example.com', 'pass_0')
        self.users = [self.user0, User.objects.create_user('user_1','u1@a.com','pass_1'),User.objects.create_user('user_2','u2@a.com','pass_2')]
        self.team = Group.objects.create(name='Team 1')
        self.user0.groups.add(self.team)
        self.product = Product.objects.create(name='Produce-1',owner=self.user0,master=self.user0,team=self.team)
        self.sprint = Sprint.objects.create(product=self.product,number=1,goal='First sprint',master=self.user0,start=datetime.now())
        self.client.login(username='user_0',password='pass_0')
        
    def tearDown(self):
        Task.objects.all().delete()
        Backlog.objects.all().delete()
        Sprint.objects.all().delete()
        Product.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        
    def add_backlog_tasks(self, backlogs=3, tasks=3):
        self.backlogs = []
        for x in xrange(backlogs):
            blog = Backlog.objects.create(product=self.product,sprint=self.sprint,story='Story-%d'%x,priority=x)
            self.backlogs.append(blog)
            for t in xrange(tasks):
                Task.objects.create(item=blog,order=t,name='Task-%d-%d'%(x,t))
            for t in xrange(tasks):
                Task.objects.create(item=blog,order=t+tasks,name='Task-%d-%d_doing'%(x,t),doer=self.users[t],status='ASSIGNED')
            Task.objects.create(item=blog,order=4,name='Task-%d_done'%(x),doer=self.users[t],status='FINISHED')

    def test_dailyscrum(self):
        self.add_backlog_tasks(3, 3)
        r = self.client.get('/daily/')
        self.assertEqual(r.status_code, 200)
        if r.template[0].name == 'error.html':
            self.fail(get_err(r.content))
        self.assertEqual(r.template[0].name, 'daily/daily.html')
        cnt = r.content
        self.assertTrue(cnt.find('draw_burndown_chart')>0)
        self.assertTrue(cnt.find('Story-0')>0)
        self.assertTrue(cnt.find('Task-0-0_doing')>0)
        self.assertTrue(cnt.find('Task-0_done')>0)
        # TODO: test tasks are sorted into different lanes
        
    def test_taskboard(self):
        r = self.client.get('/daily/taskboard/')
        self.assertEqual(r.status_code, 200)
        if r.template[0].name == 'error.html':
            self.fail(get_err(r.content))
        self.assertEqual(r.template[0].name, 'daily/taskboard.html')

    def test_submit_daily(self):
        self.add_backlog_tasks(2, 2)
        data = {'spid':self.sprint.pk, 'yesterday':'Yesterday','today':'Today','problem':'Problem','serious':'2'}
        r = self.client.post('/daily/submit', data)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r._headers.get('location',[''])[-1].endswith('/daily'))
        self.assertEqual(Daily.objects.count(), 1)
        
    def test_pick_task(self):
        self.add_backlog_tasks()
        tsk = Task.objects.all()[0]
        r = self.client.get('/daily/pick/%s'%tsk.pk)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r._headers.get('location',[''])[-1].endswith('/daily'))
        tsk2 = Task.objects.get(pk=tsk.pk)
        self.assertEqual(tsk2.doer, self.user0)
        
    def test_unpick_task(self):
        self.test_pick_task()
        tsk = Task.objects.all()[0]
        r = self.client.get('/daily/unpick/%s'%tsk.pk)
        self.assertEqual(r.status_code, 302)
        tsk2 = Task.objects.get(pk=tsk.pk)
        self.assertFalse(tsk2.doer)
        
    def test_check_pick(self):
        # TODO:
        pass
    