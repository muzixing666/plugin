# [title: 必应积分任务]
# [language: python]
# [rule: ^必应(登录|账号登录|查询|积分|运行|删除)$]
# [cron: 20 8 * * *]
# [platform: qq,qb,wx,gw,sb,wb,tg,tb,qx,xy,ip]
# [admin: false]
# [public: true]
# [disable: false]
# [author: muzixing666]
# [version: 2.0.0-yh]
# [description: 必应搜索与积分任务。注册及邀请：https://rewards.bing.com/welcome?rh=5aIZctyKXxw&ref=rafsrchae 。积分可用于兑换所在地区提供的奖励，具体以微软页面为准。私聊发送必应登录，按照提示绑定账号。]
# [param: {"required":false,"key":"bing_rewards.concurrency","bool":false,"name":"账号并发数","placeholder":"2","desc":"同时运行账号数，默认2，最多4。"}]
# [param: {"required":false,"key":"bing_rewards.proxy_mode","bool":false,"name":"代理模式","placeholder":"direct / fixed / pool / api","desc":"管理员配置，默认直连。"}]
# [param: {"required":false,"key":"bing_rewards.proxy_fixed","bool":false,"name":"固定代理","placeholder":"http://地址:端口","desc":"fixed 模式使用。"}]
# [param: {"required":false,"key":"bing_rewards.proxy_pool","bool":false,"name":"代理池","placeholder":"地址1,地址2","desc":"pool 模式使用，按账号稳定选择。"}]
# [param: {"required":false,"key":"bing_rewards.proxy_api","bool":false,"name":"代理 API 地址","placeholder":"https://代理商接口地址","desc":"api 模式使用。"}]

import concurrent.futures
import contextlib
import base64
import fcntl
import gzip
import hashlib
import json
import os
import re
import shutil
import signal
import queue
import threading
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit, unquote

sys.path.insert(0, '/data/plugins/python_packages/bing_rewards_vendor')
import requests
from autman import middleware

ROOT = Path('/data/plugins/python_packages/bing_rewards_runtime')
ENGINE = ROOT / 'microsoft_rewards.js'
BUCKET = 'bing_rewards_accounts'
RESULTS = 'bing_rewards_results'
# 构建发布版时嵌入青龙脚本的适配版，避免依赖未固定版本的远程下载。
ENGINE_DATA = None
ENGINE_SHA256 = None

def proxy_url(value):
    value = str(value or '').strip()
    if '://' not in value:
        value = 'http://' + value
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or not parsed.port or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
        raise ValueError('代理格式错误')
    return value.rstrip('/')

def parse_proxy(value):
    if isinstance(value, str):
        try: return parse_proxy(json.loads(value))
        except json.JSONDecodeError: return proxy_url(value.splitlines()[0])
    if isinstance(value, list) and value: return parse_proxy(value[0])
    if isinstance(value, dict):
        if value.get('ip') and value.get('port'): return proxy_url(str(value['ip']) + ':' + str(value['port']))
        for key in ('proxy', 'address', 'server', 'data', 'result', 'list', 'proxies', 'proxy_list', 'ip_list'):
            if key in value: return parse_proxy(value[key])
    raise ValueError('代理接口返回无效')

def get_proxy(key):
    mode = str(middleware.bucketGet('bing_rewards', 'proxy_mode') or 'direct').strip().lower()
    if mode in ('', 'direct', 'off', '0'): return None
    if mode == 'fixed': value = proxy_url(middleware.bucketGet('bing_rewards', 'proxy_fixed'))
    elif mode == 'pool':
        items = [proxy_url(v) for v in re.split(r'[,\n\r]+', str(middleware.bucketGet('bing_rewards', 'proxy_pool') or '')) if v.strip()]
        if not items: raise ValueError('代理池为空')
        value = items[int(hashlib.sha256(key.encode()).hexdigest(), 16) % len(items)]
    elif mode == 'api':
        url = str(middleware.bucketGet('bing_rewards', 'proxy_api') or '').strip()
        if urlsplit(url).scheme not in ('http', 'https') or not urlsplit(url).hostname: raise ValueError('代理接口地址错误')
        session = requests.Session(); session.trust_env = False
        try:
            response = session.get(url, timeout=15, allow_redirects=False, stream=True)
            response.raise_for_status(); data = response.raw.read(65537)
            if len(data) > 65536: raise ValueError('代理接口返回过大')
            value = parse_proxy(data.decode('utf-8-sig'))
        finally: session.close()
    else: raise ValueError('代理模式错误')
    p = urlsplit(value)
    return {'url': p.scheme + '://' + p.hostname, 'port': p.port, 'username': unquote(p.username or ''), 'password': unquote(p.password or '')}

def count_workers():
    try: return max(1, min(4, int(str(middleware.bucketGet('bing_rewards', 'concurrency') or '2'))))
    except ValueError: return 2

def account_lock(record):
    return 'account-' + hashlib.sha256(record['email'].strip().lower().encode()).hexdigest()

