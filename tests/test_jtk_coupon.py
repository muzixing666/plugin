import importlib.util
import json
import tempfile
import time
import unittest
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
        self.assertIn('不代表已到账', result)
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


if __name__ == '__main__':
    unittest.main()
