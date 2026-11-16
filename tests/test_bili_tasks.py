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
 def test_vip_status_supports_current_nav_fields(self):
  self.assertEqual(m.vip_status({'vip':{'status':1,'type':1}}),1)
  self.assertEqual(m.vip_status({'vip':{'vipStatus':0}}),0)
  self.assertEqual(m.vip_status({'vipStatus':1}),1)
  self.assertIsNone(m.vip_status({}))
 def test_active_vip_enables_member_tasks(self):
  self.calls=[];info={**self.info,'vip':{'status':1,'type':1}}
  with patch.object(m,'call',side_effect=self.api):m.run_tasks(self.session,info,{'live':'0','manga':'0','watch':'0','share':'0'})
  self.assertTrue(any(x[1].endswith('/score/task/sign2') for x in self.calls))
  self.assertEqual(sum(x[1].endswith('/vip/privilege/receive') for x in self.calls),2)
 def test_signed_vip_is_verified_and_not_signed_twice(self):
  self.calls=[];info={**self.info,'vip':{'status':1}}
  def api(session,method,url,**kwargs):
   if url.endswith('/three_days_sign'):
    self.calls.append((method,url,kwargs));return {'code':0,'data':{'three_day_sign':{'signed':True,'score':5},'big_point':{'point':42}}}
   return self.api(session,method,url,**kwargs)
  with patch.object(m,'call',side_effect=api):r=m.run_tasks(self.session,info,{'live':'0','manga':'0','watch':'0','share':'0','vip':'0'})
  self.assertFalse(any(x[1].endswith('/score/task/sign2') for x in self.calls));self.assertTrue(any('今日已完成' in line and '42' in line for line in r['lines']))
 def test_manga_already_signed_is_not_a_failure(self):
  self.calls=[]
  def api(session,method,url,**kwargs):
   if url.endswith('/ClockIn'):return {'code':1,'msg':'不能重复签到~'}
   return self.api(session,method,url,**kwargs)
  with patch.object(m,'call',side_effect=api):r=m.run_tasks(self.session,self.info,{'live':'0','watch':'0','share':'0','vip':'0'})
  self.assertIn('漫画签到：今日已签到',r['lines'])
 def test_free_tasks_verify_success_after_response_error(self):
  def data(state):return {'point_info':{'point':105},'task_info':{'modules':[{'common_task_item':[{'task_code':'bonus','state':state},{'task_code':'vipmallbuy','state':1}]}]}}
  with patch.object(m,'vip_tasks_info',side_effect=[data(1),data(3),data(3)]),patch.object(m,'call',return_value={'code':-999}) as post:
   logs=m.vip_free_tasks(self.session,'csrf')
  self.assertTrue(any('福利大积分：已完成' in line for line in logs));self.assertEqual(post.call_count,1)
  self.assertEqual(post.call_args.kwargs['json']['taskCode'],'bonus')
 def test_completed_tasks_are_never_replayed(self):
  d={'point_info':{'point':195},'task_info':{'modules':[{'common_task_item':[{'task_code':'bonus','state':3},{'task_code':'vipmallbuy','state':1}]}]}}
  with patch.object(m,'vip_tasks_info',return_value=d),patch.object(m,'call') as post:
   logs=m.vip_free_tasks(self.session,'csrf')
  post.assert_not_called();self.assertIn('福利大积分：已完成',logs)
 def test_vip_experience_requires_confirmed_eligibility(self):
  with patch.object(m,'call',return_value={'code':0,'data':{'list':[{'type':9,'state':1}]}}) as fn:
   self.assertIn('已领取',m.vip_experience_task(self.session,'csrf'));self.assertEqual(fn.call_count,1)
 def test_detailed_query_displays_available_information(self):
  info={**self.info,'uname':'test','vip':{'status':1},'level_info':{'current_level':4,'current_exp':8000,'next_exp':10800},'wallet':{'bcoin_balance':0,'coupon_balance':2}}
  sign={'three_day_sign':{'signed':True,'score':5,'count':1,'duration':7},'big_point':{'point':195}}
  tasks={'task_info':{'modules':[{'common_task_item':[{'title':'福利任务','state':3,'subtitle':'<span>+100</span>'}]}]}}
  def api(session,method,url,**kwargs):
   self.assertEqual(method,'GET')
   if url.endswith('/stat'):return {'code':0,'data':{'following':10,'follower':2}}
   return {'code':0,'data':{'silver':462,'gold':0}}
  with patch.object(m,'call',side_effect=api),patch.object(m,'vip_sign_info',return_value=sign),patch.object(m,'vip_tasks_info',return_value=tasks):
   result=m.detailed_info(self.session,info,{'login':True,'watch':True,'share':True,'coins':0})
  for value in ('距下一级2800','关注：10','银瓜子：462','大积分：195','福利任务：已完成'):
   self.assertIn(value,result)
 def test_experience_network_error_retried(self):
  results=[{'code':-999},{'code':0,'data':{'watch':True}}]
  with patch.object(m,'call',side_effect=results) as fn,patch.object(m.time,'sleep'):
   self.assertTrue(m.reward_info(self.session)['watch']);self.assertEqual(fn.call_count,2)
 def test_experience_business_error_not_retried(self):
  with patch.object(m,'call',return_value={'code':-403,'message':'blocked'}) as fn:
   errors=[];self.assertIsNone(m.reward_info(self.session,errors));self.assertEqual(fn.call_count,1);self.assertIn('-403',errors[0])
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