@contextlib.contextmanager
def take_lock(path, wait=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a+') as f:
        os.chmod(path, 0o600)
        fcntl.flock(f, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
        try: yield
        finally: fcntl.flock(f, fcntl.LOCK_UN)

def run_account(key, record, proxy, mode, workers, receive_code=None):
    try:
        with take_lock(ROOT / 'locks' / 'engine-update'):
            if ENGINE_DATA and (not ENGINE.exists() or hashlib.sha256(ENGINE.read_bytes()).hexdigest() != ENGINE_SHA256):
                data = gzip.decompress(base64.b64decode(ENGINE_DATA))
                if hashlib.sha256(data).hexdigest() != ENGINE_SHA256: raise ValueError('引擎校验失败')
                temporary = ENGINE.with_name('.engine-' + uuid.uuid4().hex)
                temporary.write_bytes(data); os.chmod(temporary, 0o600); os.replace(temporary, ENGINE)
        if not ENGINE.exists(): return {'ok': False, 'error': '运行环境未安装'}
    except Exception:
        return {'ok': False, 'error': '任务引擎加载失败'}
    root = ROOT / 'accounts' / key
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    # 同一账号避免重复运行；全局锁让定时和手动执行共享并发上限。
    try:
        with take_lock(ROOT / 'locks' / account_lock(record), False):
            while True:
                for i in range(workers):
                    try:
                        with take_lock(ROOT / 'locks' / ('slot-' + str(i)), False):
                            return invoke_engine(root, record, proxy, mode, receive_code)
                    except BlockingIOError: pass
                time.sleep(1)
    except BlockingIOError:
        return {'ok': False, 'error': '该账号正在运行'}

def invoke_engine(root, record, proxy, mode, receive_code=None):
    env = os.environ.copy()
    for name in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
        env.pop(name, None)
    env['MS_REWARDS_ACCOUNTS'] = json.dumps([{'email': record['email'], 'password': record['password'], 'totpSecret': record.get('totp', '')}], ensure_ascii=False)
    env['YH_REWARDS_PROXY'] = json.dumps(proxy or {})
    env['YH_REWARDS_QUERY'] = '1' if mode == 'query' else '0'
    env['YH_INTERACTIVE'] = '1' if receive_code else '0'
    env['NODE_PATH'] = str(ROOT / 'node_modules')
    try:
        process = subprocess.Popen(['node', str(ENGINE)], cwd=str(root), env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, start_new_session=True)
        output, deadline, lines = [], time.monotonic() + 3600, queue.Queue()
        def read_lines():
            for line in process.stdout: lines.put(line)
            lines.put(None)
        threading.Thread(target=read_lines, daemon=True).start()
        while True:
            if time.monotonic() > deadline:
                os.killpg(process.pid, signal.SIGKILL); process.wait()
                return {'ok': False, 'error': '执行超时'}
            try: line = lines.get(timeout=1)
            except queue.Empty: continue
            if line is None: break
            if line.strip() == 'YH_NEED_EMAIL_CODE':
                code = receive_code() if receive_code else ''
                try: process.stdin.write(code + '\n'); process.stdin.flush()
                except BrokenPipeError: return {'ok': False, 'error': '验证码等待超时，请重新登录'}
            elif line.startswith('YH_RESULT:') or '需要邮箱验证码' in line:
                output.append(line)
        process.wait(); output = ''.join(output)
    except OSError: return {'ok': False, 'error': '无法启动任务环境'}
    marker = None
    for line in output.splitlines():
        if line.startswith('YH_RESULT:'):
            try: marker = json.loads(line[len('YH_RESULT:'):])
            except ValueError: pass
    if not marker or not marker.get('flowCompleted'):
        if '需要邮箱验证码' in output: return {'ok': False, 'error': '微软要求邮箱验证码，请私聊发送必应登录重新验证'}
        return {'ok': False, 'error': '微软登录或积分查询未成功，请检查账号、验证方式、代理与网络'}
    return {'ok': True, 'points': marker.get('finalPoints'), 'before': marker.get('initialPoints'), 'partial': bool(marker.get('partial'))}

def main():
    sender = middleware.Sender(middleware.getSenderID())
    msg = str(sender.getMessage() or '').strip()
    interactive = msg in ('必应登录', '必应账号登录', '必应查询', '必应积分', '必应运行', '必应删除')
    owner = ''
    if interactive:
        if str(sender.getChatID() or '').strip() not in ('', '0'):
            sender.reply('请私聊机器人管理账号。'); return
        platform, user = str(sender.getImtype() or '').strip(), str(sender.getUserID() or '').strip()
        if not platform or not user: sender.reply('无法识别用户。'); return
        owner = hashlib.sha256((platform + '\0' + user).encode()).hexdigest()
    def load(key):
        try: return json.loads(str(middleware.bucketGet(BUCKET, key) or '{}'))
        except (ValueError, TypeError): return {}
    def receive(): return str(sender.input(120000, 1000, False) or '').strip()
    workers = count_workers()
    if msg in ('必应登录', '必应账号登录'):
        sender.reply('请私聊发送微软账号邮箱，发送 q 取消。输入消息会尝试撤回。')
        email = receive()
        if not email or email.lower() == 'q': sender.reply('已取消。'); return
        if not re.fullmatch(r'[A-Za-z0-9_+.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', email): sender.reply('邮箱格式无效。'); return
        sender.reply('请私聊发送密码；发送 q 取消。')
        password = receive()
        if not password or password.lower() == 'q': sender.reply('已取消。'); return
        sender.reply('如启用动态口令，请发送 TOTP 密钥；没有则发送 0。')
        totp = receive()
        if not totp or totp.lower() == 'q': sender.reply('已取消。'); return
        record = {'email': email, 'password': password, 'totp': '' if totp == '0' else totp, 'platform': platform, 'user': user}
        try: proxy = get_proxy(owner)
        except Exception: sender.reply('代理配置不可用，请联系管理员。'); return
        sender.reply('正在验证登录，请稍候。')
        # 使用临时会话验证新密码，不能被以前的登录 Cookie 掩盖。
        test_key = 'verify-' + uuid.uuid4().hex
        def receive_code():
            sender.reply('微软已发送邮箱验证码，请在两分钟内私聊发送验证码；发送 q 取消。')
            return receive()
        try:
            result = run_account(test_key, record, proxy, 'query', workers, receive_code)
            if not result['ok']: sender.reply(result['error'] + '；原绑定未更改。'); return
            source = ROOT / 'accounts' / test_key / 'sessions'
            if not source.is_dir(): sender.reply('验证成功，但浏览器会话未保存；原绑定未更改。'); return
            try:
                with take_lock(ROOT / 'locks' / account_lock(record), False):
                    if not middleware.bucketSet(BUCKET, owner, json.dumps(record, ensure_ascii=False)):
                        sender.reply('面板保存失败。'); return
                    target = ROOT / 'accounts' / owner
                    target.mkdir(parents=True, exist_ok=True, mode=0o700)
                    old = target / ('sessions-old-' + uuid.uuid4().hex)
                    if (target / 'sessions').exists(): os.replace(target / 'sessions', old)
                    try: os.replace(source, target / 'sessions')
                    except OSError:
                        if old.exists(): os.replace(old, target / 'sessions')
                        sender.reply('账号已保存，但会话保存失败，请重新登录。'); return
                    shutil.rmtree(old, ignore_errors=True)
            except BlockingIOError:
                sender.reply('该账号正在运行，请稍后重新登录。'); return
            sender.reply('登录成功，当前积分：%s。' % result['points']); return
        finally:
            shutil.rmtree(ROOT / 'accounts' / test_key, ignore_errors=True)
    if msg == '必应删除':
        sender.reply('回复“确认删除”以删除账号；其他内容取消。')
        if receive() != '确认删除': sender.reply('已取消。'); return
        record = load(owner)
        if not record.get('email'):
            middleware.bucketDel(BUCKET, owner); middleware.bucketDel(RESULTS, owner)
            sender.reply('账号记录已删除。'); return
        try:
            with take_lock(ROOT / 'locks' / account_lock(record), False):
                middleware.bucketDel(BUCKET, owner); middleware.bucketDel(RESULTS, owner)
                shutil.rmtree(ROOT / 'accounts' / owner, ignore_errors=True)
        except BlockingIOError:
            sender.reply('账号正在运行，请结束后重试删除。'); return
        sender.reply('账号记录和浏览器会话已删除。'); return
    if interactive:
        record = load(owner)
        if not record.get('email') or not record.get('password'):
            sender.reply('尚未绑定账号密码，请发送“必应登录”。'); return
        try: proxy = get_proxy(owner)
        except Exception: sender.reply('代理配置不可用，请联系管理员。'); return
        sender.reply('正在执行，请稍候。')
        def receive_code():
            sender.reply('微软已发送邮箱验证码，请在两分钟内私聊发送验证码；发送 q 取消。')
            return receive()
        result = run_account(owner, record, proxy, 'run' if msg == '必应运行' else 'query', workers, receive_code)
        if not result['ok']: sender.reply(result['error']); return
        middleware.bucketSet(RESULTS, owner, json.dumps({'time': time.time(), **result}))
        sender.reply('当前积分：%s。%s' % (result['points'], '部分任务状态待确认。' if result['partial'] else '')); return
    records, seen = [], set()
    for key in middleware.bucketAllKeys(BUCKET):
        key = str(key); record = load(key)
        if record.get('email') and record.get('password'):
            email = record['email'].strip().lower()
            if email in seen: continue
            seen.add(email)
            try: records.append((key, record, get_proxy(key)))
            except Exception: print('账号代理配置不可用，已跳过。')
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(run_account, key, record, proxy, 'run', workers): key for key, record, proxy in records}
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try: result = future.result()
            except Exception: result = {'ok': False, 'error': '执行异常'}
            middleware.bucketSet(RESULTS, key, json.dumps({'time': time.time(), **result}))
            print('账号执行结束：' + ('成功' if result.get('ok') else result.get('error', '失败')))

if __name__ == '__main__': main()
