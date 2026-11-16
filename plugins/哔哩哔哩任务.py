# [title: 哔哩哔哩任务]
# [icon: https://cdn.jsdelivr.net/gh/muzixing666/plugin@main/icons/bilibili-tasks.png]
# [language: python]
# [rule: ^(哔哩|B站)(登录|扫码登录|Cookie登录|查询|任务|运行|删除)$]
# [cron: 15 9 * * *]
# [platform: qq,qb,wx,gw,sb,wb,tg,tb,qx,xy,ip]
# [admin: false]
# [public: true]
# [disable: false]
# [author: muzixing666]
# [version: 1.0.3]
# [description: 扫码或 Cookie 绑定 B 站，查询账号与每日任务，尝试观看、分享、直播和漫画签到及大会员权益。投币数量由管理员设置，默认不投币。]
# [param: {"required":false,"key":"bili_tasks.coin_count","bool":false,"name":"每日投币目标","placeholder":"0","desc":"0 为不投币，最多 5；按当天已获得投币经验补足。"}]
# [param: {"required":false,"key":"bili_tasks.reserve","bool":false,"name":"保留硬币","placeholder":"10","desc":"投币后至少保留的硬币数，默认 10。"}]
# [param: {"required":false,"key":"bili_tasks.watch","bool":false,"name":"观看任务","placeholder":"1","desc":"1 开启，0 关闭。"}]
# [param: {"required":false,"key":"bili_tasks.share","bool":false,"name":"分享任务","placeholder":"1","desc":"1 开启，0 关闭。"}]
# [param: {"required":false,"key":"bili_tasks.live","bool":false,"name":"直播签到","placeholder":"1","desc":"1 开启，0 关闭。"}]
# [param: {"required":false,"key":"bili_tasks.manga","bool":false,"name":"漫画签到","placeholder":"1","desc":"1 开启，0 关闭，接口不可用时记录原因。"}]
# [param: {"required":false,"key":"bili_tasks.vip","bool":false,"name":"大会员权益","placeholder":"1","desc":"1 开启，0 关闭；仅对符合条件的账号尝试领取。"}]
# [param: {"required":false,"key":"bili_tasks.vip_sign","bool":false,"name":"大会员大积分签到","placeholder":"1","desc":"1 开启，0 关闭；仅会员尝试，结果以接口返回为准。"}]
# [param: {"required":false,"key":"bili_tasks.silver","bool":false,"name":"银瓜子兑换硬币","placeholder":"0","desc":"默认关闭；1 开启，消耗银瓜子兑换硬币。"}]

import contextlib
import fcntl
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

VENDOR = '/data/plugins/python_packages/bili_tasks_vendor'
if os.path.isdir(VENDOR): sys.path.insert(0, VENDOR)
import requests
from autman import middleware

ACCOUNTS, RESULTS = 'bili_tasks_accounts', 'bili_tasks_results'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
API = 'https://api.bilibili.com'

def make_session(cookie=''):
    session = requests.Session()
    session.trust_env = False
    session.headers.update({'User-Agent': UA, 'Referer': 'https://www.bilibili.com/', 'Origin': 'https://www.bilibili.com/'})
    for part in cookie.split(';'):
        name, sep, value = part.strip().partition('=')
        if sep and re.fullmatch(r'[A-Za-z0-9_]+', name): session.cookies.set(name, value, domain='.bilibili.com', path='/')
    return session

def call(session, method, url, **kwargs):
    try:
        response = session.request(method, url, timeout=15, allow_redirects=False, **kwargs)
        response.raise_for_status()
        obj = response.json()
        if not isinstance(obj, dict): return {'code': -999, 'message': '响应格式异常'}
        return obj
    except (requests.RequestException, ValueError):
        return {'code': -999, 'message': '网络或接口响应异常'}

def detail(result):
    if result.get('code') == 0: return '请求已接受'
    code = result.get('code', '未知')
    msg = str(result.get('message') or result.get('msg') or '')[:100]
    return '未完成（%s%s）' % (code, '：' + msg if msg else '')

