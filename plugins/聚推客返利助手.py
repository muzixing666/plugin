# [title: 聚推客返利助手]
# [icon: https://cdn.jsdelivr.net/gh/muzixing666/plugin@main/icons/rebate.svg]
# [language: python]
# [author: Codex]
# [version: 1.1.0]
# [public: true]
# [open_source: true]
# [disable: false]
# [priority: 100]
# [rule: (?i)https?://[^\s]*(?:jd\.com|3\.cn|jingxi\.com|taobao\.com|tmall\.com|tb\.cn|tb\.com|pinduoduo\.com|yangkeduo\.com|pdd\.cn|vip\.com|kaola\.com|douyin\.com|iesdouyin\.com|jinritemai\.com|kuaishou\.com|gifshow\.com|kwaixiaodian\.com)[^\s]*|^(?:返利帮助|返利菜单|查券帮助|返利平台|返利精选|返利检测|返利活动(?:\s+\S+)?|返利订单|我的返利订单|返利渠道|美团外卖优惠|淘宝闪购优惠|返利记录|清空返利记录)$|^查券\s+.+$|^返利测试\s+.+$]
# [description: 发送多平台购物链接，返回商品、优惠券和领券购买链接；外卖活动、个人跟单、历史记录与管理员检测。复用面板所有社媒接入，不需要自有京东联盟账号。]
# [param: {"required":true,"key":"jtk_coupon.api_key","bool":false,"name":"聚推客API Key","desc":"聚推客个人中心获取；只存面板配置，不要写进插件源码。"}]
# [param: {"required":false,"key":"jtk_coupon.pub_id","bool":false,"name":"聚推客pub_id","desc":"个人中心的推广者身份标识；新版京东、淘宝、拼多多商品查券需要。"}]
# [param: {"required":false,"key":"jtk_coupon.sid_secret","bool":false,"name":"渠道签名密钥","desc":"首次使用自动生成，长期保留；更换会影响旧订单归属。"}]
# [param: {"required":false,"key":"jtk_coupon.send_image","bool":true,"name":"发送商品图","desc":"查券成功后附一张商品图；关闭后只发文本。"}]
# [param: {"required":false,"key":"jtk_coupon.mt_act_id","bool":false,"name":"美团活动ID","desc":"管理员发送 返利活动 美团 查询当前活动ID。"}]
# [param: {"required":false,"key":"jtk_coupon.ele_act_id","bool":false,"name":"淘宝闪购活动ID","desc":"管理员发送 返利活动 外卖 查询当前活动ID。"}]

"""AutMan Python middleware plugin. Python 3.9+, standard library only."""
import datetime as dt
import hashlib
import hmac
import html
import json
import math
import os
import re
import secrets
import socket
import sqlite3
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path

BUCKET = 'jtk_coupon'
VERSION = '1.1.0'
API = 'https://api.jutuike.com'
AGGREGATE_API = 'https://api.act.jutuike.com'
CN = dt.timezone(dt.timedelta(hours=8))
HELP = '''🛍 聚推客返利助手
直接发购物链接，或：查券 链接
识别京东、淘宝/天猫、拼多多、唯品会、考拉、抖音、快手；实际可转范围由聚推客接口决定。
回复：商品名称、店铺、优惠券、参考价格、领券购买链接。

🍱 美团外卖优惠 / 淘宝闪购优惠
🧾 返利订单：私聊查看最近1小时的本人订单
🛒 返利精选：查看平台当前可推广的好券商品
🕘 返利记录：最近5次成功查券
🪪 返利渠道：查看本人渠道标识
🧹 清空返利记录：只清本人的查券记录

优惠券、渠道预估佣金不等于现金余额；最终以购买页、平台结算为准。
管理员：返利检测 / 返利活动 关键词 / 返利测试 京东链接'''
PLATFORMS = {
    'jd': ('京东', ('jd.com', '3.cn', 'jingxi.com')),
    'taobao': ('淘宝/天猫', ('taobao.com', 'tmall.com', 'tb.cn', 'tb.com')),
    'pdd': ('拼多多', ('pinduoduo.com', 'yangkeduo.com', 'pdd.cn')),
    'vip': ('唯品会', ('vip.com',)),
    'kaola': ('考拉', ('kaola.com',)),
    'douyin': ('抖音', ('douyin.com', 'iesdouyin.com', 'jinritemai.com')),
    'kuaishou': ('快手', ('kuaishou.com', 'gifshow.com', 'kwaixiaodian.com')),
}


