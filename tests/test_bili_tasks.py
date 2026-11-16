import sys,types,importlib.util,unittest,os
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,'/data/plugins/python_packages/bili_tasks_vendor')
a=types.ModuleType('autman');a.middleware=types.SimpleNamespace();sys.modules['autman']=a
spec=importlib.util.spec_from_file_location('bili',os.environ.get('BILI_PLUGIN',str(Path(__file__).resolve().parents[1]/'plugins'/'哔哩哔哩任务.py')));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def setUp(self):
  self.session=m.make_session('SESSDATA=secret;bili_jct=csrf;DedeUserID=1');self.info={'mid':1,'money':30,'vip':{'vipStatus':0}}
 def api(self,session,method,url,**kw):
  self.calls.append((method,url,kw))
  if url.endswith('/exp/reward'):return {'code':0,'data':{'watch':True,'share':True,'coins':30}}
  if url.endswith('/coin/today/exp'):return {'code':0,'data':30}
  if url.endswith('/popular'):return {'code':0,'data':{'list':[{'aid':i,'bvid':'BV'+str(i),'owner':{'mid':2}} for i in range(1,5)]}}
  if url.endswith('/archive/coins'):return {'code':0,'data':{'multiply':0}}
  return {'code':0,'data':{}}
 def test_coin_disabled_by_default(self):
  self.calls=[]
  with patch.object(m,'call',side_effect=self.api):r=m.run_tasks(self.session,self.info,{'live':'0','manga':'0','vip':'0'})
  self.assertTrue(r['ok']);self.assertFalse(any(x[1].endswith('/coin/add') for x in self.calls))
 def test_coin_target_progress(self):
  self.calls=[]
  with patch.object(m,'call',side_effect=self.api),patch.object(m.time,'sleep'):
   m.run_tasks(self.session,self.info,{'coin_count':'5','reserve':'10','live':'0','manga':'0','vip':'0'})
  self.assertEqual(sum(x[1].endswith('/coin/add') for x in self.calls),2)
 def test_failed_progress_skips_spend(self):
  self.calls=[]
  def api(*a,**k):
   if a[2].endswith('/coin/today/exp'):return {'code':-403}
   return self.api(*a,**k)
  with patch.object(m,'call',side_effect=api):m.run_tasks(self.session,self.info,{'coin_count':'5','live':'0','manga':'0','vip':'0'})
  self.assertFalse(any(x[1].endswith('/coin/add') for x in self.calls))
 def test_private_binding_and_group_refusal(self):
  saved={};sent=[]
  class Sender:
   def getMessage(self):return 'B站登录'
   def getChatID(self):return '0'
   def getImtype(self):return 'qq'
   def getUserID(self):return '1'
   def reply(self,text):sent.append(text)
  sender=Sender()
  mw=types.SimpleNamespace(Sender=lambda _:sender,getSenderID=lambda:'id',bucketSet=lambda bucket,key,value:saved.update({(bucket,key):value}) or True)
  with patch.object(m,'middleware',mw),patch.object(m,'qr_login',return_value='SESSDATA=test;bili_jct=csrf'),patch.object(m,'user_info',return_value={'mid':7,'uname':'test'}),patch.object(m,'reward_info',return_value={}):m.main()
  self.assertEqual(len(saved),1);self.assertFalse(any('SESSDATA' in x or 'csrf' in x for x in sent))
  saved.clear();sender.getChatID=lambda:'group';sent.clear()
  with patch.object(m,'middleware',mw),patch.object(m,'qr_login') as qr:m.main()
  qr.assert_not_called();self.assertFalse(saved);self.assertTrue(any('私聊' in x for x in sent))
 def test_zero_flags(self):
  self.assertFalse(m.flag({'watch':0},'watch'));self.assertEqual(m.number({'reserve':0},'reserve',10,100),0)
 def test_bad_login_stops(self):
  with patch.object(m,'call',return_value={'code':-101,'data':{'isLogin':False}}):self.assertIsNone(m.user_info(self.session))
 def test_qrcode_url_allowed_and_redirection_cookies(self):
  calls=[]
  def call(s,method,url,**kw):
   calls.append(url)
   if url.endswith('/generate'):return {'code':0,'data':{'url':'https://account.bilibili.com/test','qrcode_key':'k'}}
   return {'code':0,'data':{'code':0,'url':'https://passport.bilibili.com/?SESSDATA=test&bili_jct=csrf&DedeUserID=7'}}
  sender=types.SimpleNamespace(reply=lambda *a:None,replyImage=lambda *a:None)
  proc=types.SimpleNamespace(stdout='data:image/png;base64,dGVzdA==')
  with patch.object(m,'call',side_effect=call),patch.object(m.time,'sleep'),patch.object(m.subprocess,'run',return_value=proc):
   cookie=m.qr_login(sender)
  self.assertIn('SESSDATA=test',cookie);self.assertIn('bili_jct=csrf',cookie)
unittest.main(verbosity=2)