def cookie_string(session):
    # Account verification requires these cookies; never log their values.
    found = {}
    for cookie in session.cookies:
        if cookie.name in ('SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'sid', 'buvid3', 'b_nut'):
            found[cookie.name] = cookie.value
    return '; '.join(k + '=' + v for k, v in found.items())

def user_info(session):
    r = call(session, 'GET', API + '/x/web-interface/nav')
    d = r.get('data') or {}
    if r.get('code') != 0 or not d.get('isLogin') or not d.get('mid'):
        return None
    return d

def reward_info(session, errors=None):
    r = call(session, 'GET', API + '/x/member/web/exp/reward')
    # A temporary network/response failure should not make the entire daily
    # experience workflow skip immediately. Do not retry business errors.
    if r.get('code') == -999:
        time.sleep(1)
        r = call(session, 'GET', API + '/x/member/web/exp/reward')
    if errors is not None and r.get('code') != 0:
        errors.append(detail(r))
    return r.get('data') if r.get('code') == 0 and isinstance(r.get('data'), dict) else None

def vip_status(info):
    vip = info.get('vip') or {}
    if not isinstance(vip, dict): vip = {}
    status = vip.get('status', vip.get('vipStatus', info.get('vipStatus')))
    return status if status in (0, 1) else None

def format_info(info, reward=None):
    level = info.get('level_info') or {}
    vip = vip_status(info)
    lines = ['账号：%s' % (info.get('uname') or '未知'), 'UID：%s' % info.get('mid'),
             '等级：%s，经验：%s / %s' % (level.get('current_level', '?'), level.get('current_exp', '?'), level.get('next_exp', '?')),
             '硬币：%s' % info.get('money', '?'), '大会员：%s' % ('有效' if vip == 1 else '无效' if vip == 0 else '状态未知')]
    if reward is None: lines.append('今日任务状态暂不可用')
    else:
        lines.append('今日任务：观看%s，分享%s，投币经验%s' % ('已完成' if reward.get('watch') else '未确认', '已完成' if reward.get('share') else '未确认', reward.get('coins', '?')))
    return '\n'.join(lines)

def flag(config, key, default=True):
    raw = config.get(key)
    v = '' if raw is None else str(raw).strip().lower()
    return default if not v else v not in ('0', 'false', 'off', 'no')

def number(config, key, default, maximum):
    raw = config.get(key)
    try: return min(maximum, max(0, int(str(default if raw is None or str(raw).strip() == '' else raw))))
    except ValueError: return default

def config_from_panel():
    return {k: middleware.bucketGet('bili_tasks', k) for k in ('coin_count', 'reserve', 'watch', 'share', 'live', 'manga', 'vip', 'vip_sign', 'silver')}

def vip_sign_info(session, csrf):
    now = int(time.time() * 1000)
    params = {'csrf': csrf, 'build': '8451100', 'disable_rcmd': 0, 'mobi_app': 'android', 'platform': 'android', 'statistics': '{"appId":1,"platform":3,"version":"8.45.1","abtest":""}', 't': now, 'ts': now // 1000}
    r = call(session, 'GET', API + '/x/vip/vip_center/sign_in/three_days_sign', params=params, headers={'Referer': 'https://big.bilibili.com/mobile/bigPoint/task'})
    data = r.get('data')
    return data if r.get('code') == 0 and isinstance(data, dict) else None

def run_tasks(session, info, config):
    logs = []
    csrf = session.cookies.get('bili_jct', domain='.bilibili.com') or ''
    if not csrf: return {'ok': False, 'lines': ['Cookie 缺少 bili_jct，请重新登录。']}
    errors = []
    before = reward_info(session, errors)
    if before is None: logs.append('每日经验状态读取失败%s，观看、分享和投币已跳过。' % ('：' + errors[0] if errors else ''))
    else:
        target = number(config, 'coin_count', 0, 5)
        need = (flag(config, 'watch') and not before.get('watch')) or (flag(config, 'share') and not before.get('share')) or target > 0
        videos = []
        if need:
            popular = call(session, 'GET', API + '/x/web-interface/popular', params={'ps': 30, 'pn': 1})
            videos = ((popular.get('data') or {}).get('list') or []) if popular.get('code') == 0 else []
            videos = [x for x in videos if isinstance(x, dict) and x.get('aid') and x.get('bvid')]
            random.shuffle(videos)
        if flag(config, 'watch'):
            if before.get('watch'): logs.append('观看：今日已完成')
            elif videos:
                v = videos[0]
                duration = v.get('duration')
                seconds = min(15, max(1, int(duration) - 1)) if isinstance(duration, (int, float)) else 15
                start = int(time.time())
                body = {'aid': v['aid'], 'bvid': v['bvid'], 'cid': v.get('cid', ''), 'mid': info['mid'], 'played_time': 0, 'realtime': 0, 'real_played_time': 0, 'csrf': csrf, 'start_ts': start, 'type': 3, 'dt': 2, 'play_type': 1}
                r = call(session, 'POST', API + '/x/click-interface/web/heartbeat', data=body)
                if r.get('code') == 0:
                    time.sleep(seconds)
                    body.update({'played_time': seconds, 'realtime': seconds, 'real_played_time': seconds, 'play_type': 3})
                    r = call(session, 'POST', API + '/x/click-interface/web/heartbeat', data=body)
                logs.append('观看：' + detail(r))
            else: logs.append('观看：无法获取视频')
        if flag(config, 'share'):
            if before.get('share'): logs.append('分享：今日已完成')
            elif videos:
                r = call(session, 'POST', API + '/x/web-interface/share/add', data={'aid': videos[0]['aid'], 'csrf': csrf})
                logs.append('分享：' + detail(r))
            else: logs.append('分享：无法获取视频')
        if target:
            exp = call(session, 'GET', API + '/x/web-interface/coin/today/exp')
            if exp.get('code') != 0 or not isinstance(exp.get('data'), (int, float)):
                logs.append('投币：无法核对今日进度，已跳过')
            else:
                needed = max(0, target - int(exp['data'] // 10))
                reserve = number(config, 'reserve', 10, 100000)
                balance = info.get('money')
                if not isinstance(balance, (int, float)): needed = 0; logs.append('投币：无法核对余额，已跳过')
                else: needed = min(needed, max(0, int(balance - reserve)))
                sent = 0
                for video in videos:
                    if sent >= needed: break
                    if str((video.get('owner') or {}).get('mid', '')) == str(info['mid']): continue
                    check = call(session, 'GET', API + '/x/web-interface/archive/coins', params={'aid': video['aid']})
                    if check.get('code') != 0 or (check.get('data') or {}).get('multiply', 0): continue
                    result = call(session, 'POST', API + '/x/web-interface/coin/add', data={'aid': video['aid'], 'multiply': 1, 'select_like': 0, 'csrf': csrf})
                    if result.get('code') != 0: logs.append('投币：' + detail(result)); break
                    sent += 1
                    time.sleep(1)
                logs.append('投币：本次接口接受 %s 枚，目标待补 %s 枚' % (sent, needed))
        else: logs.append('投币：未开启')
    if flag(config, 'live'):
        r = call(session, 'GET', 'https://api.live.bilibili.com/xlive/web-ucenter/v1/sign/DoSign')
        logs.append('直播签到：' + detail(r))
    if flag(config, 'silver', False):
        wallet = call(session, 'GET', 'https://api.live.bilibili.com/xlive/revenue/v1/wallet/myWallet', params={'need_bp': 1, 'need_metal': 1, 'platform': 'pc'})
        silver = (wallet.get('data') or {}).get('silver') if wallet.get('code') == 0 else None
        if not isinstance(silver, (int, float)): logs.append('银瓜子兑换：余额无法确认，已跳过')
        elif silver < 700: logs.append('银瓜子兑换：余额不足 700')
        else:
            r = call(session, 'POST', 'https://api.live.bilibili.com/xlive/revenue/v1/wallet/silver2coin', data={'csrf_token': csrf, 'csrf': csrf})
            logs.append('银瓜子兑换：' + detail(r))
    if flag(config, 'manga'):
        r = call(session, 'POST', 'https://manga.bilibili.com/twirp/activity.v1.Activity/ClockIn', params={'platform': 'android'}, headers={'Origin': 'https://manga.bilibili.com', 'Referer': 'https://manga.bilibili.com/'})
        message = str(r.get('message') or r.get('msg') or '')
        logs.append('漫画签到：今日已签到' if r.get('code') == 1 and '不能重复签到' in message else '漫画签到：' + detail(r))
    vip = vip_status(info)
    if flag(config, 'vip_sign') and vip == 1:
        sign_info = vip_sign_info(session, csrf)
        sign_state = (sign_info or {}).get('three_day_sign') or {}
        r = None
        if not sign_state.get('signed'):
            now = int(time.time() * 1000)
            r = call(session, 'POST', API + '/pgc/activity/score/task/sign2', params={'mobi_app': 'android', 'platform': 'android', 'csrf': csrf}, json={'device': 'phone', 't': now, 'ts': now // 1000}, headers={'Referer': 'https://big.bilibili.com/mobile/index'})
            sign_info = vip_sign_info(session, csrf)
            sign_state = (sign_info or {}).get('three_day_sign') or {}
        if sign_state.get('signed'):
            points = (sign_info.get('big_point') or {}).get('point', '未知')
            logs.append('大会员大积分签到：今日已完成，签到积分%s，当前积分%s' % (sign_state.get('score', '未知'), points))
        else:
            logs.append('大会员大积分签到：' + (detail(r) if r is not None else '状态未确认'))
    if flag(config, 'vip') and vip == 1:
        for item, name in [(1, 'B币券'), (2, '会员福利')]:
            r = call(session, 'POST', API + '/x/vip/privilege/receive', params={'type': item, 'csrf': csrf})
            logs.append(name + '：' + detail(r))
        r = call(session, 'POST', 'https://manga.bilibili.com/twirp/user.v1.User/GetVipReward', params={'reason_id': 1}, headers={'Origin': 'https://manga.bilibili.com', 'Referer': 'https://manga.bilibili.com/'})
        logs.append('会员漫画福利：' + detail(r))
    after = reward_info(session)
    if after is None: logs.append('最终每日经验状态不可用，到账情况未确认。')
    else: logs.append('最终状态：观看%s，分享%s，投币经验%s' % ('已完成' if after.get('watch') else '未确认', '已完成' if after.get('share') else '未确认', after.get('coins', '?')))
    return {'ok': True, 'lines': logs, 'before': before, 'after': after}

@contextlib.contextmanager
def account_lock(uid):
    root = Path('/data/plugins/python_packages/bili_tasks_locks');root.mkdir(parents=True, exist_ok=True)
    with open(root / (hashlib.sha256(str(uid).encode()).hexdigest() + '.lock'), 'a+') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try: yield
        finally: fcntl.flock(f, fcntl.LOCK_UN)

def qr_login(sender):
    session = make_session()
    result = call(session, 'GET', 'https://passport.bilibili.com/x/passport-login/web/qrcode/generate')
    data = result.get('data') or {}
    url, key = str(data.get('url') or ''), str(data.get('qrcode_key') or '')
    host = (urlsplit(url).hostname or '').lower()
    if result.get('code') != 0 or not (host == 'bilibili.com' or host.endswith('.bilibili.com')) or urlsplit(url).scheme != 'https' or not key:
        sender.reply('二维码获取失败，请稍后重试。'); return None
    try:
        js = "let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>require('/data/plugins/node_modules/qrcode').toDataURL(s).then(x=>process.stdout.write(x)).catch(()=>process.exit(1)))"
        image = subprocess.run(['node', '-e', js], input=url, text=True, capture_output=True, timeout=15, check=True).stdout
        if not image.startswith('data:image/png;base64,'): raise ValueError('二维码生成失败')
        sender.reply('请使用哔哩哔哩 App 扫码并确认，二维码约三分钟内有效。')
        sender.replyImage(image)
    except (OSError, subprocess.SubprocessError, ValueError):
        sender.reply('二维码生成失败，请联系管理员检查 qrcode 依赖。');return None
    deadline = time.monotonic() + 180; informed = False
    while time.monotonic() < deadline:
        time.sleep(3)
        r = call(session, 'GET', 'https://passport.bilibili.com/x/passport-login/web/qrcode/poll', params={'qrcode_key': key, 'source': 'main_mini'})
        data = r.get('data') or {}; code = data.get('code')
        if r.get('code') != 0: sender.reply('扫码状态查询失败，请重试。'); return None
        if code == 0:
            # Some deployments supply cookies in the redirect URL rather than Set-Cookie.
            url = str(data.get('url') or '')
            if urlsplit(url).hostname and urlsplit(url).hostname.endswith('.bilibili.com'):
                for name, value in parse_qsl(urlsplit(url).query):
                    if name in ('SESSDATA', 'bili_jct', 'DedeUserID', 'DedeUserID__ckMd5', 'sid'): session.cookies.set(name, value, domain='.bilibili.com', path='/')
            return cookie_string(session)
        if code == 86038: sender.reply('二维码已过期，请重新发送登录指令。'); return None
        if code == 86090 and not informed: sender.reply('已扫码，请在手机上确认。'); informed = True
    sender.reply('扫码等待超时，请重新登录。');return None

def main():
    sender = middleware.Sender(middleware.getSenderID())
    message = str(sender.getMessage() or '').strip()
    interactive = bool(re.fullmatch(r'(哔哩|B站)(登录|扫码登录|Cookie登录|查询|任务|运行|删除)', message))
    owner = ''
    if interactive:
        if str(sender.getChatID() or '').strip() not in ('', '0'):
            sender.reply('请私聊机器人管理 B 站账号。');return
        platform, user = str(sender.getImtype() or '').strip(), str(sender.getUserID() or '').strip()
        if not platform or not user: sender.reply('无法识别用户，请使用支持私聊的平台。');return
        owner = hashlib.sha256((platform + '\0' + user).encode()).hexdigest()
    def load(key):
        try:
            r = json.loads(str(middleware.bucketGet(ACCOUNTS, key) or '{}'))
            return r if isinstance(r, dict) else {}
        except (TypeError, ValueError): return {}
    def receive(timeout=120000): return str(sender.input(timeout, 1000, False) or '').strip()
    if interactive and (message.endswith('登录')):
        if message.endswith('Cookie登录'):
            sender.reply('请私聊发送完整 B 站 Cookie，发送 q 取消。输入消息会尝试撤回。')
            cookie = receive()
        else: cookie = qr_login(sender)
        if not cookie or str(cookie).lower() == 'q': return
        if len(cookie) > 20000: sender.reply('Cookie 内容过长。');return
        session = make_session(cookie)
        names = {c.name for c in session.cookies}
        if not {'SESSDATA', 'bili_jct'}.issubset(names): sender.reply('登录凭证不完整，请重试；原账号未更改。');return
        info = user_info(session)
        if not info: sender.reply('无法验证登录状态，请检查网络或重新登录；原账号未更改。');return
        record = {'cookie': cookie, 'uid': str(info['mid']), 'platform': platform, 'user': user}
        if not middleware.bucketSet(ACCOUNTS, owner, json.dumps(record, ensure_ascii=False)):
            sender.reply('账号保存失败，请联系管理员。');return
        sender.reply('绑定成功。\n' + format_info(info, reward_info(session)));return
    if interactive and message.endswith('删除'):
        sender.reply('回复“确认删除”删除 B 站账号和最近结果，其他内容取消。')
        if receive(60000) != '确认删除': sender.reply('已取消。');return
        removed = middleware.bucketDel(ACCOUNTS, owner)
        middleware.bucketDel(RESULTS, owner)
        sender.reply('账号记录已删除。' if removed else '删除失败，请联系管理员检查面板存储。');return
    def execute(key, record):
        cookie = str(record.get('cookie') or '')
        if not cookie: return {'ok': False, 'lines': ['尚未绑定账号。']}
        session = make_session(cookie); info = user_info(session)
        if not info: return {'ok': False, 'lines': ['无法验证 Cookie，请重新登录或检查网络。']}
        try:
            with account_lock(info['mid']): result = run_tasks(session, info, config_from_panel())
        except BlockingIOError: return {'ok': False, 'lines': ['该账号正在执行，请稍后重试。']}
        except Exception: return {'ok': False, 'lines': ['执行异常，请联系管理员查看运行环境。']}
        saved = middleware.bucketSet(RESULTS, key, json.dumps({'time': time.strftime('%Y-%m-%d %H:%M:%S'), 'result': result}, ensure_ascii=False))
        if not saved: result['lines'].append('运行结果保存失败。')
        return result
    if interactive:
        record = load(owner)
        if not record.get('cookie'): sender.reply('请先私聊发送“B站登录”或“B站Cookie登录”。');return
        if message.endswith('查询'):
            session = make_session(record['cookie']);info = user_info(session)
            sender.reply(format_info(info, reward_info(session)) if info else '无法验证 Cookie，请重新登录或检查网络。');return
        sender.reply('开始执行 B 站任务，请稍候。')
        result = execute(owner, record);sender.reply('\n'.join(result['lines']));return
    seen = set()
    for key in middleware.bucketAllKeys(ACCOUNTS):
        key = str(key); record = load(key);uid = str(record.get('uid') or '')
        if not uid or uid in seen: continue
        seen.add(uid);result = execute(key, record)
        print('账号执行结果：' + '；'.join(result['lines']), flush=True)
    print('B 站定时任务结束。', flush=True)

if __name__ == '__main__': main()