class PluginError(Exception):
    pass


def safe_text(value, limit=160):
    text = html.unescape(str(value or ''))
    text = re.sub(r'<[^>]*>', '', text)
    return text.replace('[CQ:', '［CQ:').replace('\x00', '').strip()[:limit]


def amount(value):
    try:
        number = Decimal(str(value))
        if number.is_finite() and number >= 0:
            return format(number.quantize(Decimal('0.01')), 'f').rstrip('0').rstrip('.') if number else '0'
    except (InvalidOperation, ValueError):
        pass
    return None


def valid_url(value):
    try:
        p = urllib.parse.urlsplit(str(value))
        return str(value) if p.scheme in ('http', 'https') and p.hostname and not p.username and not p.password and not p.port else ''
    except ValueError:
        return ''


def platform_of(value):
    if not valid_url(value):
        return ''
    host = urllib.parse.urlsplit(value).hostname.lower()
    for platform, (_, domains) in PLATFORMS.items():
        if any(host == d or host.endswith('.' + d) for d in domains):
            return platform
    return ''


def extract_link(text):
    # QQ may encode & as entities in the incoming text.
    links = re.findall(r'https?://[^\s<>"“”]+', html.unescape(text), re.I)
    if len(links) > 1:
        raise PluginError('每次请发一个商品链接。')
    if not links:
        raise PluginError('请发送包含 https:// 的购物分享链接；暂不支持仅口令。')
    link = links[0].rstrip('，。！？；、）】》,.!?;)]')
    if len(link) > 2000 or not platform_of(link):
        raise PluginError('未识别为支持的电商分享链接，发送“返利平台”查看说明。')
    return link


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, key, timeout=9, transport=None, pub_id=''):
        if not key:
            raise PluginError('尚未配置聚推客API Key，请管理员打开插件配置填写。')
        self.key, self.timeout, self.transport = key, timeout, transport
        self.pub_id = str(pub_id or '').strip()

    def request(self, path, fields=None, get=False):
        aggregate = path in ('/union/wn_convert', '/union/convert', '/union/goods_channel')
        if path not in ('/jd/get_goods_link', '/union/act_list', '/union/act', '/union/orders', '/union/wn_convert', '/union/convert', '/union/goods_channel'):
            raise PluginError('不支持的接口。')
        if aggregate and not self.pub_id:
            raise PluginError('请管理员在插件配置中填写聚推客pub_id，才能使用新版商品查券。')
        params = dict(fields or {}, **({'pub_id': self.pub_id} if aggregate else {'apikey': self.key}))
        if self.transport:
            result = self.transport(path, params, get)
        else:
            encoded = urllib.parse.urlencode(params).encode('utf-8')
            url = (AGGREGATE_API if aggregate else API) + path
            if get:
                url += '?' + encoded.decode('ascii')
            request = urllib.request.Request(url, data=None if get else encoded,
                headers={'User-Agent': 'Yuhua-Rebate/1.0', 'Content-Type': 'application/x-www-form-urlencoded'},
                method='GET' if get else 'POST')
            try:
                opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
                with opener.open(request, timeout=self.timeout) as response:
                    body = response.read(2 * 1024 * 1024 + 1)
                if len(body) > 2 * 1024 * 1024:
                    raise PluginError('平台返回内容过大，请稍后重试。')
                result = json.loads(body.decode('utf-8-sig'))
            except urllib.error.HTTPError as error:
                raise PluginError('聚推客接口HTTP %s；请检查接口权限或稍后重试。' % error.code) from None
            except (urllib.error.URLError, TimeoutError, OSError, ValueError):
                raise PluginError('无法连接聚推客HTTPS接口，请检查服务器网络和域名；不会降级明文传输。') from None
        if not isinstance(result, dict):
            raise PluginError('平台返回格式异常。')
        if str(result.get('code')) != '1':
            message = safe_text(result.get('msg') or result.get('message') or '未返回成功状态', 100)
            message = message.replace(self.key, '***')
            message = re.sub(r'https?://\S+', '[接口地址]', message)
            raise PluginError('聚推客：%s（请管理员确认密钥及业务权限）。' % message)
        return result.get('data')

    def goods(self, link, sid):
        if self.pub_id:
            parsed = self.request('/union/wn_convert', {'content': link})
            if not isinstance(parsed, dict) or not parsed.get('goodsId'):
                raise PluginError('未解析到可推广商品；商品可能未参与推广，请换一条链接。')
            source = parsed.get('source')
            if source not in PLATFORMS or source != platform_of(link):
                raise PluginError('商品平台解析不一致，已停止转链。')
            return self.convert_product(parsed, sid)
        if platform_of(link) != 'jd':
            raise PluginError('多平台商品查券需要管理员在插件配置填写聚推客pub_id。')
        data = self.request('/jd/get_goods_link', {'goods_link': link, 'sid': sid})
        if not isinstance(data, dict) or not valid_url(data.get('link')):
            raise PluginError('未返回可用推广链接，商品可能未参与推广或账号无此业务权限。')
        return data

    def convert_product(self, parsed, sid):
        source = parsed['source']
        converted = self.request('/union/convert', {'goodsId': str(parsed['goodsId']), 'sid': sid,
            'source': source, 'sub_share_rate': '1'})
        if not isinstance(converted, dict) or not valid_url(converted.get('url')):
            raise PluginError('未返回有效推广链接，请确认商品权限。')
        coupon_info = converted.get('couponInfo') or {}
        coupon_info = coupon_info if isinstance(coupon_info, dict) else {}
        # VIP's generic discount is a discount rate, never treat it as a cash coupon.
        raw_discount = coupon_info.get('fav') if source == 'vip' else coupon_info.get('fav', converted.get('discount', parsed.get('discount')))
        discount = amount(raw_discount)
        has_coupon = discount is not None and Decimal(discount) > 0
        images = converted.get('goodsCarouselPictures') or []
        image = images[0] if images else parsed.get('goodsThumbUrl')
        return {
            'skuName': converted.get('goodsName') or parsed.get('goodsName'),
            'link': converted['url'], '_source': source, 'is_coupon': 1 if has_coupon else 0,
            'couponInfo': [{'discount': discount}] if has_coupon else [],
            'priceInfo': {'lowestPrice': converted.get('price', parsed.get('price')),
                'lowestCouponPrice': converted.get('price', parsed.get('price'))},
            'shopInfo': {'shopName': converted.get('shopName') or parsed.get('shopName')},
            'imageInfo': {'imageList': [{'url': image}] if image else []}
        }

    def featured(self, sid):
        data = self.request('/union/goods_channel', {'eliteId': 1, 'page': 1, 'pageSize': 3})
        if not isinstance(data, dict) or not isinstance(data.get('list'), list):
            raise PluginError('精选商品接口返回格式异常。')
        result = []
        for item in data['list'][:3]:
            if item.get('goodsId'):
                result.append(self.convert_product(dict(item, source='jd'), sid))
        return result

    def activities(self):
        rows = []
        for page in range(1, 31):
            data = self.request('/union/act_list', {'page': page, 'pageSize': 100}, get=True)
            if not isinstance(data, dict) or not isinstance(data.get('data'), list):
                raise PluginError('活动列表格式异常。')
            rows.extend(data['data'])
            try:
                last = int(data['last_page'])
            except (KeyError, ValueError, TypeError):
                raise PluginError('活动列表缺少分页信息。') from None
            if page >= last:
                return rows
        raise PluginError('活动过多，请联系平台确认分页。')

    def activity(self, activity_id, sid):
        data = self.request('/union/act', {'act_id': activity_id, 'sid': sid})
        if not isinstance(data, dict):
            raise PluginError('活动返回格式异常。')
        url = valid_url(data.get('h5')) or valid_url(data.get('long_h5'))
        if not url:
            raise PluginError('此活动未返回网页链接，可能仅支持小程序或已下线。')
        return '%s\n%s\n请从此入口领券下单，优惠和计佣以活动规则为准。' % (safe_text(data.get('act_name') or '外卖活动'), url)

    def orders(self, sid):
        end = dt.datetime.now(CN).replace(microsecond=0)
        start = end - dt.timedelta(seconds=3599)
        data = self.request('/union/orders', {'sid': sid, 'query_type': 1,
            'start_time': start.strftime('%Y-%m-%d %H:%M:%S'), 'end_time': end.strftime('%Y-%m-%d %H:%M:%S'),
            'page': 1, 'pageSize': 10})
        if not isinstance(data, dict) or not isinstance(data.get('data'), list):
            raise PluginError('订单数据格式异常。')
        # Do not rely on upstream SID filtering to enforce privacy.
        return [x for x in data['data'] if str(x.get('sid', '')) == sid][:10]


