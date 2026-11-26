# [title: 优惠券查询]
# [icon: https://cdn.jsdelivr.net/gh/muzixing666/plugin@main/icons/rebate.svg]
# [language: python]
# [author: Codex]
# [version: 2.1.7]
# [public: true]
# [open_source: true]
# [disable: false]
# [priority: 100]
# [rule: (?i)https?://[^\s]*(?:jd\.com|3\.cn|jingxi\.com|taobao\.com|tmall\.com|tb\.cn|tb\.com|pinduoduo\.com|yangkeduo\.com|pdd\.cn|vip\.com|kaola\.com|kuaishou\.com|gifshow\.com|kwaixiaodian\.com)[^\s]*|^(?:优惠券查询|优惠券帮助|优惠券菜单|优惠券精选|支持平台|查询记录|清空查询记录|优惠券检测|折淘客检测|优惠券配置|拼多多授权|订单查询|优惠券活动(?:\s+\S+)?|美团外卖优惠|淘宝闪购优惠)$|^查券\s+.+$|^优惠券测试\s+.+$|(?:[￥¥$₤₴€£][A-Za-z0-9]{5,40}[￥¥$₤₴€£])|^\s*(?:\([A-Za-z0-9]{5,40}\)|（[A-Za-z0-9]{5,40}）|【[A-Za-z0-9]{5,40}】)\s*$|^(?s:.*(?:淘宝|天猫|手淘|淘口令|复制|打开).*(?:\([A-Za-z0-9]{5,40}\)|（[A-Za-z0-9]{5,40}）|【[A-Za-z0-9]{5,40}】).*|.*(?:\([A-Za-z0-9]{5,40}\)|（[A-Za-z0-9]{5,40}）|【[A-Za-z0-9]{5,40}】).*(?:淘宝|天猫|手淘|淘口令|复制|打开).*)$|^(?:查券\s+)?淘口令[：:\s]+(?s:\S.*)$]
# [description: 发送购物链接，一键查询商品信息和优惠券，获取领券购买入口。支持识别淘宝／天猫、京东、拼多多、唯品会、快手、考拉海购链接，另有美团外卖和淘宝闪购优惠入口。]
# [param: {"required":false,"key":"jtk_coupon.api_key","bool":false,"name":"聚推客 API Key","desc":"接口密钥，仅保存在配置中；京东继续使用聚推客，不接折淘客。"}]
# [param: {"required":false,"key":"jtk_coupon.pub_id","bool":false,"name":"聚推客 pub_id","desc":"个人中心的推广者身份标识，用于新版商品解析和转链。"}]
# [param: {"required":false,"key":"jtk_coupon.ztk_key","bool":false,"name":"折淘客 AppKey","desc":"折淘客对接密钥；不写进源码。仅 Key 不足以完成转链，还需授权 SID、PID。"}]
# [param: {"required":false,"key":"jtk_coupon.ztk_sid","bool":false,"name":"折淘客授权 SID","desc":"授权管理中的淘客账号授权 ID，不是用户标识；淘宝、唯品会批量转链接口需要。"}]
# [param: {"required":false,"key":"jtk_coupon.ztk_pid","bool":false,"name":"折淘客 PID","desc":"与授权账户一致的 mm_数字_数字_数字；未配置时折淘客失败不会影响聚推客结果。"}]
# [param: {"required":false,"key":"jtk_coupon.pdd_client_id","bool":false,"name":"拼多多应用 Client ID","desc":"折淘客拼多多专用转链所用应用 ID，需在多多进宝关联应用。"}]
# [param: {"required":false,"key":"jtk_coupon.pdd_client_secret","bool":false,"name":"拼多多应用 Client Secret","desc":"折淘客拼多多专用转链所用密钥；只填面板配置，启用后经 HTTPS 发送至折淘客。"}]
# [param: {"required":false,"key":"jtk_coupon.pdd_pid","bool":false,"name":"拼多多推广位 PID","desc":"数字_数字格式，使用已完成授权备案的推广位；专用接口需同时配置折淘客 Key、应用 ID 和密钥。"}]
# [param: {"required":false,"key":"jtk_coupon.pdd_track_user","bool":false,"name":"拼多多按用户跟单","desc":"留空或 false 使用导购模式，只传 PID。填 true 为转链附加用户标识，每个用户需单独完成授权备案。"}]
# [param: {"required":false,"key":"jtk_coupon.ztk_kaola_sid","bool":false,"name":"折淘客考拉授权 SID","desc":"折淘客中已授权的考拉账号对应 SID，留空跳过考拉转链。"}]
# [param: {"required":false,"key":"jtk_coupon.ztk_relation_id","bool":false,"name":"折淘客淘宝渠道关系 ID","desc":"可选；授权类型要求渠道关系 ID 时填写已备案的 relation_id，不可随意编造。留空不传。"}]
# [param: {"required":false,"key":"jtk_coupon.jtk_enabled","bool":false,"name":"启用聚推客","desc":"留空默认开启；填 false 可关闭。提供京东与其他已开通平台查询。"}]
# [param: {"required":false,"key":"jtk_coupon.ztk_enabled","bool":false,"name":"启用折淘客","desc":"留空且已配置 Key 时默认开启；填 false 可关闭。京东始终不会发送至折淘客。"}]
# [param: {"required":false,"key":"jtk_coupon.preferred_provider","bool":false,"name":"信息不足时优先接口","desc":"jtk（默认）或 ztk；只有同商品且两家金额均已知时，才按最高金额选择。"}]
# [param: {"required":false,"key":"jtk_coupon.jtk_factor","bool":false,"name":"聚推客金额系数","desc":"0～1，默认 1；比较金额乘此系数，可按服务费调整；未设置表示比较平台原始预估。"}]
# [param: {"required":false,"key":"jtk_coupon.ztk_factor","bool":false,"name":"折淘客金额系数","desc":"0～1，默认 1；与聚推客系数口径一致才有比较意义。普通用户不展示金额。"}]
# [param: {"required":false,"key":"jtk_coupon.admin_amount","bool":false,"name":"管理员显示金额","desc":"留空默认开启；false 关闭；只在管理员私聊显示返利金额、接口比较与失败原因。"}]
# [param: {"required":false,"key":"jtk_coupon.request_timeout","bool":false,"name":"单次接口超时（秒）","desc":"3～15，默认 8；两家并行查询，聚推客解析加转链最多两次请求。"}]
# [param: {"required":false,"key":"jtk_coupon.cache_seconds","bool":false,"name":"查询缓存（秒）","desc":"0～600，默认 60；0 禁用。按用户和配置隔离；更换密钥、授权或系数后自动失效。"}]
# [param: {"required":false,"key":"jtk_coupon.rate_limit","bool":false,"name":"每用户每分钟次数","desc":"1～30，默认 8；限制商品、精选和外卖查询频率。帮助、记录不计入。"}]
# [param: {"required":false,"key":"jtk_coupon.group_query","bool":false,"name":"群聊自动查询","desc":"留空默认开启；false 时群内发送链接不查询，需私聊；群聊永不展示管理员金额。"}]
# [param: {"required":false,"key":"jtk_coupon.allowed_platforms","bool":false,"name":"开放的平台","desc":"留空全部；用英文逗号填写 jd,taobao,pdd,vip,kaola,kuaishou。实际成功依赖接口权限。"}]
# [param: {"required":false,"key":"jtk_coupon.send_image","bool":true,"name":"发送商品图","desc":"查券后附一张可信商品图；关闭只发文本。"}]
# [param: {"required":false,"key":"jtk_coupon.history_enabled","bool":false,"name":"保存查询记录","desc":"留空默认开启；false 不再保存新记录，缓存仍可使用。只保存商品标题与链接；私聊可清空。"}]
# [param: {"required":false,"key":"jtk_coupon.mt_act_id","bool":false,"name":"美团活动 ID","desc":"管理员私聊发送 优惠券活动 美团 查看当前 ID；外卖活动使用聚推客。"}]
# [param: {"required":false,"key":"jtk_coupon.ele_act_id","bool":false,"name":"淘宝闪购活动 ID","desc":"管理员私聊发送 优惠券活动 外卖 查看当前 ID；外卖活动使用聚推客。"}]
# [param: {"required":false,"key":"jtk_coupon.sid_secret","bool":false,"name":"用户标识签名密钥","desc":"首次由管理员初始化后长期保留；更换会影响既有用户和订单归属，不要随意修改。"}]

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
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, InvalidOperation
from pathlib import Path

