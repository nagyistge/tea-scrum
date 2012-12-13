import re
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group
from django.utils import simplejson
from views import *
from TeaScrum.product.models import Product

class PokerViewTest(TestCase):
    def setUp(self):
        N = 5
        self.users = []
        self.team = Group.objects.create(name='Team_1')
        for i in xrange(N):
            u = User.objects.create_user('user_%d'%i, 'user%d@example.com', 'pass_%d'%i)
            u.groups.add(self.team)
            self.users.append(u)
#            print 'user[%d].pk=%d'%(i,u.pk)
        self.product = Product.objects.create(name='Product_1',owner=self.users[0],master=self.users[0],team=self.team)
#        print 'self.product.pk=',self.product.pk
        
    def tearDown(self):
        Product.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()
        
    def testStart(self):
        self.client.login(username='user_0',password='pass_0')
        r = self.client.get('/poker/start/?pid=%s'%self.product.pk)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.find('{"sid":')>=0)
        vs = Vote.objects.all()
        self.assertEqual(vs.count(), 1)
        self.assertTrue(vs[0].session, 1)
        self.assertTrue(vs[0].status, "STARTED")
        # non scrum master login should fail
        client2 = Client()
        client2.login(username='user_2',password='pass_2')
        r2 = client2.get('/poker/start/?pid=%s'%self.product.pk)
        self.assertTrue(r2.content.find("Scrum Master required")>0)
        
    def testStop(self):
        self.client.login(username='user_0', password='pass_0')
        r = self.client.get('/poker/stop/')
        self.assertTrue(r.content.find('Not enough parameters')>=0)
        r = self.client.get('/poker/start/?pid=%s'%self.product.pk)
        sid = re.findall(r'"sid":\s*"(\w+)"', r.content)[0]
        self.user_vote(3, self.product.pk, sid, 2)
        self.user_vote(4, self.product.pk, sid, 6)
        r = self.client.get('/poker/stop/?pid=%s&sid=%s'%(self.product.pk,sid))
        self.assertTrue(re.match(r'{"status":\s*"OK"}', r.content))
        vs = Vote.objects.all()
        self.assertEqual(vs.count(), 3)
        self.assertEqual(vs[0].status, "CLOSED")
        self.assertEqual(vs[1].status, "CLOSED")
        self.assertEqual(vs[2].status, "CLOSED")
        
        # test start to clear the precious session
        sid2 = self.create_session()
        self.assertNotEqual(sid2, sid)
        self.assertEqual(Vote.objects.count(), 1)
        
    def create_session(self, ux=0, product=None, client=None):
        if not client: client = self.client
        client.login(username='user_%d'%ux,password='pass_%d'%ux)
        if not product: product = self.product.pk
        r = client.get('/poker/start/?pid=%s'%product)
        if not r.content:
            print 'create_session(',ux,product,client
        return re.findall(r'"sid":\s*"(\w+)"', r.content)[0] #sid
        
    def user_vote(self, user, pid, sid, vote):
        client = Client()
        client.login(username='user_%d'%user, password='pass_%d'%user)
        return client.get('/poker/vote/?pid=%s&sid=%s&vote=%s'%(pid,sid,vote))
        
    def testCollect(self):
        sid = self.create_session()
        self.user_vote(2, self.product.pk, sid, 5)
        r = self.client.get('/poker/collect/?pid=%s&sid=%s' % (self.product.pk,sid))