def product_message(data):
    url = valid_url(data.get('link'))
    if not url:
        raise PluginError('商品没有有效的推广链接。')
    lines = ['🛍 ' + safe_text(data.get('skuName') or '商品 / 活动', 150)]
    source = PLATFORMS.get(data.get('_source'), ('', ()))[0]
    if source:
        lines.append('平台：' + source)
    shop = data.get('shopInfo') or {}
    if isinstance(shop, dict) and shop.get('shopName'):
        lines.append('店铺：' + safe_text(shop['shopName'], 50))
    price = data.get('priceInfo') or {}
    price = price if isinstance(price, dict) else {}
    current = amount(price.get('lowestPrice', price.get('price')))
    if current is not None:
        lines.append('参考售价：¥' + current)
    coupons = data.get('couponInfo') or []
    if isinstance(coupons, dict):
        coupons = [coupons]
    now_ms = time.time() * 1000
    usable = []
    for coupon in coupons if isinstance(coupons, list) else []:
        if not isinstance(coupon, dict) or str(coupon.get('yn', '1')) == '0':
            continue
        discount = amount(coupon.get('discount'))
        if discount is None or Decimal(discount) <= 0:
            continue
        begin, end = coupon.get('takeBeginTime'), coupon.get('takeEndTime')
        try:
            if begin is not None and float(begin) > now_ms:
                continue
            if end is not None and float(end) < now_ms:
                continue
        except (TypeError, ValueError):
            continue
        usable.append((coupon, discount))
    if str(data.get('is_coupon')) == '1' and usable:
        coupon, discount = usable[0]
        quota = amount(coupon.get('quota'))
        lines.append('🎫 优惠券：' + ('满%s减%s元' % (quota, discount) if quota and Decimal(quota) > 0 else discount + '元，门槛见领券页'))
        after = amount(price.get('lowestCouponPrice'))
        if after is not None:
            lines.append('券后参考价：¥' + after)
    elif str(data.get('is_coupon')) == '0':
        lines.append('🎫 当前未查到优惠券，可查看购买页的其他优惠。')
    else:
        lines.append('🎫 暂无完整的可领取券信息，以领券页为准。')
    lines.extend(['', '🔗 领券 / 购买链接：', url, '', '价格以结算页为准；渠道佣金待平台结算，不代表已到账或可提现余额。'])
    return '\n'.join(lines)


