import importlib.util
import json
import tempfile
import time
import unittest
import threading
from pathlib import Path

plugin_file = Path(__file__).with_name('jtk_coupon.py')
if not plugin_file.is_file():
    plugin_file = Path(__file__).resolve().parents[1] / 'plugins' / '聚推客返利助手.py'
spec = importlib.util.spec_from_file_location('jtk_coupon', plugin_file)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class Sender:
    def __init__(self, uid='1', im='qq', chat='', admin=False):
        self.uid, self.im, self.chat, self.admin = uid, im, chat, admin
    def getUserID(self): return self.uid
    def getImtype(self): return self.im
    def getChatID(self): return self.chat
    def isAdmin(self): return self.admin


class Middleware:
    def __init__(self): self.values = {'api_key': 'synthetic-test-key', 'sid_secret': 'synthetic-persistent-sid-secret'}
    def bucketGet(self, bucket, key): return self.values.get(key)
    def bucketSet(self, bucket, key, value): self.values[key] = value


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = p.State(Path(self.temp.name) / 'state.sqlite3')
        self.mw = Middleware()
    def tearDown(self):
        self.state.close()
        self.temp.cleanup()
    def test_domains(self):
        self.assertEqual(p.platform_of('https://item.jd.com/123.html'), 'jd')
        for url in ['https://jd.com.evil.test/a', 'https://eviljd.com/a', 'https://jd.com@evil.test/a', 'file:///x', 'https://jd.com:9000/a']:
            self.assertEqual(p.platform_of(url), '')
    def test_extract(self):
        self.assertEqual(p.extract_link('分享 https://item.jd.com/123.html?a=1&amp;b=2。'), 'https://item.jd.com/123.html?a=1&b=2')
        with self.assertRaises(p.PluginError): p.extract_link('https://jd.com/a https://jd.com/b')
    def test_money(self):
        self.assertEqual(p.amount('100.00'), '100')
        self.assertEqual(p.amount('0.10'), '0.1')
        self.assertEqual(p.amount(0), '0')
        self.assertIsNone(p.amount(float('nan')))
        self.assertIsNone(p.amount(-1))
    def test_jd_request_has_no_own_jd_credentials(self):
        calls = []
        def request(path, fields, get):
            calls.append((path, fields, get))
            return {'code': 1, 'data': {'link': 'https://u.jd.com/test'}}
        client = p.Client('synthetic-test-key', transport=request)
        client.goods('https://item.jd.com/1.html', 'sid1')
        self.assertEqual(calls[0][0], '/jd/get_goods_link')
        self.assertEqual(set(calls[0][1]), {'apikey', 'goods_link', 'sid'})
    def test_coupon_and_price(self):
        result = p.product_message({'skuName': '商品', 'link': 'https://u.jd.com/test', 'is_coupon': 1,
            'couponInfo': [{'discount': 10, 'quota': 99}], 'priceInfo': {'lowestCouponPrice': 89}})
        self.assertIn('满99减10元', result)
        self.assertIn('券后参考价：¥89', result)
        self.assertIn('以购买页面为准', result)
    def test_expired_coupon_not_claimed(self):
        result = p.product_message({'link': 'https://u.jd.com/test', 'is_coupon': 1,
            'couponInfo': [{'discount': 10, 'quota': 99, 'takeEndTime': 1}]})
        self.assertNotIn('满99减10元', result)
    def test_no_coupon(self):
        self.assertIn('未查到优惠券', p.product_message({'link': 'https://u.jd.com/test', 'is_coupon': 0}))
    def test_upstream_error_does_not_echo_key(self):
        client = p.Client('synthetic-test-key', transport=lambda *args: {'code': 0, 'msg': 'bad synthetic-test-key'})
        with self.assertRaises(p.PluginError) as error: client.activities()
        self.assertNotIn('synthetic-test-key', str(error.exception))
    def test_sid_isolation(self):
        one = p.Plugin(Sender(), self.mw, self.state).identity()
        two = p.Plugin(Sender(im='tg'), self.mw, self.state).identity()
        three = p.Plugin(Sender(uid='2'), self.mw, self.state).identity()
        self.assertEqual(len(one), 28)
        self.assertEqual(len({one, two, three}), 3)
    def test_first_user_cannot_initialize_channel_key(self):
        self.mw.values.pop('sid_secret')
        with self.assertRaises(p.PluginError): p.Plugin(Sender(), self.mw, self.state).identity()
        sid = p.Plugin(Sender(admin=True), self.mw, self.state).identity()
        self.assertEqual(len(sid), 28)
        self.assertTrue(self.mw.values['sid_secret'])
    def test_private_commands_not_leaked_to_group(self):
        plugin = p.Plugin(Sender(chat='123'), self.mw, self.state)
        for command in ['返利订单', '返利记录', '返利渠道', '清空返利记录']:
            text, _ = plugin.handle(command)
            self.assertIn('私聊', text)
    def test_orders_filter_sid_even_if_provider_does_not(self):
        client = p.Client('k', transport=lambda *args: {'code': 1, 'data': {'data': [
            {'sid': 'mine', 'order_sn': '12345678901234567890'}, {'sid': 'other', 'order_sn': 'hidden'}]}})
        self.assertEqual([x['order_sn'] for x in client.orders('mine')], ['12345678901234567890'])
    def test_rate_limit(self):
        self.assertTrue(all(self.state.allow('u1') for _ in range(8)))
        self.assertFalse(self.state.allow('u1'))
        self.assertTrue(self.state.allow('u2'))
    def test_success_cache_and_own_history(self):
        data = {'link': 'https://u.jd.com/test', 'skuName': 'test'}
        self.state.remember('k1', 'u1', data)
        self.assertEqual(self.state.cached('k1'), data)
        self.assertEqual(self.state.history('u2'), [])
        self.assertEqual(len(self.state.history('u1')), 1)
        self.state.clear_history('u1')
        self.assertEqual(self.state.history('u1'), [])
    def test_image_allowlist(self):
        self.assertEqual(p.product_image({'imageInfo': {'imageList': [{'url': 'http://127.0.0.1/private'}]}}), '')
        self.assertTrue(p.product_image({'imageInfo': {'imageList': [{'url': 'https://img14.360buyimg.com/x.jpg'}]}}))
    def test_non_admin_cannot_run_diagnostics(self):
        self.assertIn('仅管理员', p.Plugin(Sender(), self.mw, self.state).handle('返利检测')[0])
    def test_success_repeated_conversion_uses_cache(self):
        calls = []
        class Client:
            def goods(self, *args):
                calls.append(args)
                return {'skuName': 'item', 'link': 'https://u.jd.com/test', 'is_coupon': 0}
        plugin = p.Plugin(Sender(), self.mw, self.state, Client())
        plugin.handle('https://item.jd.com/1.html')
        plugin.handle('https://item.jd.com/1.html')
        self.assertEqual(len(calls), 1)
    def test_new_aggregate_parses_then_converts_with_stable_sid(self):
        calls = []
        def transport(path, fields, get):
            calls.append((path, fields))
            if path.endswith('wn_convert'):
                return {'code': 1, 'data': {'goodsId': 'opaque-id', 'source': 'jd', 'goodsName': 'item', 'marketPrice': 100, 'price': 90, 'discount': 10}}
            return {'code': 1, 'data': {'url': 'https://u.jd.com/test', 'goodsName': 'item', 'price': 90, 'discount': 10}}
        client = p.Client('secret', pub_id='publisher', transport=transport)
        data = client.goods('https://item.jd.com/123.html', 'stable-sid')
        self.assertEqual(calls[0][0], '/union/wn_convert')
        self.assertEqual(calls[1][1]['sid'], 'stable-sid')
        self.assertEqual(calls[1][1]['pub_id'], 'publisher')
        self.assertNotIn('apikey', calls[1][1])
        self.assertIn('优惠券：10元', p.product_message(data))
    def test_aggregate_platform_mismatch_cannot_make_link(self):
        client = p.Client('secret', pub_id='publisher', transport=lambda *args: {'code':1, 'data':{'goodsId':'other','source':'taobao'}})
        with self.assertRaises(p.PluginError): client.goods('https://item.jd.com/123.html', 'sid')
    def test_all_recognized_ecommerce_domains(self):
        urls = {'jd':'https://item.jd.com/1.html','taobao':'https://detail.tmall.com/item.htm?id=1',
            'pdd':'https://mobile.yangkeduo.com/goods.html?goods_id=1','vip':'https://m.vip.com/product-1.html',
            'kaola':'https://www.kaola.com/product/1.html','douyin':'https://v.douyin.com/abc/',
            'kuaishou':'https://v.kuaishou.com/abc/'}
        for source, url in urls.items():
            with self.subTest(source=source): self.assertEqual(p.platform_of(url), source)
    def test_vip_discount_is_not_misrepresented_as_cash_coupon(self):
        def transport(path, fields, get):
            return {'code':1,'data':{'goodsId':'v','source':'vip','goodsName':'item','price':80,'discount':8,
                **({'url':'https://m.vip.com/test'} if path.endswith('/convert') else {})}}
        data = p.Client('secret',pub_id='pub',transport=transport).goods('https://m.vip.com/test','sid')
        self.assertEqual(data['is_coupon'],0)
        self.assertNotIn('8元',p.product_message(data))
    def test_curated_products_are_converted_before_reply(self):
        calls=[]
        def transport(path,fields,get):
            calls.append((path,fields))
            if path.endswith('goods_channel'):
                return {'code':1,'data':{'list':[{'goodsId':'candidate','goodsName':'current','price':10}]}}
            return {'code':1,'data':{'url':'https://u.jd.com/test','goodsName':'current','price':10,'discount':0}}
        data=p.Client('key',pub_id='publisher',transport=transport).featured('sid')
        self.assertEqual(data[0]['link'],'https://u.jd.com/test')
        self.assertEqual(calls[1][1]['goodsId'],'candidate')
        self.assertEqual(calls[1][1]['sid'],'sid')
    def test_all_conversion_sources_propagate_attribution(self):
        for source,(_,domains) in p.PLATFORMS.items():
            with self.subTest(source=source):
                calls=[]
                def transport(path,fields,get):
                    calls.append(fields)
                    if path.endswith('wn_convert'):
                        return {'code':1,'data':{'goodsId':'opaque','source':source,'goodsName':'item'}}
                    return {'code':1,'data':{'url':'https://example.com/promotion','goodsName':'item','price':10}}
                p.Client('key',pub_id='pub',transport=transport).goods('https://'+domains[0]+'/item','stable')
                self.assertEqual(calls[-1]['sid'],'stable')
                self.assertEqual(calls[-1]['source'],source)
    def test_upstream_no_orders_is_a_normal_empty_result(self):
        client=p.Client('key',transport=lambda *args:{'code':0,'msg':'【对应条件内无数据】'})
        self.assertEqual(client.orders('sid'),[])
    def test_false_string_is_not_administrator_permission(self):
        sender=Sender()
        sender.isAdmin=lambda:'false'
        self.assertFalse(p.Plugin(sender,self.mw,self.state).admin())

    def item(self, provider='jtk', commission='2.00', pid='123', source='taobao'):
        return {'_provider':provider,'_commission':commission,'_product_id':pid,'_source':source,
            'skuName':'普通商品','link':'https://uland.taobao.com/coupon/a','is_coupon':0,
            'priceInfo':{'lowestCouponPrice':10},'shopInfo':{'shopName':'同一店铺'}}

    def test_select_largest_amount_not_string_or_rate(self):
        result=p.select_result([self.item('jtk','9.9'),self.item('ztk','12.01')])
        self.assertEqual(result['_provider'],'ztk')
        self.assertIn('已比较',result['_selection'])

    def test_fee_adjustment_changes_winner(self):
        result=p.select_result([self.item('jtk','9'),self.item('ztk','10')],factors={'ztk':.8})
        self.assertEqual(result['_provider'],'jtk')

    def test_unknown_is_not_zero(self):
        result=p.select_result([self.item('jtk',None),self.item('ztk','10')])
        self.assertEqual(result['_provider'],'jtk')
        self.assertIn('不足',result['_selection'])
        self.assertEqual(p.select_result([self.item('jtk','0'),self.item('ztk','1')])['_provider'],'ztk')

    def test_different_product_ids_cannot_compete(self):
        result=p.select_result([self.item('jtk','1','123'),self.item('ztk','20','124')])
        self.assertEqual(result['_provider'],'jtk')
        self.assertIn('不足',result['_selection'])

    def test_opaque_ids_require_same_title_shop_price(self):
        a,b=self.item('jtk','1','opaque'),self.item('ztk','2','123')
        self.assertTrue(p.comparable(a,b))
        b['skuName']='其他规格'
        self.assertFalse(p.comparable(a,b))

    def test_parallel_calls_and_one_failure_fallback(self):
        barrier=threading.Barrier(2,timeout=2)
        item=self.item()
        class Good:
            def goods(self,*args): barrier.wait(); return item
        class Bad:
            def goods(self,*args): barrier.wait(); raise p.PluginError('授权无效')
        result=p.ComparisonClient({'jtk':Good(),'ztk':Bad()}).goods('https://item.taobao.com/item.htm?id=123','sid')
        self.assertEqual(result['_provider'],'jtk')
        self.assertIn('ztk',result['_errors'])

    def test_jd_never_calls_zhetaoke(self):
        item=self.item(source='jd')
        class Good:
            def goods(self,*args): return item
        class MustNotCall:
            def goods(self,*args): raise AssertionError('JD sent to Zhetaoke')
        result=p.ComparisonClient({'jtk':Good(),'ztk':MustNotCall()}).goods('https://item.jd.com/123.html','sid')
        self.assertNotIn('ztk',result['_errors'])

    def test_no_affiliate_words_in_public_render_and_help(self):
        item=p.select_result([self.item('jtk','10'),self.item('ztk','12')],{'private':'返利接口错误'})
        item['skuName']='返利商品 佣金 推广 渠道'
        plugin=p.Plugin(Sender(),self.mw,self.state)
        text=plugin.render(item)
        for word in ('返利','返佣','佣金','推广','渠道','聚推客','折淘客'):
            self.assertNotIn(word,text)
            self.assertNotIn(word,p.HELP)
        self.assertNotIn('private',text)

    def test_admin_amount_private_only_and_switch(self):
        item=p.select_result([self.item('jtk','10'),self.item('ztk','12')])
        private=p.Plugin(Sender(admin=True),self.mw,self.state)
        self.assertIn('预估返利金额：¥12',private.render(item))
        group=p.Plugin(Sender(admin=True,chat='group'),self.mw,self.state)
        self.assertNotIn('返利',group.render(item))
        self.mw.values['admin_amount']='false'
        self.assertNotIn('返利',private.render(item))

    def test_shared_cache_never_contains_rendered_admin_text(self):
        item=self.item(commission='77')
        class Client:
            def goods(self,*args): return item
        admin=p.Plugin(Sender(admin=True),self.mw,self.state,Client())
        self.assertIn('返利',admin.handle('https://item.taobao.com/item.htm?id=123')[0])
        ordinary=p.Plugin(Sender(),self.mw,self.state,Client())
        self.assertNotIn('返利',ordinary.handle('https://item.taobao.com/item.htm?id=123')[0])

    def test_config_change_invalidates_cache(self):
        plugin=p.Plugin(Sender(),self.mw,self.state)
        before=plugin.cache_key('sid','link')
        self.mw.values['ztk_key']='another-synthetic-key'
        self.assertNotEqual(before,plugin.cache_key('sid','link'))

    def test_configuration_bounds(self):
        plugin=p.Plugin(Sender(),self.mw,self.state)
        for value,expected in [('nan',8),('-1',3),('99',15),('bad',8)]:
            self.mw.values['request_timeout']=value
            self.assertEqual(plugin.number('request_timeout',8,3,15),expected)

    def test_history_disabled_and_zero_cache_ttl(self):
        self.state.remember('key','sid',self.item(),ttl=0,save_history=False)
        self.assertIsNone(self.state.cached('key'))
        self.assertEqual(self.state.history('sid'),[])

    def test_ztk_normalizes_amount_and_stable_pdd_tracking(self):
        calls=[]
        def transport(endpoint,params):
            calls.append(params)
            return {'status':200,'plat':3,'tao_id':'123','title':'商品','tkfee3':'5.12','tkrate3':'90',
                'size':'20','quanhou_jiage':'10','is_youquan':'1','coupon_info_money':'10',
                'result_url':'https://mobile.yangkeduo.com/test'}
        client=p.ZhetaokeClient('synthetic','authsid','mm_1_2_3',transport=transport)
        data=client.goods('https://mobile.yangkeduo.com/goods.html?goods_id=123','user-sid')
        self.assertEqual(data['_commission'],'5.12')
        self.assertEqual(json.loads(calls[0]['custom_parameters'])['uid'],'user-sid')
        self.assertNotIn('unionId',calls[0])

    def test_ztk_missing_authorization_and_jd_are_rejected(self):
        calls=[]
        client=p.ZhetaokeClient('synthetic',transport=lambda *args:calls.append(args))
        for link in ['https://item.jd.com/123.html','https://item.taobao.com/item.htm?id=123']:
            with self.assertRaises(p.PluginError):client.goods(link,'sid')
        self.assertEqual(calls,[])

    def test_ztk_error_never_echoes_raw_key_or_account_data(self):
        client=p.ZhetaokeClient('secret-key',transport=lambda *args:{'status':301,'msg':'secret-key account-token'})
        with self.assertRaises(p.PluginError) as caught:client.accounts()
        self.assertNotIn('secret-key',str(caught.exception))
        self.assertNotIn('account-token',str(caught.exception))

    def test_ztk_empty_product_is_not_a_zero_price_success(self):
        for title in ('', '0'):
            client=p.ZhetaokeClient('k','s','mm_1_2_3',transport=lambda *args:{
                'status':200,'plat':1,'tao_id':'123','title':title,'size':'0','tkfee3':'0',
                'result_url':'https://item.taobao.com/item.htm?id=123&ali_trackid=sample'})
            with self.assertRaises(p.PluginError):
                client.goods('https://item.taobao.com/item.htm?id=123','sid')

    def test_ztk_platform_mismatch(self):
        client=p.ZhetaokeClient('k','s','mm_1_2_3',transport=lambda *args:{'status':200,'plat':2,'result_url':'https://u.jd.com/a'})
        with self.assertRaises(p.PluginError):client.goods('https://item.taobao.com/item.htm?id=123','sid')

    def test_ztk_never_fabricates_vip_pid_or_taobao_relation_id(self):
        calls=[]
        def request(endpoint,params):
            calls.append(params)
            return {'status':200,'plat':5 if 'vip.com' in params['tkl'] else 1,
                'result_url':'https://m.vip.com/test','tao_id':'123','title':'商品'}
        client=p.ZhetaokeClient('k','sid','mm_1_2_3',transport=request)
        client.goods('https://m.vip.com/product-123.html','user-hmac')
        self.assertNotIn('chanTag',calls[-1])
        client.goods('https://item.taobao.com/item.htm?id=123','user-hmac')
        self.assertNotIn('relation_id',calls[-1])
        client.relation_id='registered-channel'
        client.goods('https://item.taobao.com/item.htm?id=123','user-hmac')
        self.assertEqual(calls[-1]['relation_id'],'registered-channel')

    def test_generic_error_does_not_expose_credentials_in_main(self):
        import sys,types
        sender=Sender()
        sender.getMessage=lambda:'https://item.taobao.com/item.htm?id=123'
        replies=[]
        sender.reply=replies.append
        middleware=types.SimpleNamespace(Sender=lambda _:sender,getSenderID=lambda:'x')
        sys.modules['middleware']=middleware
        from unittest.mock import patch
        with patch.object(p,'State',return_value=self.state),patch.object(p.Plugin,'handle',side_effect=p.PluginError('返利 secret-key')):
            p.main()
        self.assertNotIn('secret-key',replies[0])
        self.assertNotIn('返利',replies[0])
        # main closes the state; reopen for tearDown.
        self.state=p.State(Path(self.temp.name)/'state.sqlite3')


if __name__ == '__main__':
    unittest.main()