#        self.assertTrue(re.match(r'\{"status": "STARTED", "votes": \{"1": "\*", "3": "5"\}\}', r.content))
        ds = simplejson.loads(r.content)
        self.assertEqual(ds['status'], 'STARTED')
        self.assertEqual(ds['votes'], {'%d'%self.users[0].pk:'*','%d'%self.users[2].pk:'*'})
        self.user_vote(3, self.product.pk, sid, 4)
        r = self.client.get('/poker/collect/?pid=%s&sid=%s' % (self.product.pk,sid))
        ds = simplejson.loads(r.content)
        self.assertEqual(ds['votes'], {'%d'%self.users[0].pk:'*','%d'%self.users[2].pk:'*','%d'%self.users[3].pk:'*'})
        self.user_vote(4, self.product.pk, sid, 2)
        client4 = Client()
        client4.login(username='user_4',password='pass_4')
        # stop the session
        self.client.get('/poker/stop/?pid=%s&sid=%s' % (self.product.pk,sid))
        r = client4.get('/poker/collect/?pid=%s&sid=%s' % (self.product.pk,sid))
        ds = simplejson.loads(r.content)
        self.assertEqual(sorted(ds['votes'].values()), ['*','2','4','5'])
        
    def testStatus(self):
        client3 = Client()
        client3.login(username='user_3',password='pass_3')
        r = client3.get('/poker/status/?pid=%s'%self.product.pk)
        self.assertTrue(re.match('{"status":\s*"IDLE"}', r.content))
        sid = self.create_session()
        r = self.client.get('/poker/status/?pid=%s'%self.product.pk)
        self.assertTrue(re.match('{"status":\s*"STARTED"', r.content))
        r = client3.get('/poker/status/?pid=%s'%self.product.pk)
        self.assertTrue(re.match('{"status":\s*"STARTED"', r.content))
        self.client.get('/poker/stop/?pid=%s&sid=%s'%(self.product.pk,sid))
        r = client3.get('/poker/status/?pid=%s'%self.product.pk)
        self.assertTrue(re.match('{"status":\s*"CLOSED"', r.content))
        
    def testVote(self):
        sid = self.create_session()
        self.client.get('/poker/vote/?pid=%s&sid=%s&vote=5'%(self.product.pk,sid))
        v = Vote.objects.get(session=sid)
        self.assertEqual(v.vote, '5')
#        r = client2.get('/poker/vote/?pid=1&sid=%s&vote=3')
        r = self.user_vote(2, self.product.pk, sid, 3)
        self.assertTrue(re.match(r'{"status":\s*"OK"}', r.content))
        vs = Vote.objects.all()
        self.assertEqual(vs.count(), 2)
        self.assertEqual(vs[1].vote, '3')
    
class PokerModelTest(TestCase):
    def setUp(self):
        N = 5
        self.users = []
        self.team = Group.objects.create(name='Team_1')
        for i in xrange(N):
            u = User.objects.create_user('user_%d'%i, 'user%d@example.com', 'pass_%d'%i)
            u.groups.add(self.team)
            self.users.append(u)
#            print 'user[%d].pk=%d'%(i,u.pk)
        self.product = Product.objects.create(name='Product_1',owner=self.users[0],master=self.users[0],team=self.team)
#        print 'self.product.pk=',self.product.pk
        
    def tearDown(self):
        Product.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()

    def testGeneral(self):
        """ Test multi-product concurrency. """
        sid1 = Vote.objects.start(self.users[0], self.product.pk)['sid']
        product2 = Product.objects.create(name='Product_2',owner=self.users[2],master=self.users[2],team=self.team)
        sid2 = Vote.objects.start(self.users[2], product2.pk)['sid']
        Vote.objects.get_or_create(session=sid1, product=self.product.pk, voter=self.users[1], vote='1')
        Vote.objects.get_or_create(session=sid1, product=self.product.pk, voter=self.users[3], vote='3')
        Vote.objects.get_or_create(session=sid2, product=product2.pk, voter=self.users[2], vote='2')
        Vote.objects.get_or_create(session=sid2, product=product2.pk, voter=self.users[4], vote='4')
        vs = Vote.objects.all()
        self.assertEqual(vs.count(), 6)
        d = Vote.objects.status(self.product.pk)
        self.assertEqual(d,{"status":"STARTED","sid":sid1})
        qs = Vote.objects.collect(self.product.pk, sid1)
        self.assertEqual(qs.count(),3)
        sid3 = Vote.objects.start(self.users[0], self.product.pk)['sid']
        self.assertEqual(Vote.objects.count(), 4)
        self.assertEqual(Vote.objects.collect(self.product.pk,sid1).count(), 0)