def product_image(data):
    images = (data.get('imageInfo') or {}).get('imageList') or []
    if images and isinstance(images[0], dict):
        value = valid_url(images[0].get('url'))
        if value:
            host = urllib.parse.urlsplit(value).hostname.lower()
            if any(host == d or host.endswith('.' + d) for d in ('360buyimg.com', 'pddpic.com', 'alicdn.com')):
                return value
    return ''


class State:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), timeout=3)
        self.db.execute('PRAGMA busy_timeout=3000')
        self.db.execute('CREATE TABLE IF NOT EXISTS rate (sid TEXT PRIMARY KEY, window INTEGER, count INTEGER)')
        self.db.execute('CREATE TABLE IF NOT EXISTS cache (cache_key TEXT PRIMARY KEY, expires REAL, payload TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, sid TEXT, stamp REAL, title TEXT, url TEXT)')
        self.db.commit()

    def allow(self, sid):
        window = int(time.time() // 60)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row = self.db.execute('SELECT window,count FROM rate WHERE sid=?', (sid,)).fetchone()
            count = row[1] + 1 if row and row[0] == window else 1
            self.db.execute('INSERT OR REPLACE INTO rate VALUES (?,?,?)', (sid, window, count))
            self.db.commit()
            return count <= 8
        except Exception:
            self.db.rollback()
            raise

    def cached(self, key):
        row = self.db.execute('SELECT expires,payload FROM cache WHERE cache_key=?', (key,)).fetchone()
        return json.loads(row[1]) if row and row[0] > time.time() else None

    def remember(self, key, sid, data):
        now = time.time()
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)', (key, now + 60, json.dumps(data, ensure_ascii=False)))
            self.db.execute('DELETE FROM cache WHERE expires < ?', (now,))
            self.db.execute('INSERT INTO history(sid,stamp,title,url) VALUES (?,?,?,?)',
                (sid, now, safe_text(data.get('skuName') or '京东商品'), valid_url(data.get('link'))))
            self.db.execute('DELETE FROM history WHERE sid=? AND id NOT IN (SELECT id FROM history WHERE sid=? ORDER BY id DESC LIMIT 20)', (sid, sid))
            self.db.execute('DELETE FROM history WHERE stamp < ?', (now - 30 * 86400,))

    def history(self, sid):
        return self.db.execute('SELECT title,url FROM history WHERE sid=? ORDER BY id DESC LIMIT 5', (sid,)).fetchall()

    def clear_history(self, sid):
        with self.db:
            self.db.execute('DELETE FROM history WHERE sid=?', (sid,))

    def close(self):
        self.db.close()