BUCKET = 'jtk_coupon'
VERSION = '2.1.7'
API = 'https://api.jutuike.com'
AGGREGATE_API = 'https://api.act.jutuike.com'
CN = dt.timezone(dt.timedelta(hours=8))
HELP = """🛍 优惠券查询
直接发送购物链接或淘口令。未自动识别时，可发送「淘口令：完整分享文案」。
返回商品、价格、优惠券和购买链接。平台提供口令时会一并返回。

🛒 优惠券精选：查看当前精选商品
🍱 美团外卖优惠 / 淘宝闪购优惠
🕘 查询记录：私聊查看最近 5 次成功查询
🧹 清空查询记录：清除本人的查询记录
📋 支持平台：查看平台说明

价格、优惠券有效期和使用条件以购买页面为准。"""
PLATFORMS = {
    'jd': ('京东', ('jd.com', '3.cn', 'jingxi.com')),
    'taobao': ('淘宝/天猫', ('taobao.com', 'tmall.com', 'tb.cn', 'tb.com')),
    'pdd': ('拼多多', ('pinduoduo.com', 'yangkeduo.com', 'pdd.cn')),
    'vip': ('唯品会', ('vip.com',)),
    'kaola': ('考拉', ('kaola.com',)),
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


TAOBAO_PASSWORD = re.compile(r'(?:[￥¥$₤₴€£][A-Za-z0-9]{5,40}[￥¥$₤₴€£])')
TAOBAO_BRACKET_PASSWORD = re.compile(r'(?:\([A-Za-z0-9]{5,40}\)|（[A-Za-z0-9]{5,40}）|【[A-Za-z0-9]{5,40}】)')
TAOBAO_SHARE_CONTEXT = re.compile(r'(?:淘宝|天猫|手淘|淘口令|复制|打开)')
TAOBAO_PREFIX = '淘口令：'


def query_platform(value):
    if (value.startswith(TAOBAO_PREFIX) or TAOBAO_PASSWORD.fullmatch(value)
            or TAOBAO_BRACKET_PASSWORD.fullmatch(value)):
        return 'taobao'
    return platform_of(value)


def extract_query(text):
    value = html.unescape(re.sub(r'^查券\s+', '', text).strip())
    explicit = re.fullmatch(r'淘口令[：:\s]+(.+)', value, re.S)
    if explicit:
        value = explicit.group(1).strip()
    passwords = TAOBAO_PASSWORD.findall(value)
    if not passwords and (explicit or TAOBAO_SHARE_CONTEXT.search(value)):
        passwords = TAOBAO_BRACKET_PASSWORD.findall(value)
    if len(passwords) > 1:
        raise PluginError('每次请发送一个商品口令。')
    if passwords:
        urls = re.findall(r'https?://[^\s<>"“”]+', value, re.I)
        if any(platform_of(url) not in ('', 'taobao') for url in urls):
            raise PluginError('请把淘口令和其他平台商品链接分开发送。')
        return passwords[0]
    if TAOBAO_BRACKET_PASSWORD.fullmatch(value):
        return value
    if explicit and len(value) <= 600 and not re.search(r'https?://', value, re.I):
        return TAOBAO_PREFIX + value
    return extract_link(value)


def extract_link(text):
    # QQ may encode & as entities in the incoming text.
    links = re.findall(r'https?://[^\s<>"“”]+', html.unescape(text), re.I)
    if len(links) > 1:
        raise PluginError('每次请发一个商品链接。')
    if not links:
        raise PluginError('请发送商品链接或淘口令。')
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
            if path == '/union/orders' and any(term in message for term in ('对应条件内无数据', '暂无订单', '无订单数据')):
                return {'data': [], 'last_page': 0}
            if path == '/union/wn_convert' and '没有匹配到合适的商品' in message:
                raise PluginError('此链接暂未匹配到可推广商品。请换一条有效商品分享链接；不是每件商品都有券或返利。')
            raise PluginError('聚推客：%s（请管理员确认密钥及业务权限）。' % message)
        return result.get('data')

    def goods(self, link, sid):
        source = platform_of(link)
        if self.pub_id:
            try:
                parsed = self.request('/union/wn_convert', {'content': link})
                if not isinstance(parsed, dict) or not parsed.get('goodsId'):
                    raise PluginError('未解析到可推广商品；商品可能未参与推广，请换一条链接。')
                if parsed.get('source') != source or source not in PLATFORMS:
                    raise PluginError('商品平台解析不一致，已停止转链。')
                return self.convert_product(parsed, sid)
            except PluginError as aggregate_error:
                if source != 'jd':
                    raise
                try:
                    return self.jd_goods(link, sid)
                except PluginError as direct_error:
                    raise PluginError('京东聚合：%s；京东专用：%s' % (aggregate_error, direct_error)) from None
        if source != 'jd':
            raise PluginError('多平台商品查券需要管理员在插件配置填写聚推客pub_id。')
        return self.jd_goods(link, sid)

    def jd_goods(self, link, sid):
        data = self.request('/jd/get_goods_link', {'goods_link': link, 'sid': sid})
        if not isinstance(data, dict) or not valid_url(data.get('link')):
            raise PluginError('未返回可用推广链接，商品可能未参与推广或账号无此业务权限。')
        data['_provider'], data['_source'] = 'jtk', 'jd'
        info = data.get('commissionInfo') or {}
        data['_commission'] = amount(info.get('commission')) if isinstance(info, dict) else None
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
        coupon = {'discount': discount}
        for source_key, target_key in (('useBeginTime', 'takeBeginTime'), ('useEndTime', 'takeEndTime')):
            value = coupon_info.get(source_key)
            if value:
                try:
                    coupon[target_key] = dt.datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S').replace(tzinfo=CN).timestamp() * 1000
                except (ValueError, TypeError, OverflowError):
                    coupon['yn'] = '0'
        images = converted.get('goodsCarouselPictures') or []
        image = images[0] if images else parsed.get('goodsThumbUrl')
        return {
            '_provider': 'jtk', '_product_id': str(parsed.get('skuId') or parsed.get('goodsId') or ''),
            '_commission': amount(converted.get('commission', parsed.get('commission'))),
            'skuName': converted.get('goodsName') or parsed.get('goodsName'),
            'link': converted['url'], '_source': source, 'is_coupon': 1 if has_coupon else 0,
            'couponInfo': [coupon] if has_coupon else [],
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
        return '%s\n%s\n请从此入口领券下单，优惠和使用条件以活动页面为准。' % (public_text(data.get('act_name') or '外卖活动'), url)

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


def usable_coupon(data):
    if str(data.get('is_coupon')) != '1':
        return None
    coupons = data.get('couponInfo') or []
    if isinstance(coupons, dict):
        coupons = [coupons]
    now_ms = time.time() * 1000
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
        return coupon, discount


def append_password(lines, data):
    password = data.get('_password')
    if not isinstance(password, str):
        return
    if TAOBAO_PASSWORD.fullmatch(password) or TAOBAO_BRACKET_PASSWORD.fullmatch(password):
        lines.extend(['📋 复制口令到购物 App', password])


def product_message(data):
    url = valid_url(data.get('link'))
    if not url:
        raise PluginError('商品没有有效的购买链接。')
    lines = ['🛍 ' + public_text(data.get('skuName') or '商品 / 活动', 150)]
    source = PLATFORMS.get(data.get('_source'), ('', ()))[0]
    if source:
        lines.append('平台：' + source)
    shop = data.get('shopInfo') or {}
    if isinstance(shop, dict) and shop.get('shopName'):
        lines.append('店铺：' + public_text(shop['shopName'], 50))
    price = data.get('priceInfo') or {}
    price = price if isinstance(price, dict) else {}
    current = amount(price.get('lowestPrice', price.get('price')))
    if current is not None:
        lines.append('参考售价：¥' + current)
    usable = usable_coupon(data)
    if usable:
        coupon, discount = usable
        quota = amount(coupon.get('quota'))
        lines.append('🎫 优惠券：' + ('满%s减%s元' % (quota, discount) if quota and Decimal(quota) > 0 else discount + '元，门槛见领券页'))
        after = amount(price.get('lowestCouponPrice'))
        if after is not None:
            lines.append('券后参考价：¥' + after)
    elif str(data.get('is_coupon')) == '0':
        lines.append('🎫 当前未查到优惠券，可查看购买页的其他优惠。')
    else:
        lines.append('🎫 暂无完整的可领取券信息，以领券页为准。')
    lines.extend(['', '🔗 ' + ('领券购买' if usable else '购买链接'), url])
    append_password(lines, data)
    alternative = data.get('_alternative') or {}
    alternative_url = valid_url(alternative.get('link'))
    alternative_coupon = usable_coupon(alternative)
    if not usable and alternative_url and alternative_coupon:
        _, discount = alternative_coupon
        lines.extend(['', '🎟 同款有券', '优惠券：¥' + discount])
        alt_shop = safe_text((alternative.get('shopInfo') or {}).get('shopName'), 50)
        if alt_shop:
            lines.append('店铺：' + public_text(alt_shop, 50))
        after = amount((alternative.get('priceInfo') or {}).get('lowestCouponPrice'))
        if after is not None:
            lines.append('券后参考价：¥' + after)
        lines.extend(['领券链接', alternative_url])
        append_password(lines, alternative)
    lines.extend(['', '价格、优惠券有效期和使用条件以购买页面为准。'])
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

    def allow(self, sid, limit=8):
        window = int(time.time() // 60)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row = self.db.execute('SELECT window,count FROM rate WHERE sid=?', (sid,)).fetchone()
            count = row[1] + 1 if row and row[0] == window else 1
            self.db.execute('INSERT OR REPLACE INTO rate VALUES (?,?,?)', (sid, window, count))
            self.db.commit()
            return count <= limit
        except Exception:
            self.db.rollback()
            raise

    def cached(self, key):
        row = self.db.execute('SELECT expires,payload FROM cache WHERE cache_key=?', (key,)).fetchone()
        return json.loads(row[1]) if row and row[0] > time.time() else None

    def remember(self, key, sid, data, ttl=60, save_history=True):
        now = time.time()
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)', (key, now + ttl, json.dumps(data, ensure_ascii=False)))
            self.db.execute('DELETE FROM cache WHERE expires < ?', (now,))
            if save_history:
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
        return self.client or Client(self.key, timeout=self.number('request_timeout', 8, 3, 15), pub_id=self.setting('pub_id'))

    def admin(self):
        try:
            value = self.sender.isAdmin()
            return value is True or str(value).lower() in ('true', '1')
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

    def enabled(self, key, default=True):
        value = self.setting(key)
        return default if value is None or str(value).strip() == '' else str(value).lower() in ('true', '1', 'yes', 'on')

    def number(self, key, default, low, high):
        try:
            value = float(self.setting(key))
            return max(low, min(high, value)) if math.isfinite(value) else default
        except (TypeError, ValueError):
            return default

    def details_allowed(self):
        return self.admin() and self.private() and self.enabled('admin_amount')

    def comparison_client(self):
        if self.client:
            return self.client
        clients = {}
        timeout = self.number('request_timeout', 8, 3, 15)
        if self.enabled('jtk_enabled'):
            try:
                clients['jtk'] = self.api_client()
            except PluginError:
                pass
        if self.enabled('ztk_enabled') and self.setting('ztk_key'):
            clients['ztk'] = ZhetaokeClient(self.setting('ztk_key'), self.setting('ztk_sid'), self.setting('ztk_pid'), timeout,
                relation_id=self.setting('ztk_relation_id'), pdd_client_id=self.setting('pdd_client_id'),
                pdd_client_secret=self.setting('pdd_client_secret'), pdd_pid=self.setting('pdd_pid'),
                kaola_sid=self.setting('ztk_kaola_sid'),
                pdd_track_user=self.enabled('pdd_track_user', False))
        return ComparisonClient(clients, {key: self.number(key + '_factor', 1, 0, 1) for key in ('jtk', 'ztk')},
            self.setting('preferred_provider') or 'jtk')

    def render(self, data):
        return product_message(data) + (admin_details(data) if self.details_allowed() else '')

    def cache_key(self, sid, link):
        keys = ('pub_id','ztk_key','ztk_sid','ztk_pid','ztk_relation_id','pdd_client_id','pdd_client_secret','pdd_pid','pdd_track_user','ztk_kaola_sid','jtk_enabled','ztk_enabled','preferred_provider','jtk_factor','ztk_factor')
        config = json.dumps([self.key] + [self.setting(k) for k in keys], ensure_ascii=False)
        return hashlib.sha256((VERSION + sid + link + config).encode()).hexdigest()

    def diagnostics(self, accounts=False):
        self.identity()
        lines = ['优惠券查询 v' + VERSION, '京东：仅聚推客；折淘客不接京东。',
            '聚推客：' + ('已配置 Key' if self.key else '未配置 Key'),
            '聚推客 pub_id：' + ('已配置' if self.setting('pub_id') else '未配置'),
            '折淘客 Key：' + ('已配置' if self.setting('ztk_key') else '未配置'),
            '折淘客授权 SID：' + ('已配置' if self.setting('ztk_sid') else '缺少'),
            '折淘客 PID：' + ('格式有效' if re.fullmatch(r'mm_\d+_\d+_\d+', str(self.setting('ztk_pid') or '')) else '缺少或格式无效'),
            '折淘客考拉 SID：' + ('已配置' if self.setting('ztk_kaola_sid') else '缺少'),
            '美团活动 ID：' + ('已配置' if self.setting('mt_act_id') else '缺少'),
            '淘宝闪购活动 ID：' + ('已配置' if self.setting('ele_act_id') else '缺少'),
            '折淘客拼多多：' + ('已配置' if self.setting('pdd_client_id') and self.setting('pdd_client_secret')
                and re.fullmatch(r'\d+_\d+', str(self.setting('pdd_pid') or '')) else '缺少应用凭证或有效 PID'),
            '金额：仅管理员私聊可见，普通用户和群聊不展示。']
        if accounts and self.setting('ztk_key'):
            try:
                rows = ZhetaokeClient(self.setting('ztk_key'), timeout=self.number('request_timeout',8,3,15)).accounts()
                lines.append('折淘客授权列表：请求成功，本页 %d 个账户。' % len(rows))
                # Do not print account tokens or auto-select somebody else's PID.
                lines.append('请在折淘客授权管理确认有效 SID 与同账户 PID 后填入插件配置。')
            except PluginError as error:
                lines.append(str(error))
        lines.append('商品验证：优惠券测试 商品链接；活动：优惠券活动 关键词')
        return '\n'.join(lines)

    def handle(self, text):
        text = text.strip()
        aliases = {'返利帮助':'优惠券帮助','返利菜单':'优惠券菜单','查券帮助':'优惠券帮助',
            '返利平台':'支持平台','返利精选':'优惠券精选','返利记录':'查询记录','清空返利记录':'清空查询记录',
            '返利检测':'优惠券检测','订单查询':'返利订单'}
        text = aliases.get(text,text)
        if text in ('优惠券查询','优惠券帮助','优惠券菜单'):
            return HELP, ''
        if text == '支持平台':
            return '识别京东、淘宝/天猫、拼多多、唯品会、考拉、快手。\n实际可查询范围取决于已开通的接口；部分商品可能没有优惠券。\n外卖请发送“美团外卖优惠”或“淘宝闪购优惠”。', ''
        admin_command = (text in ('优惠券检测','折淘客检测','优惠券配置','拼多多授权','返利渠道','返利订单','我的返利订单')
            or text.startswith(('返利活动','优惠券活动','返利测试','优惠券测试')))
        if admin_command and (not self.admin() or not self.private()):
            return '此指令仅管理员私聊可用。', ''
        if text in ('优惠券检测','折淘客检测','优惠券配置'):
            return self.diagnostics(text == '折淘客检测'), ''
        if text == '拼多多授权':
            client = self.comparison_client()
            ztk = client.clients.get('ztk') if isinstance(client, ComparisonClient) else None
            if not ztk:
                raise PluginError('请先启用并配置折淘客。')
            return ztk.pdd_authorization(self.identity()), ''
        if text.startswith(('返利活动','优惠券活动')):
            keyword = re.sub(r'^(?:返利活动|优惠券活动)', '', text).strip()
            rows = self.api_client().activities()
            matches = [x for x in rows if not keyword or keyword in str(x.get('act_name',''))]
            return '\n'.join(['当前活动（前20项）：'] + ['%s：%s' % (x.get('act_id'),safe_text(x.get('act_name'))) for x in matches[:20]]), ''
        sid = self.identity()
        if text == '返利渠道':
            return '本人渠道标识：' + sid, ''
        if text in ('查询记录','清空查询记录'):
            if not self.private():
                return '查询记录请私聊查看或清空。', ''
            if text == '清空查询记录':
                self.state.clear_history(sid)
                return '已清空本人的查询记录。', ''
            rows = self.state.history(sid)
            return ('最近成功查询：\n\n' + '\n\n'.join('%s\n%s' % (public_text(title),url) for title,url in rows)) if rows else '暂无查询记录。', ''
        if text in ('返利订单','我的返利订单'):
            rows = self.api_client().orders(sid)
            if not rows:
                return '最近1小时暂无本人订单。此处仅查询聚推客订单；折淘客订单请在其后台查看。', ''
            return '\n\n'.join('订单尾号 %s\n%s\n预估返利金额：¥%s' % (str(x.get('order_sn',''))[-6:],
                safe_text(x.get('order_title') or x.get('act_name')),amount(x.get('jtk_share_fee')) or '未知') for x in rows), ''
        if not self.private() and not self.enabled('group_query'):
            return '请私聊发送商品链接或口令查询优惠券。', ''
        limit = int(self.number('rate_limit',8,1,30))
        if not self.state.allow(sid, limit):
            return '查询较频繁，请一分钟后再试。', ''
        if text == '优惠券精选':
            rows = self.api_client().featured(sid)
            # Convert each curated item's link through the same comparison path.
            results = []
            for item in rows:
                try:
                    results.append(self.comparison_client().goods(item['link'],sid))
                except PluginError:
                    results.append(item)
            return '\n\n'.join(self.render(item) for item in results) if results else '暂无精选商品。', ''
        if text in ('美团外卖优惠','淘宝闪购优惠'):
            activity_id = str(self.setting('mt_act_id' if text == '美团外卖优惠' else 'ele_act_id') or '').strip()
            if not activity_id:
                return '此优惠入口暂未配置，请联系管理员。', ''
            return self.api_client().activity(activity_id,sid), ''
        link = extract_query(text)
        allowed = str(self.setting('allowed_platforms') or '').strip()
        if allowed and query_platform(link) not in {x.strip() for x in allowed.split(',')}:
            return '该平台暂未开放查询。', ''
        cache_key = self.cache_key(sid, link)
        ttl = self.number('cache_seconds',60,0,600)
        data = self.state.cached(cache_key) if ttl else None
        if data is None:
            data = self.comparison_client().goods(link,sid)
            self.state.remember(cache_key,sid,data,ttl,self.enabled('history_enabled'))
        image = product_image(data) if self.enabled('send_image',False) else ''
        return self.render(data), image



ZTK_API = 'https://api.zhetaoke.com:10001/api/'
PROVIDERS = {'jtk': '聚推客', 'ztk': '折淘客'}


def public_text(value, limit=160):
    text = safe_text(value, limit)
    return re.sub(r'返利|返佣|佣金|计佣|推广|渠道|聚推客|折淘客', '优惠', text)


def pdd_error(result):
    details = result if isinstance(result, dict) else {}
    response = details.get('error_response')
    if isinstance(response, dict):
        details = response
    code = str(details.get('error_code') or details.get('sub_code') or details.get('status') or '')
    code = code if re.fullmatch(r'[0-9]{1,10}', code) else ''
    message = ' '.join(str(details.get(key) or '') for key in ('error_msg', 'sub_msg', 'msg', 'message', 'content'))
    # Use fixed hints only. The upstream response may contain configuration values.
    hints = (
        (('关联应用', '关联对应'), '请检查多多进宝的应用关联。'),
        (('未备案', '授权备案', '未授权'), '请检查应用与推广位的授权备案。'),
        (('appkey', 'appsecret', '密钥'), '请检查折淘客 Key 和拼多多应用凭证。'),
        (('推广位', 'pid'), '请检查拼多多推广位与应用的配置。'),
        (('商品', '链接'), '请检查商品状态和推广权限。'),
    )
    hint = next((text for words, text in hints if any(word in message.lower() for word in words)), '')
    return '折淘客拼多多拒绝转链' + ('（错误码 ' + code + '）' if code else '') + '。' + hint


class ZhetaokeClient:
    """Official HTTPS batch converter; JD deliberately excluded."""
    def __init__(self, key, sid='', pid='', timeout=8, transport=None, relation_id='',
                 pdd_client_id='', pdd_client_secret='', pdd_pid='', kaola_sid='', pdd_track_user=False):
        self.key, self.sid, self.pid = key, sid, pid
        self.timeout, self.transport = timeout, transport
        self.relation_id = str(relation_id or '').strip()
        self.pdd_client_id = str(pdd_client_id or '').strip()
        self.pdd_client_secret = str(pdd_client_secret or '').strip()
        self.pdd_pid = str(pdd_pid or '').strip()
        self.pdd_track_user = pdd_track_user
        self.kaola_sid = str(kaola_sid or '').strip()

    def request(self, endpoint, fields):
        if endpoint not in ('open_gaoyongzhuanlian_tkl_piliang.ashx', 'open_taokeshouquaninfo.ashx', 'api_quanwang.ashx',
                'open_pdd_zhuanlian_new.ashx', 'open_pdd_shouquan_query_new.ashx', 'open_pdd_shouquan_new.ashx',
                'open_kaola_zhuanke_api_zhuanlian.ashx'):
            raise PluginError('折淘客接口不在允许列表。')
        if not self.key:
            raise PluginError('折淘客未配置 Key。')
        params = dict(fields, appkey=self.key)
        if self.transport:
            result = self.transport(endpoint, params)
        else:
            search = endpoint == 'api_quanwang.ashx'
            get = search or endpoint.startswith('open_pdd_')
            encoded = urllib.parse.urlencode(params)
            url = ('https://api.zhetaoke.com:10003/api/' if search else ZTK_API) + endpoint
            if get:
                url += '?' + encoded
            req = urllib.request.Request(url,
                data=None if get else encoded.encode(),
                headers={'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'CouponQuery/2.0'})
            try:
                opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
                with opener.open(req, timeout=self.timeout) as response:
                    body = response.read(2 * 1024 * 1024 + 1)
                if len(body) > 2 * 1024 * 1024:
                    raise PluginError('折淘客响应超过大小限制。')
                result = json.loads(body.decode('utf-8-sig'))
            except urllib.error.HTTPError as error:
                raise PluginError('折淘客 HTTP %s。' % error.code) from None
            except (TimeoutError, urllib.error.URLError, OSError) as error:
                reason = getattr(error, 'reason', error)
                if isinstance(reason, TimeoutError):
                    raise PluginError('折淘客 HTTPS 请求超时。') from None
                if isinstance(reason, ssl.SSLCertVerificationError):
                    raise PluginError('折淘客 HTTPS 证书验证失败。') from None
                raise PluginError('折淘客 HTTPS 连接失败。') from None
            except ValueError:
                raise PluginError('折淘客返回的数据无法解析为 JSON。') from None
        if endpoint == 'open_pdd_zhuanlian_new.ashx':
            if isinstance(result, dict) and isinstance(result.get('goods_zs_unit_generate_response'), dict):
                return result
            raise PluginError(pdd_error(result))
        if endpoint == 'open_pdd_shouquan_new.ashx':
            if isinstance(result, dict) and isinstance(result.get('rp_promotion_url_generate_response'), dict):
                return result
            raise PluginError(pdd_error(result))
        if endpoint == 'open_pdd_shouquan_query_new.ashx':
            if isinstance(result, dict) and isinstance(result.get('authority_query_response'), dict):
                return result
            raise PluginError(pdd_error(result))
        if (endpoint == 'open_kaola_zhuanke_api_zhuanlian.ashx'
                and isinstance(result, dict) and str(result.get('code')) == '200'):
            return result
        if not isinstance(result, dict) or str(result.get('status')) != '200':
            # Keep upstream messages out of replies because they can contain request credentials.
            if endpoint == 'open_gaoyongzhuanlian_tkl_piliang.ashx' and isinstance(result, dict):
                status = str(result.get('status') or '')
                suffix = '（状态码 ' + status + '）' if re.fullmatch(r'[0-9]{1,6}', status) else ''
                message = str(result.get('message') or result.get('msg') or result.get('content') or '').lower()
                if any(word in message for word in ('rid', 'relation_id', '代理类型', '渠道pid')):
                    hint = '请核对淘宝代理授权 SID、渠道 PID 和关系 ID。'
                elif any(word in message for word in ('sid', '授权', 'token')):
                    hint = '请核对平台授权 SID 和有效期。'
                elif any(word in message for word in ('口令', '商品', '链接')):
                    hint = '请核对分享口令或商品是否仍可以推广。'
                else:
                    hint = '请检查 Key、授权、PID 或商品权限。'
                raise PluginError('折淘客未返回成功状态' + suffix + '。' + hint)
            raise PluginError('折淘客未返回成功状态，请检查 Key、授权、PID 或商品权限。')
        return result

    def accounts(self):
        rows = self.request('open_taokeshouquaninfo.ashx', {'page': '1'}).get('data')
        return rows if isinstance(rows, list) else []

    def goods(self, link, user_sid):
        source = query_platform(link)
        if source == 'pdd':
            return self.pdd_goods(link, user_sid)
        if source == 'kaola':
            return self.kaola_goods(link, user_sid)
        if source not in ('taobao', 'vip'):
            raise PluginError('折淘客当前支持淘宝/天猫、拼多多、唯品会和考拉。')
        if not self.sid or not re.fullmatch(r'mm_\d+_\d+_\d+', str(self.pid)):
            raise PluginError('折淘客缺少授权 SID 或有效 PID（mm_三段格式）。')
        content = link[len(TAOBAO_PREFIX):] if link.startswith(TAOBAO_PREFIX) else link
        fields = {'sid': self.sid, 'pid': self.pid, 'tkl': content}
        if source == 'taobao' and self.relation_id:
            fields['relation_id'] = self.relation_id
        result = self.request('open_gaoyongzhuanlian_tkl_piliang.ashx', fields)
        mapped = {'1': 'taobao', '3': 'pdd', '5': 'vip'}.get(str(result.get('plat')))
        url = valid_url(result.get('result_url'))
        if mapped != source or not url:
            raise PluginError('折淘客未返回匹配平台的有效商品链接。')
        title = safe_text(result.get('tao_title') or result.get('title'))
        if not title or title == '0':
            raise PluginError('折淘客未返回有效商品详情，无法确认此商品的优惠和金额，请更换在售商品链接。')
        coupon = amount(result.get('coupon_info_money'))
        has_coupon = str(result.get('is_youquan')) == '1' and coupon is not None and Decimal(coupon) > 0
        return {'skuName': result.get('tao_title') or result.get('title'), 'link': url,
            '_source': source, '_provider': 'ztk', '_product_id': str(result.get('tao_id') or ''),
            '_commission': amount(result.get('tkfee3')), 'is_coupon': int(has_coupon),
            '_password': safe_text(result.get('result_tkl'), 80),
            'couponInfo': [{'discount': coupon}] if has_coupon else [],
            'priceInfo': {'lowestPrice': result.get('size'), 'lowestCouponPrice': result.get('quanhou_jiage')},
            'shopInfo': {'shopName': result.get('nick')},
            'imageInfo': {'imageList': [{'url': result.get('pic')}]}}


    def pdd_fields(self, user_sid):
        if not (self.pdd_client_id and self.pdd_client_secret and re.fullmatch(r'\d+_\d+', self.pdd_pid)):
            raise PluginError('请配置拼多多应用 ID、密钥及已备案的拼多多 PID。')
        fields = {'pdd_app_key': self.pdd_client_id, 'pdd_app_secret': self.pdd_client_secret,
            'pid': self.pdd_pid}
        if self.pdd_track_user:
            custom = json.dumps({'uid': user_sid, 'sid': ''}, separators=(',', ':'))
            if len(custom.encode()) > 64:
                raise PluginError('拼多多用户标识超过长度限制。')
            fields['custom_parameters'] = custom
        return fields

    def pdd_authorization(self, user_sid):
        fields = self.pdd_fields(user_sid)
        binding = self.request('open_pdd_shouquan_query_new.ashx', fields)['authority_query_response']
        if str(binding.get('bind')) == '1':
            return '当前会话的拼多多用户标识已绑定。' if self.pdd_track_user else '拼多多导购 PID 已绑定。'
        response = self.request('open_pdd_shouquan_new.ashx', fields)['rp_promotion_url_generate_response']
        rows = response.get('url_list')
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict):
                continue
            for key in ('mobile_url', 'url'):
                url = valid_url(row.get(key))
                if url and url.startswith('https://') and platform_of(url) == 'pdd':
                    return '请用手机打开授权链接并在拼多多确认授权，然后在同一会话重新查券。\n' + url
        raise PluginError('拼多多未返回可用授权链接。')

    def pdd_goods(self, link, user_sid):
        fields = self.pdd_fields(user_sid)
        parts = urllib.parse.urlsplit(link)
        goods_ids = urllib.parse.parse_qs(parts.query, keep_blank_values=True).get('goods_id', [])
        fields['content'] = goods_ids[0] if len(goods_ids) == 1 and re.fullmatch(r'[0-9]{6,20}', goods_ids[0]) else link
        try:
            result = self.request('open_pdd_zhuanlian_new.ashx', fields)
        except PluginError as error:
            if '错误码 50001）' not in str(error):
                raise
            raise PluginError(str(error) + self.pdd_binding_status(fields)) from None
        links = result.get('goods_zs_unit_generate_response') or {}
        for key in ('mobile_short_url', 'short_url', 'mobile_url', 'url'):
            url = valid_url(links.get(key))
            if url and platform_of(url) == 'pdd':
                return {'skuName': '拼多多商品', 'link': url, '_source': 'pdd',
                    '_provider': 'ztk', '_link_only': True}
        raise PluginError('拼多多专用转链未返回可用购买链接。')

    def pdd_binding_status(self, conversion_fields):
        fields = {key: value for key, value in conversion_fields.items() if key != 'content'}
        results = []
        labels = ('当前用户', '仅 PID') if 'custom_parameters' in fields else ('仅 PID',)
        for label in labels:
            try:
                payload = self.request('open_pdd_shouquan_query_new.ashx', fields)['authority_query_response']
                status = {'1': '已绑定', '0': '未绑定'}.get(str(payload.get('bind')), '状态未知')
            except PluginError:
                status = '查询失败'
            results.append(label + '：' + status)
            if fields.pop('custom_parameters', None) is None:
                break
        return ' 备案查询：' + '，'.join(results) + '。'

    def kaola_goods(self, link, user_sid):
        if not self.kaola_sid:
            raise PluginError('请配置折淘客考拉授权 SID。')
        tracking = str(int(hashlib.sha256(user_sid.encode()).hexdigest(), 16) % 10**11).zfill(11)
        result = self.request('open_kaola_zhuanke_api_zhuanlian.ashx', {'sid': self.kaola_sid,
            'targetUrl': link, 'trackingCode2': tracking})
        rows = result.get('data')
        row = rows[0] if isinstance(rows, list) and rows and isinstance(rows[0], dict) else {}
        for candidate in (row.get('shortLink'), row.get('shareLink')):
            url = valid_url(candidate)
            if url and platform_of(url) == 'kaola':
                return {'skuName': PLATFORMS['kaola'][0] + '商品', 'link': url, '_source': 'kaola',
                    '_provider': 'ztk', '_link_only': True}
        raise PluginError('未返回有效商品链接。')

    def find_coupon(self, original, user_sid):
        if original.get('_source') != 'taobao' or not self.sid or not re.fullmatch(r'mm_\d+_\d+_\d+', str(self.pid)):
            return None
        title = safe_text(original.get('skuName'), 500)
        image = product_image(original)
        product_id = original.get('_product_id') or ''
        if not (title and image and product_id):
            return None
        result = self.request('api_quanwang.ashx', {'sid': self.sid, 'pid': self.pid,
            'q': title, 'page': '1', 'page_size': '10', 'sort': 'new'})
        rows = result.get('content')
        if not isinstance(rows, list):
            return None
        for row in rows[:10]:
            if not isinstance(row, dict):
                continue
            item_id = str(row.get('tao_id') or '')
            discount = amount(row.get('coupon_info_money'))
            if (not re.fullmatch(r'[A-Za-z0-9_-]{5,120}', item_id) or not discount or Decimal(discount) <= 0
                    or safe_text(row.get('tao_title'), 500) != title):
                continue
            if item_id != product_id and image_key(row.get('pict_url')) != image_key(image):
                continue
            if item_id.isdigit():
                link = 'https://item.taobao.com/item.htm?id=' + item_id
            else:
                link = valid_url(row.get('item_url'))
                if not link.startswith('https://') or platform_of(link) != 'taobao':
                    continue
            alternate = self.goods(link, user_sid)
            if (safe_text(alternate.get('skuName'), 500) == title
                    and alternate.get('link') != original.get('link')
                    and usable_coupon(alternate)
                    and (alternate.get('_product_id') == product_id or image_key(product_image(alternate)) == image_key(image))):
                return alternate
            # Bound extra conversion traffic to one matched search result.
            break
        return None


def image_key(value):
    url = valid_url(value)
    if not url:
        return None
    parts = urllib.parse.urlsplit(url)
    return parts.hostname, parts.path


def comparable(one, two):
    if one.get('_source') != two.get('_source'):
        return False
    # IDs can use different opaque formats between vendors. Exact public product IDs
    # are strongest; otherwise require identical title, shop and buyer price.
    a, b = one.get('_product_id'), two.get('_product_id')
    if a and b and a == b:
        return True
    if a and b and str(a).isdigit() and str(b).isdigit():
        return False
    title = lambda d: re.sub(r'\s+', '', safe_text(d.get('skuName')))
    shop = lambda d: safe_text((d.get('shopInfo') or {}).get('shopName'))
    price = lambda d: amount((d.get('priceInfo') or {}).get('lowestCouponPrice'))
    return bool(title(one) and title(one) == title(two) and shop(one) and shop(one) == shop(two)
        and price(one) is not None and price(one) == price(two))


def select_result(candidates, errors=None, factors=None, preferred='jtk'):
    if not candidates:
        detail = '；'.join(PROVIDERS.get(k,k) + '：' + safe_text(v,140) for k,v in (errors or {}).items())
        raise PluginError('暂未查询到可用优惠。' + detail)
    factors = factors or {}
    ordered = sorted(candidates, key=lambda x: (bool(x.get('_link_only')), x.get('_provider') != preferred))
    base = ordered[0]
    eligible = [x for x in ordered if comparable(base, x) or x is base]
    def commission(item):
        value = amount(item.get('_commission'))
        if value is None:
            return None
        return Decimal(value) * Decimal(str(factors.get(item.get('_provider'), 1)))
    known = [x for x in eligible if commission(x) is not None]
    # Unknown is not zero. If a provider omits amount, preserve deterministic priority
    # and explicitly report incomplete comparison to the administrator.
    complete = len(eligible) == len(ordered) and len(known) == len(eligible)
    selected = max(known, key=commission) if complete and known else base
    result = dict(selected)
    result['_comparison'] = [{'provider': x.get('_provider', 'jtk'), 'amount': amount(x.get('_commission')),
        'adjusted': str(commission(x)) if commission(x) is not None else None,
        'comparable': x in eligible} for x in ordered]
    result['_errors'] = dict(errors or {})
    result['_selection'] = ('已比较同商品预估金额' if complete and len(known) > 1
        else '仅一个有效结果' if len(ordered) == 1 else '商品或金额信息不足，按接口优先级选择')
    return result


class ComparisonClient:
    def __init__(self, clients, factors=None, preferred='jtk'):
        self.clients, self.factors, self.preferred = clients, factors or {}, preferred

    def goods(self, link, sid):
        candidates, errors = [], {}
        source = query_platform(link)
        if valid_url(link):
            clients = {k: v for k, v in self.clients.items()
                if k != 'ztk' or source in ('taobao', 'pdd', 'vip', 'kaola')}
        else:
            clients = {k: v for k, v in self.clients.items() if k == 'ztk'}
            if not clients:
                raise PluginError('口令查询需启用折淘客并配置对应平台授权。')
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {k: pool.submit(v.goods, link, sid) for k, v in clients.items()}
            for name, future in futures.items():
                try:
                    item = dict(future.result())
                    if not valid_url(item.get('link')):
                        raise PluginError('未返回有效商品链接。')
                    item['_provider'] = name
                    candidates.append(item)
                except PluginError as error:
                    errors[name] = str(error)
                except Exception:
                    errors[name] = '接口返回异常。'
        result = select_result(candidates, errors, self.factors, self.preferred)
        if not usable_coupon(result):
            alternate = next((item for item in candidates if
                item.get('link') != result.get('link') and usable_coupon(item) and comparable(result, item)), None)
            search = getattr(clients.get('ztk'), 'find_coupon', None)
            if not alternate and search and result.get('_source') == 'taobao':
                try:
                    alternate = search(result, sid)
                except PluginError as error:
                    result['_errors']['ztk_search'] = str(error)
            if alternate:
                result['_alternative'] = alternate
        return result


def admin_details(data):
    selected = PROVIDERS.get(data.get('_provider'), '聚推客')
    lines = ['', '【管理员】', '选择接口：' + selected,
        '预估返利金额：' + ('¥' + amount(data.get('_commission')) if amount(data.get('_commission')) is not None else '未提供'),
        '选择依据：' + data.get('_selection', '单接口结果')]
    for row in data.get('_comparison', []):
        lines.append('%s：%s%s' % (PROVIDERS.get(row['provider'], row['provider']),
            '¥' + row['amount'] if row['amount'] is not None else '金额未知',
            '；调整后¥' + format(Decimal(row['adjusted']), '.2f') if row.get('adjusted') is not None else ''))
    for name, error in data.get('_errors', {}).items():
        lines.append('%s：%s' % (PROVIDERS.get(name, '同款查券' if name == 'ztk_search' else name), safe_text(error, 140)))
    lines.append('金额为平台预估，非已结算；税费及实际订单以平台为准。')
    return '\n'.join(lines)


def main():
    import middleware
    sender = middleware.Sender(middleware.getSenderID())
    state = None
    plugin = None
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
        sender.reply('⚠️ ' + (str(error) if plugin and plugin.admin() and plugin.private() else '暂未查询到可用优惠，请稍后重试或更换商品链接。'))
    except Exception:
        sender.reply('⚠️ 优惠券查询暂时不可用，请联系管理员。')
    finally:
        if state:
            state.close()


if __name__ == '__main__':
    main()