class Plugin:
    def __init__(self, sender, middleware, state, client=None):
        self.sender, self.mw, self.state = sender, middleware, state
        self.key = str(self.setting('api_key') or os.environ.get('JTK_API_KEY', '')).strip()
        self.client = client

    def setting(self, key):
        return self.mw.bucketGet(BUCKET, key)

    def api_client(self):
        return self.client or Client(self.key, pub_id=self.setting('pub_id'))

    def admin(self):
        try:
            return bool(self.sender.isAdmin())
        except Exception:
            return False

    def identity(self):
        platform = ''
        for method in ('getImtype', 'getImType', 'getPlatform'):
            try:
                value = getattr(self.sender, method)()
                if value:
                    platform = str(value)
                    break
            except (AttributeError, TypeError):
                pass
        uid = self.sender.getUserID()
        if not platform or uid is None or not str(uid):
            raise PluginError('中间件未返回有效的平台和用户身份，请管理员发送“返利检测”。')
        signing = self.setting('sid_secret')
        if not signing:
            if not self.admin():
                raise PluginError('首次使用请管理员发送“返利检测”初始化渠道标识。')
            signing = secrets.token_hex(32)
            self.mw.bucketSet(BUCKET, 'sid_secret', signing)
        return hmac.new(str(signing).encode(), (platform + ':' + str(uid)).encode(), hashlib.sha256).hexdigest()[:28]

    def private(self):
        for method in ('getChatID', 'getGroupCode', 'getGroupID'):
            try:
                value = getattr(self.sender, method)()
                return str(value or '') in ('', '0', 'None')
            except (AttributeError, TypeError):
                pass
        return False

    def handle(self, text):
        text = text.strip()
        if text in ('返利帮助', '返利菜单', '查券帮助'):
            return HELP, ''
        if text == '返利平台':
            return '购物链接识别：京东、淘宝/天猫、拼多多、唯品会、考拉、抖音、快手。\n聚推客公开聚合转链接口明确列出京东、淘宝、拼多多、唯品会；其他平台交由上游解析，未开放会返回失败，不能保证每条链接都有券或佣金。\n外卖使用已配置的活动入口，不把普通店铺链接伪装成返利链接。', ''
        if text == '返利检测':
            if not self.admin():
                return '此指令仅管理员可用。', ''
            methods = [m for m in ('getImtype', 'getImType', 'getUserID', 'getChatID', 'getGroupCode', 'getMessage') if hasattr(self.sender, m)]
            sid = self.identity()
            client = self.api_client()
            activities = client.activities()
            return '✅ 返利助手 %s\n密钥认证和HTTPS活动接口正常\n活动数量：%d\n渠道标识：%s\n中间件：%s\n京东接口需另发“返利测试 京东链接”验证。' % (VERSION, len(activities), sid, ', '.join(methods)), ''
        if text.startswith('返利活动'):
            if not self.admin():
                return '此指令仅管理员可用。', ''
            keyword = text[len('返利活动'):].strip()
            activities = self.api_client().activities()
            matches = [x for x in activities if not keyword or keyword in str(x.get('act_name', ''))]
            lines = ['当前活动（前20项）：'] + ['%s：%s' % (x.get('act_id'), safe_text(x.get('act_name'))) for x in matches[:20]]
            if not matches:
                lines.append('未找到匹配活动，试试“返利活动”查看全部。')
            lines.append('把需要的活动ID填入插件配置；仅查询不会自动替换现有活动。')
            return '\n'.join(lines), ''
        if text.startswith('返利测试 ') and not self.admin():
            return '此指令仅管理员可用。', ''
        sid = self.identity()
        if text == '返利渠道':
            if not self.private():
                return '渠道标识请私聊查询。', ''
            return '本人渠道标识：%s\n仅查询通过本助手入口产生并成功归因的订单。' % sid, ''
        if text in ('返利记录', '清空返利记录'):
            if not self.private():
                return '查券记录请私聊查询或清空。', ''
            if text.startswith('清空'):
                self.state.clear_history(sid)
                return '已清空本人的查券记录；不会删除平台订单。', ''
            rows = self.state.history(sid)
            return ('🕘 最近成功查券：\n\n' + '\n\n'.join('%s\n%s' % row for row in rows)) if rows else '暂无查券记录。', ''
        if not self.state.allow(sid):
            return '查询较频繁，请一分钟后再试（每分钟最多8次）。', ''
        client = self.api_client()
        if text == '返利精选':
            rows = client.featured(sid)
            return '\n\n'.join(product_message(item) for item in rows) if rows else '暂无可推广精选商品。', ''
        if text in ('返利订单', '我的返利订单'):
            if not self.private():
                return '订单包含个人消费信息，请私聊发送“返利订单”。', ''
            rows = client.orders(sid)
            if not rows:
                return '最近1小时暂无本人已归因订单。平台跟单可能延迟；更早记录请联系管理员在聚推客后台核对。', ''
            statuses = {0: '未付款', 1: '已付款', 2: '待结算', 3: '已结算', 4: '无效'}
            lines = ['🧾 最近1小时本人订单（最多10条）：']
            for row in rows:
                lines.append('%s\n尾号%s · %s\n渠道预估佣金 ¥%s' % (safe_text(row.get('order_title') or row.get('act_name'), 70),
                    str(row.get('order_sn', ''))[-6:], statuses.get(int(row.get('status', -1)), '未知'), amount(row.get('jtk_share_fee')) or '待确认'))
            lines.append('这是渠道佣金明细，不代表个人可提现余额。')
            return '\n\n'.join(lines), ''
        if text in ('美团外卖优惠', '淘宝闪购优惠'):
            setting = 'mt_act_id' if text == '美团外卖优惠' else 'ele_act_id'
            activity_id = str(self.setting(setting) or '').strip()
            if not activity_id:
                return '管理员尚未选择此活动，请先用“返利活动”查询并配置活动ID。', ''
            return client.activity(activity_id, sid), ''
        link = extract_link(text)
        cache_key = hashlib.sha256((sid + ':' + link).encode()).hexdigest()
        data = self.state.cached(cache_key)
        if data is None:
            data = client.goods(link, sid)
            self.state.remember(cache_key, sid, data)
        send_image = str(self.setting('send_image')).lower() in ('true', '1')
        return product_message(data), product_image(data) if send_image else ''


def main():
    import middleware
    sender = middleware.Sender(middleware.getSenderID())
    state = None
    try:
        state = State(Path(__file__).resolve().parent / '.jtk_coupon' / 'state.sqlite3')
        plugin = Plugin(sender, middleware, state)
        reply, image = plugin.handle(str(sender.getMessage() or ''))
        sender.reply(reply)
        if image:
            try:
                sender.replyImage(image)
            except Exception:
                pass  # Text reply already delivered; image failure must not duplicate the response.
    except PluginError as error:
        sender.reply('⚠️ ' + str(error))
    except Exception:
        sender.reply('⚠️ 返利助手处理失败，请管理员检查插件运行环境与数据目录权限。')
    finally:
        if state:
            state.close()


if __name__ == '__main__':
    main()
