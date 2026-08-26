#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [language: python]
# [wb: true]
# [pin: true]
# [public: true]
# [rule: ^(登录)$]
# [rule: ^(登陆)$]
# [rule: ^(上车)$]
# [rule: ^(京东续期)$]
# [author: Muzixing]
# [title: 京东微信登录]
# [description: 京东微信登录插件<br>指令:登录/登陆/上车/京东续期<br>✨ 仅保留微信Code/YYB Go微信登录及京东续期<br>✨ 支持微信扫码绑定、YYB账号管理、单账号续期、一键续期、管理员批量续期、自动续期<br>✨ 支持京东CK有效性检测、双通道换CK、短信/人脸验证、代理及青龙写入。]
# ===================== YYB / 微信Code配置 =====================
# [param: {"required":false,"key":"jd_code_config.codeServerUrl","bool":false,"placeholder":"http://192.168.1.10:8000","name":"YYB Go服务地址","desc":"YYB Go API地址，例如 http://192.168.1.10:8000"}]
# [param: {"required":false,"key":"jd_code_config.codeApiType","bool":false,"placeholder":"yyb","name":"Code接口模式","desc":"yyb=YYB Go完整模式；simple=仅/login获取Code。续期、绑定、账号管理必须使用yyb"}]
# [param: {"required":false,"key":"jd_code_config.defaultRef","bool":false,"placeholder":"","name":"默认微信账号ref","desc":"YYB模式可填写账号ID/UIN/openid，留空则扫码"}]
# [param: {"required":false,"key":"jd_code_config.jdAppId","bool":false,"placeholder":"wxf95d0d80e9d5bfc0","name":"京东小程序AppID","desc":"默认 wxf95d0d80e9d5bfc0"}]
# [param: {"required":false,"key":"jd_code_config.QLVarName","bool":false,"placeholder":"JD_COOKIE","name":"青龙变量名","desc":"微信Code登录及续期写入的青龙变量名"}]
# [param: {"required":false,"key":"jd_code_config.qrPollInterval","bool":false,"placeholder":"3","name":"扫码轮询间隔","desc":"单位：秒"}]
# [param: {"required":false,"key":"jd_code_config.qrTimeout","bool":false,"placeholder":"180","name":"扫码超时","desc":"单位：秒，最少60秒"}]
# [param: {"required":false,"key":"jd_code_config.checkBeforeRefresh","bool":true,"name":"续期前检查","desc":"续期前先检查青龙中的JD_COOKIE是否仍有效，有效则跳过续期"}]
# [param: {"required":false,"key":"jd_code_config.autoRefreshOnLogin","bool":false,"name":"登录后自动续期","desc":"微信登录成功后立即执行一次续期"}]
# [param: {"required":false,"key":"jd_code_config.autoRefreshInterval","bool":false,"placeholder":"21600","name":"自动续期间隔","desc":"自动续期托管间隔，单位秒，默认6小时"}]

# ===================== 平台/权限兼容配置 =====================
# [param: {"required":false,"key":"dd_login_config.enableWX","bool":true,"name":"微信平台可用","desc":"是否允许在微信平台使用"}]
# [param: {"required":false,"key":"dd_login_config.enableQQ","bool":true,"name":"QQ群可用","desc":"是否允许在QQ群使用"}]
# [param: {"required":false,"key":"dd_login_config.enableQX","bool":true,"name":"QQ私聊可用","desc":"是否允许在QQ私聊使用"}]
# [param: {"required":false,"key":"dd_login_config.enableTG","bool":true,"name":"Telegram可用","desc":"是否允许在Telegram使用"}]
# [param: {"required":false,"key":"dd_login_config.enableOther","bool":true,"name":"其他平台可用","desc":"是否允许在其他平台使用"}]
# [param: {"required":false,"key":"dd_login_config.whiteList","bool":false,"placeholder":"留空不限","name":"群白名单","desc":"多个群ID用逗号分隔"}]
# [param: {"required":false,"key":"dd_login_config.pushAdminOn","bool":false,"name":"通知管理员","desc":"登录/续期结果通知管理员"}]
# [param: {"required":false,"key":"dd_login_config.pushPlatform","bool":false,"placeholder":"qq&wx","name":"通知平台","desc":"多个平台用&分隔"}]
# [param: {"required":false,"key":"dd_login_config.adminID","bool":false,"placeholder":"","name":"管理员ID","desc":"接收通知的管理员ID"}]

# ===================== 代理配置（兼容原插件） =====================
# [param: {"required":false,"key":"dd_login_config.ProxyAPI","bool":false,"placeholder":"http://api.xxx.com/getip","name":"代理API","desc":"Code服务、京东登录、CK检测共用代理API；留空直连"}]
# [param: {"required":false,"key":"dd_login_config.ProxyScope","bool":false,"placeholder":"all","name":"代理范围","desc":"all=全部；ck=CK检测；login=京东登录；code=YYB/Code服务"}]
# [param: {"required":false,"key":"dd_login_config.ProxyTimeout","bool":false,"placeholder":"10","name":"代理超时","desc":"代理API请求超时秒数"}]

# ===================== 青龙兼容配置 =====================
# [param: {"required":false,"key":"Joh_CK.Name1","bool":false,"placeholder":"容器1名称","name":"容器1名称(京东CK管理)","desc":"复用京东CK管理插件配置"}]
# [param: {"required":false,"key":"Joh_CK.container1","bool":false,"placeholder":"URL丨ClientID丨ClientSecret","name":"CK容器1(京东CK管理)","desc":"格式：URL丨ClientID丨ClientSecret"}]
# [param: {"required":false,"key":"Joh_CK.Name2","bool":false,"placeholder":"容器2名称","name":"容器2名称(京东CK管理)","desc":"复用京东CK管理插件配置"}]
# [param: {"required":false,"key":"Joh_CK.container2","bool":false,"placeholder":"URL丨ClientID丨ClientSecret","name":"CK容器2(京东CK管理)","desc":"格式：URL丨ClientID丨ClientSecret"}]
# [param: {"required":false,"key":"dd_jdck_config.Qinglong","bool":false,"placeholder":"URL丨ClientID丨ClientSecret","name":"默认青龙","desc":"没有container1/2时使用"}]

import base64
import json
import os
import random
import re
import time
import urllib.parse

import requests
import middleware

requests.packages.urllib3.disable_warnings()

TIMEOUT = 30
INPUT_TIMEOUT = 60
QUIT_KEYWORDS = ("q", "Q", "退出", "取消")
JD_APPID_DEFAULT = "wxf95d0d80e9d5bfc0"
JD_SILENT_AUTH_URL = "https://wxapplogin.m.jd.com/cgi-bin/jxpp/silentauthlogin"
JD_LOGIN_REDIRECT_URL = "https://wqlogin1.jd.com/mlogin/wxv3/LoginRedirect"
BUCKET_QL_TOKEN = "dd_login_ql_token"

sender_id = middleware.getSenderID()
sender = middleware.Sender(sender_id) if sender_id else None
userid = sender.getUserID() if sender else ""


def _log(*args):
    print("[京东微信登录]", *args)


def _cfg(bucket, key, default=""):
    try:
        value = middleware.bucketGet(bucket, key)
        return default if value in (None, "") else value
    except Exception:
        return default


def _to_bool(value, default=False):
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s == "true":
        return True
    if s == "false":
        return False
    return default


def _to_int(value, default=0):
    try:
        return int(str(value).strip())
    except Exception:
        return default


def friendly_err(e):
    msg = str(e)
    low = msg.lower()
    if "remote end closed" in low:
        return "代理连接被关闭"
    if "timed out" in low or "timeout" in low:
        return "连接超时"
    if "connection refused" in low:
        return "连接被拒绝"
    if "getaddrinfo" in low:
        return "域名解析失败"
    if "connection reset" in low:
        return "连接被重置"
    if "ssl" in low:
        return "SSL错误"
    return msg


def get_config():
    api_type = str(_cfg("jd_code_config", "codeApiType", "yyb")).strip().lower()
    if api_type not in ("yyb", "simple"):
        api_type = "yyb"

    return {
        "code_url": str(_cfg("jd_code_config", "codeServerUrl", "")).strip().rstrip("/"),
        "code_api_type": api_type,
        "code_default_ref": str(_cfg("jd_code_config", "defaultRef", "")).strip(),
        "code_jd_app_id": str(_cfg("jd_code_config", "jdAppId", JD_APPID_DEFAULT) or JD_APPID_DEFAULT).strip(),
        "code_ql_var_name": str(_cfg("jd_code_config", "QLVarName", "JD_COOKIE") or "JD_COOKIE").strip(),
        "code_qr_poll_interval": max(1, _to_int(_cfg("jd_code_config", "qrPollInterval", "3"), 3)),
        "code_qr_timeout": max(60, _to_int(_cfg("jd_code_config", "qrTimeout", "180"), 180)),
        "code_check_before_refresh": _to_bool(_cfg("jd_code_config", "checkBeforeRefresh", "true"), True),
        "code_auto_refresh_on_login": _to_bool(_cfg("jd_code_config", "autoRefreshOnLogin", "false"), False),
        "code_auto_refresh_interval": max(60, _to_int(_cfg("jd_code_config", "autoRefreshInterval", "21600"), 21600)),
        "proxy_api": str(_cfg("dd_login_config", "ProxyAPI", "") or _cfg("dd_jd_query_config", "ProxyAPI", "")).strip(),
        "proxy_scope": str(_cfg("dd_login_config", "ProxyScope", "all")).strip().lower() or "all",
        "proxy_timeout": max(3, _to_int(_cfg("dd_login_config", "ProxyTimeout", "10"), 10)),
        "white_list": str(_cfg("dd_login_config", "whiteList", "")).strip(),
        "push_admin_on": _to_bool(_cfg("dd_login_config", "pushAdminOn", "false"), False),
        "push_platform": str(_cfg("dd_login_config", "pushPlatform", "")).strip(),
        "admin_id": str(_cfg("dd_login_config", "adminID", "")).strip(),
        "enableqq": _to_bool(_cfg("dd_login_config", "enableQQ", "true"), True),
        "enableqx": _to_bool(_cfg("dd_login_config", "enableQX", "true"), True),
        "enablewx": _to_bool(_cfg("dd_login_config", "enableWX", "true"), True),
        "enabletg": _to_bool(_cfg("dd_login_config", "enableTG", "true"), True),
        "enableother": _to_bool(_cfg("dd_login_config", "enableOther", "true"), True),
    }


def check_admin(s, config):
    try:
        return bool(s.isAdmin())
    except Exception:
        return False


def check_white_list(s, config):
    if not config["white_list"]:
        return True
    try:
        group_id = str(s.getGroupID() or s.getChatID() or "")
    except Exception:
        group_id = ""
    allowed = [x.strip() for x in re.split(r"[,，]", config["white_list"]) if x.strip()]
    return not group_id or group_id in allowed


def check_platform_enabled(config, s):
    try:
        platform = str(s.getPlatform() or "").lower()
    except Exception:
        platform = ""
    if platform in ("wx", "wxmp"):
        return config["enablewx"]
    if platform in ("qq", "qb"):
        return config["enableqq"]
    if platform == "qx":
        return config["enableqx"]
    if platform == "tg":
        return config["enabletg"]
    return config["enableother"]


def notify_admin(config, message):
    if not config.get("push_admin_on") or not config.get("admin_id"):
        return
    try:
        platforms = [x.strip() for x in config.get("push_platform", "").split("&") if x.strip()]
        for p in platforms:
            try:
                middleware.sendMessage(p, config["admin_id"], message)
            except Exception:
                pass
    except Exception:
        pass


def get_input(s, timeout=INPUT_TIMEOUT, validator=None, error_tip=None):
    try:
        value = s.input(timeout * 1000, 1, False)
    except Exception:
        s.reply("⏰ 操作超时，已取消")
        return None
    if not value:
        s.reply("⏰ 操作超时，已取消")
        return None
    if isinstance(value, dict):
        value = value.get("text") or value.get("message") or ""
    text = str(value).strip()
    if text in QUIT_KEYWORDS:
        s.reply("✅ 已退出")
        return None
    if validator and not validator(text):
        if error_tip:
            s.reply(error_tip)
        return None
    return text


# ===================== 代理 =====================

def _proxy_in_scope(scope, area):
    scope = (scope or "all").strip().lower()
    if scope in ("no", "off", "false", "0", "disable", "disabled"):
        return False
    if scope in ("all", "*", ""):
        return True
    return area in [x.strip() for x in scope.replace("，", ",").split(",")]


def _extract_proxy_from_text(text):
    text = str(text or "").strip()
    if not text:
        return None

    for line in re.split(r"[\r\n,]+", text):
        line = line.strip()
        if not line:
            continue
        m = re.search(
            r"(?:(?P<user>[^:@\s]+):(?P<pwd>[^@\s]+)@)?"
            r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3}):(?P<port>\d{2,5})",
            line,
        )
        if not m:
            m = re.search(
                r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3})[:：](?P<port>\d{2,5})",
                line,
            )
        if not m:
            continue

        ip = m.group("ip")
        port = int(m.group("port"))
        if not (1 <= port <= 65535):
            continue

        user = m.groupdict().get("user") or ""
        pwd = m.groupdict().get("pwd") or ""
        if user and pwd:
            proxy_url = f"http://{urllib.parse.quote(user)}:{urllib.parse.quote(pwd)}@{ip}:{port}"
        else:
            proxy_url = f"http://{ip}:{port}"
        return {"url": proxy_url, "display": f"{ip}:{port}"}
    return None


def fetch_proxy_info(proxy_api, timeout=10):
    if not proxy_api:
        return None
    try:
        resp = requests.get(
            proxy_api,
            timeout=timeout,
            verify=False,
            headers={"User-Agent": "JDLoginPlugin/4.0.0", "Accept": "*/*"},
        )
        info = _extract_proxy_from_text(resp.text)
        if info:
            _log(f"代理获取成功: {info['display']}")
        return info
    except Exception as e:
        _log(f"代理API拉取失败: {friendly_err(e)}")
        return None


def build_proxies(proxy_info):
    if not proxy_info:
        return None
    return {"http": proxy_info["url"], "https": proxy_info["url"]}


def _request_with_proxy(method, url, proxy_api=None, scope="all", area="login", timeout=10, **kwargs):
    proxies = None
    if proxy_api and _proxy_in_scope(scope, area):
        proxies = build_proxies(fetch_proxy_info(proxy_api, timeout))
    request_kwargs = dict(kwargs)
    request_kwargs.setdefault("timeout", timeout)
    request_kwargs.setdefault("verify", False)
    if proxies:
        request_kwargs["proxies"] = proxies

    try:
        return requests.request(method, url, **request_kwargs)
    except Exception as e:
        if proxies:
            _log(f"代理请求失败({friendly_err(e)})，回退直连")
            request_kwargs.pop("proxies", None)
            return requests.request(method, url, **request_kwargs)
        raise e


# ===================== 青龙 =====================

def load_ql_panels():
    panels = []
    for i in (1, 2):
        value = _cfg("Joh_CK", f"container{i}", "")
        if value:
            parts = str(value).split("丨")
            if len(parts) >= 3:
                name = _cfg("Joh_CK", f"Name{i}", f"容器{i}")
                panels.append({
                    "Name": name,
                    "Host": parts[0].strip().rstrip("/"),
                    "ClientID": parts[1].strip(),
                    "ClientSecret": parts[2].strip(),
                    "Version": "2.17.0",
                })

    if not panels:
        value = _cfg("dd_jdck_config", "Qinglong", "")
        if value:
            parts = str(value).split("丨")
            if len(parts) >= 3:
                panels.append({
                    "Name": "默认容器",
                    "Host": parts[0].strip().rstrip("/"),
                    "ClientID": parts[1].strip(),
                    "ClientSecret": parts[2].strip(),
                    "Version": "2.17.0",
                })
    return panels


class QingLongClient:
    def __init__(self, panel):
        self.panel = panel
        self.host = str(panel.get("Host") or "").rstrip("/")
        self.client_id = str(panel.get("ClientID") or "")
        self.client_secret = str(panel.get("ClientSecret") or "")
        version = str(panel.get("Version") or "2.17.0").split(".")
        try:
            minor = int(version[1])
        except Exception:
            minor = 17
        self.id_key = "_id" if minor < 11 else "id"

    def get_token(self, force=False):
        cache_key = f"{self.client_id}_token"
        if not force:
            cached = middleware.bucketGet(BUCKET_QL_TOKEN, cache_key)
            if cached:
                try:
                    data = json.loads(str(cached))
                    if int(data.get("expiration", 0)) * 1000 > int(time.time() * 1000):
                        return data
                except Exception:
                    pass

        if not self.host or not self.client_id or not self.client_secret:
            return None

        try:
            url = (
                f"{self.host}/open/auth/token"
                f"?client_id={urllib.parse.quote(self.client_id)}"
                f"&client_secret={urllib.parse.quote(self.client_secret)}"
            )
            resp = requests.get(url, timeout=30, verify=False)
            body = resp.json()
            if body.get("code") == 200 and "data" in body:
                middleware.bucketSet(BUCKET_QL_TOKEN, cache_key, json.dumps(body["data"]))
                return body["data"]
        except Exception:
            pass
        return None

    def request(self, method, path, body=None):
        token = self.get_token()
        if not token:
            raise Exception("获取青龙Token失败")

        headers = {
            "Authorization": f"{token.get('token_type', 'Bearer')} {token.get('token')}",
            "Content-Type": "application/json",
        }
        url = f"{self.host}{path}"

        def send():
            if method == "GET":
                return requests.get(url, headers=headers, timeout=30, verify=False)
            if method == "POST":
                return requests.post(url, headers=headers, json=body or [], timeout=30, verify=False)
            if method == "PUT":
                return requests.put(url, headers=headers, json=body or [], timeout=30, verify=False)
            raise Exception("不支持的请求方法")

        resp = send()
        if resp.status_code == 401:
            token = self.get_token(force=True)
            if not token:
                raise Exception("青龙Token刷新失败")
            headers["Authorization"] = f"{token.get('token_type', 'Bearer')} {token.get('token')}"
            resp = send()

        data = resp.json()
        if data.get("code") == 200:
            return data.get("data")
        raise Exception(data.get("message") or f"青龙请求失败 HTTP {resp.status_code}")

    def all_envs(self):
        return self.request("GET", "/open/envs") or []

    def add_envs(self, envs):
        return self.request("POST", "/open/envs", envs)

    def edit_env(self, env):
        return self.request("PUT", "/open/envs", env)

    def enable_env(self, env_id):
        return self.request("PUT", "/open/envs/enable", [env_id])


def decode_pin(pin):
    try:
        return urllib.parse.unquote(str(pin))
    except Exception:
        return str(pin)


def get_pin_from_cookie(cookie):
    m = re.search(r"pt_pin=([^;\s]+)", cookie or "")
    return m.group(1) if m else ""


def commit_cookie_to_ql(s, uid, cookie_value, env_name="JD_COOKIE", skip_bind=False, append_remark=None):
    panels = load_ql_panels()
    if not panels:
        s.reply("⚠️ 未配置青龙面板，Cookie未写入\n💡 请配置 Joh_CK.container1")
        return False, []

    pin = get_pin_from_cookie(cookie_value)
    if not pin:
        s.reply("❌ Cookie格式错误，未找到pt_pin")
        return False, []

    pin_dec = decode_pin(pin)
    final_cookie = cookie_value

    if any(ord(c) > 127 for c in pin_dec):
        encoded = urllib.parse.quote(pin_dec, safe="")
        final_cookie = re.sub(r"pt_pin=([^;\s]+)", f"pt_pin={encoded}", cookie_value)

    success_panels = []

    for panel in panels:
        try:
            ql = QingLongClient(panel)
            envs = ql.all_envs()
            matched = None

            for env in envs:
                if env.get("name") != env_name:
                    continue
                value = str(env.get("value", ""))
                env_pin = get_pin_from_cookie(value)
                if not env_pin:
                    continue
                env_pin_dec = decode_pin(env_pin)
                if pin in (env_pin, env_pin_dec) or pin_dec in (env_pin, env_pin_dec):
                    matched = env
                    break

            remark = pin_dec
            if matched:
                env_id = matched.get(ql.id_key) or matched.get("_id") or matched.get("id")
                old = str(matched.get("remarks", "") or "")
                if old:
                    remark = old
                    if append_remark and append_remark not in remark:
                        remark = f"{remark} ({append_remark})"
                elif append_remark:
                    remark = f"{pin_dec} ({append_remark})"

                ql.edit_env({
                    "name": env_name,
                    "value": final_cookie,
                    "remarks": remark,
                    ql.id_key: env_id,
                })
                if env_id:
                    ql.enable_env(env_id)
            else:
                if append_remark:
                    remark = f"{pin_dec} ({append_remark})"
                ql.add_envs([{
                    "name": env_name,
                    "value": final_cookie,
                    "remarks": remark,
                }])
            success_panels.append(panel.get("Name", "未知"))
        except Exception as e:
            _log(f"青龙[{panel.get('Name','未知')}]写入失败: {friendly_err(e)}")

    return bool(success_panels), success_panels


def check_ck_validity(cookie, proxy_api=None, proxy_scope="all"):
    try:
        cookie.encode("latin-1")
    except UnicodeEncodeError:
        m = re.search(r"pt_pin=([^;\s]+)", cookie)
        if m:
            cookie = cookie.replace(
                f"pt_pin={m.group(1)}",
                f"pt_pin={urllib.parse.quote(m.group(1), safe='')}",
            )

    headers = {
        "Cookie": cookie,
        "Referer": "https://h5.m.jd.com/",
        "User-Agent": "jdapp;iPhone;10.1.2;15.0;network/wifi",
    }

    for _ in range(2):
        try:
            if proxy_api and _proxy_in_scope(proxy_scope, "ck"):
                resp = _request_with_proxy(
                    "get",
                    "https://plogin.m.jd.com/cgi-bin/ml/islogin",
                    proxy_api=proxy_api,
                    scope=proxy_scope,
                    area="ck",
                    headers=headers,
                    timeout=10,
                )
            else:
                resp = requests.get(
                    "https://plogin.m.jd.com/cgi-bin/ml/islogin",
                    headers=headers,
                    timeout=10,
                    verify=False,
                )
            data = resp.json()
            if str(data.get("islogin")) == "1":
                return True
        except Exception:
            time.sleep(1)
    return False


# ===================== YYB Go 微信扫码 =====================

def _code_create_qr(config):
    if config.get("code_api_type") != "yyb":
        return None
    try:
        resp = _request_with_proxy(
            "post",
            f"{config['code_url']}/qr",
            proxy_api=config.get("proxy_api"),
            scope=config.get("proxy_scope", "all"),
            area="code",
            params={"as_base64": "true"},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data")
        _log("创建二维码失败:", data)
    except Exception as e:
        _log("创建二维码异常:", friendly_err(e))
    return None


def _code_poll_qr(config, session_id):
    try:
        resp = _request_with_proxy(
            "get",
            f"{config['code_url']}/qr/{urllib.parse.quote(str(session_id))}/poll",
            proxy_api=config.get("proxy_api"),
            scope=config.get("proxy_scope", "all"),
            area="code",
            timeout=TIMEOUT,
        )
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data", {}).get("status", "unknown")
    except Exception as e:
        _log("二维码轮询异常:", friendly_err(e))
    return "unknown"


def _code_confirm_qr(config, session_id):
    try:
        resp = _request_with_proxy(
            "post",
            f"{config['code_url']}/qr/{urllib.parse.quote(str(session_id))}/confirm",
            proxy_api=config.get("proxy_api"),
            scope=config.get("proxy_scope", "all"),
            area="code",
            timeout=TIMEOUT,
        )
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data")
    except Exception as e:
        _log("确认二维码异常:", friendly_err(e))
    return None


def _code_get_code(config, ref):
    url = config.get("code_url", "")
    app_id = config.get("code_jd_app_id", JD_APPID_DEFAULT)

    try:
        if config.get("code_api_type") == "simple":
            resp = _request_with_proxy(
                "get",
                f"{url}/login",
                proxy_api=config.get("proxy_api"),
                scope=config.get("proxy_scope", "all"),
                area="code",
                params={"appId": app_id},
                timeout=TIMEOUT,
            )
            data = resp.json()
            if data.get("err") == 0 and data.get("code"):
                return data.get("code"), None
            return None, None

        resp = _request_with_proxy(
            "post",
            f"{url}/wxapp/getCode",
            proxy_api=config.get("proxy_api"),
            scope=config.get("proxy_scope", "all"),
            area="code",
            json={"ref": str(ref), "app_id": app_id},
            timeout=TIMEOUT,
        )
        data = resp.json()
        if data.get("code") != 0:
            return None, None

        wx_data = data.get("data") or {}
        openid = wx_data.get("openid") or ""
        result = wx_data.get("result")
        code = (
            result.get("code")
            if isinstance(result, dict)
            else (result if isinstance(result, str) and result else wx_data.get("code"))
        )
        if code:
            return code, openid or None
    except Exception as e:
        _log("获取微信Code异常:", friendly_err(e))
    return None, None


# ===================== 京东双通道换CK =====================

def _gen_state():
    return (
        f"snsapi_base{random.randint(10**19, 10**20 - 1)}-"
        f"{int(time.time())}-{random.randint(100000,999999)}-"
        f"{random.randint(10000,99999)}-0-default-0-1-biz_wxMy"
    )


def _extract_set_cookie_headers(resp):
    result = []
    try:
        raw = getattr(resp.raw, "headers", None)
        if raw is not None and hasattr(raw, "get_all"):
            values = raw.get_all("Set-Cookie")
            if values:
                result.extend(str(v).strip() for v in values if str(v).strip())
    except Exception:
        pass
    if result:
        return result
    try:
        for c in resp.cookies:
            if c.name and c.value:
                result.append(f"{c.name}={c.value}")
    except Exception:
        pass
    return result


def _jd_code_login(code, app_id, openid=None, proxy_api=None, proxy_scope="all"):
    if not app_id:
        app_id = JD_APPID_DEFAULT

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 26_5_2) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 "
            "MicroMessenger/8.0.75 NetType/WIFI Language/zh_CN"
        ),
        "Referer": f"https://servicewechat.com/{app_id}/676/page-frame.html",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Connection": "keep-alive",
    }

    session = requests.Session()
    session.headers.update(headers)
    session.verify = False

    if openid:
        ts_part = f"{int(time.time()*1000)}{random.randint(1000000000,9999999999)}"
        rand_part = f"JA2019_{random.randint(1000000,9999999)}"
        jdwxapp_value = f"{ts_part}.{rand_part}.{app_id}..{openid}"
        session.cookies.set("__jdwxapp", jdwxapp_value, domain=".jd.com")
        session.cookies.set("wxapp_openid", openid, domain=".jd.com")
        session.cookies.set("wq_unionid", openid, domain=".jd.com")
        session.cookies.set("open_id", openid, domain=".jd.com")
        session.cookies.set("wxapp_type", "1", domain=".jd.com")
        session.cookies.set("wxapp_version", "11.18.300", domain=".jd.com")

    try:
        silent_headers = headers.copy()
        silent_headers["Content-Type"] = "application/x-www-form-urlencoded"
        silent_headers["Accept-Encoding"] = "gzip,compress,br,deflate"
        payload = (
            f"code={urllib.parse.quote(str(code))}&eid_token="
            f"&returnurl=%2Fpages%2Flogin%2Fweb-view%2Fweb-view"
            f"&wxappid={app_id}&appid=1340&client_ver=1.3.2"
            f"&ts={int(time.time())}&sign=688acba45785e9770f2569f93018732a"
        )

        resp = _request_with_proxy(
            "post",
            JD_SILENT_AUTH_URL,
            proxy_api=proxy_api,
            scope=proxy_scope,
            area="login",
            data=payload,
            headers=silent_headers,
            timeout=TIMEOUT,
        )
        data = resp.json()

        if data.get("pt_key") and data.get("pt_pin"):
            pin = urllib.parse.unquote(data["pt_pin"])
            return f"pt_key={data['pt_key']};pt_pin={data['pt_pin']};", pin, None, 0, ""

        err_msg = data.get("message") or data.get("msg") or data.get("errMsg") or "silentauthlogin未返回凭证"
        err_code = data.get("err_code") or data.get("errCode") or 0
        try:
            err_code_int = int(err_code)
        except Exception:
            err_code_int = 0

        if err_code_int == 128:
            jmp = data.get("jmp_url") or data.get("JmpUrl") or ""
            return None, None, "需要短信/语音验证，请完成验证后等待60秒再输入ok重试", 128, jmp
        if err_code_int == 118:
            return None, None, "可能需要人脸二次验证，请在京东App完成验证后再试", 118, ""
        err_log = f"silentauthlogin响应: {data} | 错误: {err_msg}"
    except Exception as e:
        err_log = f"silentauthlogin异常: {friendly_err(e)}"

    state = _gen_state()
    url = (
        f"{JD_LOGIN_REDIRECT_URL}?code={urllib.parse.quote(str(code))}"
        f"&state={urllib.parse.quote(state)}"
    )

    try:
        resp = _request_with_proxy(
            "get",
            url,
            proxy_api=proxy_api,
            scope=proxy_scope,
            area="login",
            allow_redirects=False,
            timeout=TIMEOUT,
        )
    except Exception as e:
        return None, None, f"LoginRedirect请求失败: {friendly_err(e)}", 0, ""

    current = resp
    redirect_count = 0
    pt_key = None
    pt_pin = None

    while redirect_count < 10:
        for raw in _extract_set_cookie_headers(current):
            m = re.search(r"pt_key=([^;]+)", raw)
            if m:
                pt_key = m.group(1)
            m = re.search(r"pt_pin=([^;]+)", raw)
            if m:
                pt_pin = m.group(1)
            if not pt_key:
                m = re.search(r"wq_skey=([^;]+)", raw)
                if m:
                    pt_key = m.group(1)
            if not pt_key:
                m = re.search(r"sfstoken=([^;]+)", raw)
                if m:
                    pt_key = m.group(1)

        if pt_key and pt_pin:
            break

        if current.status_code not in (301,302,303,307,308):
            break

        location = current.headers.get("Location", "")
        if not location:
            break
        if location.startswith("/"):
            parsed = urllib.parse.urlparse(current.url)
            location = f"{parsed.scheme}://{parsed.netloc}{location}"

        try:
            current = _request_with_proxy(
                "get",
                location,
                proxy_api=proxy_api,
                scope=proxy_scope,
                area="login",
                allow_redirects=False,
                timeout=TIMEOUT,
            )
            redirect_count += 1
        except Exception:
            break

    if pt_key and pt_pin:
        return (
            f"pt_key={pt_key};pt_pin={pt_pin};",
            urllib.parse.unquote(pt_pin),
            None,
            0,
            "",
        )

    return None, None, f"{err_log} | LoginRedirect未提取到CK", 0, ""


def _jd_code_login_lt(code, app_id, proxy_api=None, proxy_scope="all"):
    if not app_id:
        app_id = JD_APPID_DEFAULT

    url = "https://wq.jd.com/mlogin/wxapp/login_lt"
    params = {
        "appid": app_id,
        "code": code,
        "type": "silent",
        "isPopup": "false",
        "isIgnoreCookie": "false",
        "isOfficialPin": "false",
        "loginColor": "{}",
        "returnUrl": "pages/my/index/index",
        "deviceName": "iPhone",
        "deviceOS": "iOS",
        "deviceOSVersion": "17.0",
        "deviceVersion": "8.0.49",
        "g_tk": "0",
        "g_ty": "ls",
    }
    headers = {
        "User-Agent": f"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 "
                      f"(KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.49 "
                      f"NetType/WIFI Language/zh_CN miniProgram/{app_id}",
        "Referer": f"https://servicewechat.com/{app_id}/873/page-frame.html",
        "Accept": "application/json,text/plain,*/*",
    }

    session = requests.Session()
    session.verify = False

    def extract_pt(jar):
        pk = pp = ""
        for c in jar:
            if c.name == "pt_key" and c.value:
                pk = c.value
            if c.name == "pt_pin" and c.value:
                pp = c.value
        if pk and pp:
            return f"pt_key={pk};pt_pin={pp};", urllib.parse.unquote(pp)
        return None, None

    try:
        proxies = None
        if proxy_api and _proxy_in_scope(proxy_scope, "login"):
            proxies = build_proxies(fetch_proxy_info(proxy_api, timeout=10))

        resp = session.get(
            url,
            params=params,
            headers=headers,
            proxies=proxies,
            timeout=15,
            verify=False,
        )

        ck, pin = extract_pt(session.cookies)
        if ck:
            return ck, pin, None, 0, ""

        data = resp.json()
        info = data.get("info") or (data.get("data") or {}).get("info") or {}
        acrj_url = info.get("ACRJUrl") or info.get("acrjUrl")
        acrj_state = info.get("ACRJState") or info.get("acrjState")

        if acrj_url:
            if acrj_url.startswith("//"):
                acrj_url = "https:" + acrj_url
            elif acrj_url.startswith("/"):
                acrj_url = "https://wq.jd.com" + acrj_url
            if acrj_state and "ACRJState=" not in acrj_url:
                acrj_url += ("&" if "?" in acrj_url else "?") + f"ACRJState={acrj_state}"

            for _ in range(5):
                r = session.get(
                    acrj_url,
                    headers=headers,
                    proxies=proxies,
                    allow_redirects=False,
                    timeout=15,
                )
                ck, pin = extract_pt(session.cookies)
                if ck:
                    return ck, pin, None, 0, ""
                if r.status_code in (301,302,303,307,308):
                    loc = r.headers.get("Location")
                    if not loc:
                        break
                    acrj_url = urllib.parse.urljoin(acrj_url, loc)
                else:
                    break

        return None, None, f"login_lt未返回有效凭证: {str(data)[:120]}", 0, ""
    except Exception as e:
        return None, None, f"login_lt异常: {friendly_err(e)}", 0, ""


def _do_login_with_fallback(config, ref, app_id, openid):
    code, code_openid = _code_get_code(config, ref)
    if not code:
        return None, None, "获取Code失败，微信授权可能已失效", 0, ""

    cookie, pin, err_log, err_code, jmp = _jd_code_login(
        code,
        app_id,
        openid=code_openid or openid,
        proxy_api=config.get("proxy_api"),
        proxy_scope=config.get("proxy_scope", "all"),
    )

    if not cookie and err_code not in (118, 128):
        _log(f"主通道失败：{err_log}，切换login_lt备用通道")
        code2, _ = _code_get_code(config, ref)
        if code2:
            cookie, pin, err_log, err_code, jmp = _jd_code_login_lt(
                code2,
                app_id,
                proxy_api=config.get("proxy_api"),
                proxy_scope=config.get("proxy_scope", "all"),
            )
        else:
            err_log += " | 备用通道重新获取Code失败"

    return cookie, pin, err_log, err_code, jmp


# ===================== YYB账号绑定/续期 =====================

def _get_user_bound_code_accounts(uid, config):
    if config.get("code_api_type") != "yyb":
        return []
    url = config.get("code_url", "")
    if not url:
        return []
    try:
        resp = requests.get(f"{url}/accounts", timeout=10, verify=False)
        data = resp.json()
        if data.get("code") == 0 and isinstance(data.get("data"), list):
            return list(data["data"])
    except Exception as e:
        _log("拉取YYB账号列表失败:", friendly_err(e))
    return []


def _get_local_user_refs(uid):
    raw = middleware.bucketGet("jd_code_user_refs", str(uid))
    try:
        return set(json.loads(str(raw)) if raw else [])
    except Exception:
        return set()


def bind_local_user_ref(uid, ref):
    if not uid or not ref:
        return
    raw = middleware.bucketGet("jd_code_user_refs", str(uid))
    try:
        arr = json.loads(str(raw)) if raw else []
        if not isinstance(arr, list):
            arr = []
    except Exception:
        arr = []
    ref = str(ref)
    if ref not in arr:
        arr.append(ref)
        middleware.bucketSet("jd_code_user_refs", str(uid), json.dumps(arr, ensure_ascii=False))


def _unbind_local_user_ref(uid, ref):
    if not uid or not ref:
        return
    raw = middleware.bucketGet("jd_code_user_refs", str(uid))
    try:
        arr = json.loads(str(raw)) if raw else []
    except Exception:
        arr = []
    ref = str(ref)
    if ref in arr:
        arr.remove(ref)
        middleware.bucketSet("jd_code_user_refs", str(uid), json.dumps(arr, ensure_ascii=False))


def _filter_accounts_for_user(accounts, uid, is_admin):
    if is_admin:
        return accounts
    refs = _get_local_user_refs(uid)
    return [a for a in accounts if str(a.get("id") or a.get("openid") or "") in refs]


def _refresh_one_code_account(config, s, uid, acc, is_admin=False):
    ref = str(acc.get("id") or acc.get("openid") or "")
    nick = acc.get("nickname") or "未知"

    yyb_pin = str(acc.get("pt_pin") or acc.get("pin") or "")
    local_pin = str(middleware.bucketGet("jd_code_wechat_pin_map", ref) or "")

    s.reply(f"🔍 正在检测账号【{nick}】状态...")

    if config.get("code_check_before_refresh"):
        try:
            is_valid = False
            valid_pin = ""
            for panel in load_ql_panels():
                if is_valid:
                    break
                ql = QingLongClient(panel)
                for env in ql.all_envs():
                    if env.get("name") != config.get("code_ql_var_name", "JD_COOKIE"):
                        continue
                    val = str(env.get("value", ""))
                    remark = str(env.get("remarks", ""))
                    m = re.search(r"pt_pin=([^;\s]+)", val)
                    if not m:
                        continue
                    raw_pin = m.group(1)
                    dec_pin = decode_pin(raw_pin)

                    match = False
                    if local_pin and local_pin in (raw_pin, dec_pin):
                        match = True
                    elif yyb_pin and yyb_pin in (raw_pin, dec_pin):
                        match = True
                    elif nick in (raw_pin, dec_pin) or (nick and nick in remark):
                        match = True

                    if match and check_ck_validity(
                        val,
                        proxy_api=config.get("proxy_api"),
                        proxy_scope=config.get("proxy_scope", "all"),
                    ):
                        is_valid = True
                        valid_pin = dec_pin
                        break

            if is_valid:
                if not is_admin and valid_pin:
                    # 普通用户续期时恢复绑定；管理员给别人续期不改变归属
                    try:
                        middleware.bucketSet("jd_code_wechat_pin_map", ref, valid_pin)
                    except Exception:
                        pass
                return True, f"{nick} -> 🟢 京东CK未过期，跳过续期", False
        except Exception as e:
            _log("CK前置检查异常:", friendly_err(e))

    app_id = config.get("code_jd_app_id", JD_APPID_DEFAULT)
    cookie, pin, err_log, err_code, jmp_url = _do_login_with_fallback(
        config, ref, app_id, acc.get("openid")
    )

    if not cookie and err_code == 128:
        s.reply(
            f"⏸️ 账号【{nick}】触发短信/语音验证\n"
            "请在京东App完成验证，等待约60秒后回复 ok 重试"
        )
        if jmp_url:
            s.reply(f"🔗 验证链接：{jmp_url}")
        inp = s.input(70000, 1, False)
        if inp:
            text = str(inp if not isinstance(inp, dict) else inp.get("text", "")).strip().lower()
            if text == "ok":
                s.reply("🔄 收到 ok，正在重新双通道续期...")
                cookie, pin, err_log, err_code, jmp_url = _do_login_with_fallback(
                    config, ref, app_id, acc.get("openid")
                )

    if not cookie:
        return False, f"{nick} -> 🔴 京东CK提取失败 ({err_log or '无底层日志'})", False

    try:
        middleware.bucketSet("jd_code_wechat_pin_map", ref, decode_pin(pin))
    except Exception:
        pass

    success, panels = commit_cookie_to_ql(
        s,
        uid,
        cookie,
        config.get("code_ql_var_name", "JD_COOKIE"),
        skip_bind=True,
        append_remark=nick,
    )

    if success:
        return True, f"{nick} -> 🟢 续期成功 ({', '.join(panels)})", False
    return False, f"{nick} -> 🔴 写入青龙失败", False


def run_code_auto_refresh(s, uid, config):
    if config.get("code_api_type") != "yyb":
        s.reply("❌ Code续期仅支持yyb模式")
        return

    interval = config.get("code_auto_refresh_interval", 21600)
    s.reply(
        f"🔄 Code自动续期托管已启动\n"
        f"⏱ 续期间隔：{interval} 秒\n"
        "💡 发送 q 终止托管"
    )

    round_num = 0
    while True:
        round_num += 1
        accounts = _get_user_bound_code_accounts(uid, config)
        try:
            is_admin = check_admin(s, config)
        except Exception:
            is_admin = False
        accounts = _filter_accounts_for_user(accounts, uid, is_admin)

        if not accounts:
            s.reply("⚠️ 暂无可续期账号，托管继续等待")
        else:
            succ = skip = fail = 0
            for acc in accounts:
                ok, msg, _ = _refresh_one_code_account(
                    config, s, uid, acc, is_admin=is_admin
                )
                s.reply(msg)
                if ok:
                    if "跳过续期" in msg:
                        skip += 1
                    else:
                        succ += 1
                else:
                    fail += 1
            s.reply(f"📊 第{round_num}轮完成：成功 {succ}，有效跳过 {skip}，失败 {fail}")

        waited = 0
        while waited < interval:
            chunk = min(300, interval - waited)
            try:
                inp = s.input(chunk * 1000, 1, False)
                if inp:
                    txt = str(inp if not isinstance(inp, dict) else inp.get("text", "")).strip()
                    if txt in QUIT_KEYWORDS:
                        s.reply(f"✅ 自动续期托管已终止，共完成 {round_num} 轮")
                        return
            except Exception:
                pass
            waited += chunk


def run_code_refresh_menu(s, uid, config):
    if config.get("code_api_type") != "yyb":
        s.reply("❌ Code续期仅支持yyb模式")
        return

    accounts = _get_user_bound_code_accounts(uid, config)
    is_admin = check_admin(s, config)
    accounts = _filter_accounts_for_user(accounts, uid, is_admin)

    if not accounts:
        s.reply("❌ 暂无可续期微信账号\n💡 请先完成【微信扫码登录】")
        return

    lines = ["╭━━━ 🔄 京东账号续期 ━━━╮"]
    for i, acc in enumerate(accounts, 1):
        status = acc.get("status", "unknown")
        nick = acc.get("nickname") or "未知"
        icon = "🟢" if status == "alive" else ("🔴" if status == "expired" else "🟡")
        lines.append(f"【{i}】{icon} {nick} ({status})")
    lines += [
        "━━━━━━━━━━━━━━━━━━━━",
        "【A】一键检测并续期全部账号",
        "(回复数字续期指定账号，q退出)",
    ]
    s.reply("\n".join(lines))

    inp = get_input(s, validator=lambda t: t.lower() == "a" or t.isdigit())
    if not inp:
        return

    if inp.lower() == "a":
        succ = skip = fail = 0
        for acc in accounts:
            ok, msg, _ = _refresh_one_code_account(config, s, uid, acc, is_admin=is_admin)
            s.reply(msg)
            if ok:
                if "跳过续期" in msg:
                    skip += 1
                else:
                    succ += 1
            else:
                fail += 1
        s.reply(f"📊 一键续期完成：成功 {succ}，有效跳过 {skip}，失败 {fail}")
        return

    idx = int(inp)
    if idx < 1 or idx > len(accounts):
        s.reply("❌ 选择无效")
        return

    ok, msg, _ = _refresh_one_code_account(
        config, s, uid, accounts[idx - 1], is_admin=is_admin
    )
    s.reply(msg)


# ===================== 微信扫码登录 =====================

def _send_qr(s, config, qr_data):
    session_id = qr_data.get("session_id")
    image_base64 = qr_data.get("image_base64")
    image_sent = False

    if image_base64:
        try:
            b64 = str(image_base64)
            if "," in b64:
                b64 = b64.split(",", 1)[1]
            image_bytes = base64.b64decode(b64)
            temp_dir = "/tmp" if os.path.exists("/tmp") else os.getcwd()
            temp_path = os.path.join(temp_dir, f"jd_code_qr_{session_id}.jpg")
            with open(temp_path, "wb") as f:
                f.write(image_bytes)
            try:
                s.reply(f"[CQ:image,file=file:///{temp_path}]")
                image_sent = True
            except Exception:
                pass
            if not image_sent:
                try:
                    s.reply({"type": "image", "path": temp_path})
                    image_sent = True
                except Exception:
                    pass
        except Exception as e:
            _log("二维码Base64处理失败:", friendly_err(e))

    if not image_sent:
        image_url = f"{config['code_url']}/qr/{urllib.parse.quote(str(session_id))}/image"
        try:
            s.reply(f"[CQ:image,file={image_url}]")
            image_sent = True
        except Exception:
            pass
        if not image_sent:
            s.reply(f"📱 二维码URL：{image_url}")


def run_code_qr_login(s, uid):
    config = get_config()

    if config.get("code_api_type") != "yyb":
        s.reply("❌ 当前登录功能需要 Code接口模式=yyb")
        return
    if not config.get("code_url"):
        s.reply("❌ 未配置 YYB Go 服务地址")
        return

    # 已绑定账号先给用户账号管理菜单
    local_refs = _get_local_user_refs(uid)
    if local_refs:
        all_accounts = _get_user_bound_code_accounts(uid, config)
        user_accounts = [
            a for a in all_accounts
            if str(a.get("id") or a.get("openid") or "") in local_refs
        ]

        if user_accounts:
            while True:
                lines = ["╭━━━ 📱 当前已绑定微信 ━━━╮"]
                for i, acc in enumerate(user_accounts, 1):
                    status = acc.get("status")
                    icon = "🟢" if status == "alive" else ("🔴" if status == "expired" else "🟡")
                    lines.append(
                        f"【{i}】{icon} {acc.get('nickname') or '未知'} ({status or 'unknown'})"
                    )
                lines += [
                    "━━━━━━━━━━━━━━━━━━━━",
                    "【A】🔄 一键续期全部账号",
                    "【0】➕ 新增微信扫码账号",
                    "(回复数字管理账号，q退出)",
                ]
                s.reply("\n".join(lines))

                inp = get_input(s, validator=lambda t: t.lower() == "a" or t.isdigit())
                if not inp:
                    return

                if inp.lower() == "a":
                    succ = skip = fail = 0
                    for acc in user_accounts:
                        ok, msg, expired = _refresh_one_code_account(
                            config, s, uid, acc, is_admin=False
                        )
                        s.reply(msg)
                        if ok:
                            if "跳过续期" in msg:
                                skip += 1
                            else:
                                succ += 1
                        else:
                            fail += 1
                        if expired:
                            _unbind_local_user_ref(
                                uid, str(acc.get("id") or acc.get("openid") or "")
                            )
                    s.reply(f"📊 一键续期完成：成功 {succ}，有效跳过 {skip}，失败 {fail}")
                    return

                choice = int(inp)
                if choice == 0:
                    break
                if not (1 <= choice <= len(user_accounts)):
                    s.reply("❌ 选择无效")
                    continue

                target = user_accounts[choice - 1]
                ref = str(target.get("id") or target.get("openid") or "")
                nick = target.get("nickname") or "未知"
                s.reply(
                    f"当前账号：{nick}\n"
                    "【1】🔄 手动续期\n"
                    "【2】🗑️ 解除绑定\n"
                    "【0】返回"
                )
                sub = get_input(s, validator=lambda t: t in ("0", "1", "2"))
                if not sub:
                    return
                if sub == "0":
                    continue
                if sub == "2":
                    _unbind_local_user_ref(uid, ref)
                    user_accounts.pop(choice - 1)
                    s.reply(f"✅ 已解除微信【{nick}】绑定")
                    if not user_accounts:
                        break
                    continue

                ok, msg, expired = _refresh_one_code_account(
                    config, s, uid, target, is_admin=False
                )
                s.reply(msg)
                if expired:
                    _unbind_local_user_ref(uid, ref)
                return

    s.reply("⏳ 正在创建YYB微信扫码会话...")

    qr_data = _code_create_qr(config)
    if not qr_data:
        s.reply(
            f"❌ 创建二维码失败\n"
            f"请检查 YYB Go 服务：{config['code_url']}/qr"
        )
        return

    session_id = qr_data.get("session_id")
    _send_qr(s, config, qr_data)

    s.reply("📱 请使用微信扫码并确认授权\n发送 q 可退出")

    start_time = time.time()
    last_status = ""
    account = None

    while time.time() - start_time < config["code_qr_timeout"]:
        try:
            inp = s.input(config["code_qr_poll_interval"] * 1000, 1, False)
            if inp:
                txt = str(inp if not isinstance(inp, dict) else inp.get("text", "")).strip()
                if txt in QUIT_KEYWORDS:
                    s.reply("✅ 已安全退出")
                    return
        except Exception:
            pass

        status = _code_poll_qr(config, session_id)

        if status != last_status:
            if status == "scanned":
                s.reply("✅ 已扫码，请在手机端确认授权")
            elif status in ("authorized", "confirmed"):
                account = _code_confirm_qr(config, session_id)
                break
            elif status == "expired":
                s.reply("❌ 二维码已过期，请重新发送【登录】")
                return
            last_status = status

    if not account:
        s.reply("⏰ 扫码超时或微信授权失败")
        return

    ref = str(account.get("id") or account.get("openid") or "")
    openid = account.get("openid") or ""
    nickname = account.get("nickname") or "未知"

    if not ref:
        s.reply("❌ YYB Go未返回账号ref")
        return

    bind_local_user_ref(uid, ref)
    s.reply(f"✅ 微信绑定成功：{nickname}\n⏳ 正在通过YYB Go获取京东Code...")

    cookie, pin, err_log, err_code, jmp = _do_login_with_fallback(
        config,
        ref,
        config.get("code_jd_app_id", JD_APPID_DEFAULT),
        openid,
    )

    if not cookie and err_code == 128:
        s.reply(
            "⏸️ 该账号需要短信/语音验证\n"
            "请在京东App完成验证，等待约60秒后回复 ok 重试"
        )
        if jmp:
            s.reply(f"🔗 验证链接：{jmp}")
        inp = s.input(70000, 1, False)
        if inp and str(inp if not isinstance(inp, dict) else inp.get("text", "")).strip().lower() == "ok":
            cookie, pin, err_log, err_code, jmp = _do_login_with_fallback(
                config, ref, config.get("code_jd_app_id", JD_APPID_DEFAULT), openid
            )

    if not cookie:
        s.reply(
            "❌ 京东微信登录失败\n"
            f"原因：{err_log or '未获取到Cookie'}"
        )
        return

    pin = decode_pin(pin)
    try:
        middleware.bucketSet("jd_code_wechat_pin_map", ref, pin)
    except Exception:
        pass

    s.reply(f"✅ 京东登录成功\n👤 账号：{pin}\n⏳ 正在写入青龙...")

    success, panels = commit_cookie_to_ql(
        s,
        uid,
        cookie,
        config.get("code_ql_var_name", "JD_COOKIE"),
        skip_bind=True,
        append_remark=nickname,
    )

    if success:
        s.reply(
            f"🎉 微信Code登录完成\n"
            f"👤 京东账号：{pin}\n"
            f"📦 已写入：{', '.join(panels)}"
        )
        notify_admin(config, f"用户 {uid} 通过微信Code登录：{pin}")
        if config.get("code_auto_refresh_on_login"):
            run_code_auto_refresh(s, uid, config)
    else:
        s.reply(f"⚠️ 登录成功，但青龙写入失败：{', '.join(panels) if panels else '无'}")


# ===================== 主入口 =====================

def main():
    if not sender:
        return

    try:
        msg = str(sender.getMessage() or "").strip()
    except Exception:
        msg = ""

    config = get_config()

    # 管理员专用：京东续期
    if msg == "京东续期":
        if not check_admin(sender, config):
            sender.reply("❌ 权限不足：仅管理员可执行该指令")
            return

        if config.get("code_api_type") != "yyb":
            sender.reply("❌ 京东续期仅支持 Code接口模式=yyb")
            return

        accounts = _get_user_bound_code_accounts(userid, config)
        accounts = _filter_accounts_for_user(accounts, userid, True)

        if not accounts:
            sender.reply("❌ 暂未绑定任何微信账号\n💡 请先发送【登录】完成微信扫码")
            return

        sender.reply(f"⏳ 管理员正在一键检测并续期 {len(accounts)} 个微信账号...")
        succ = skip = fail = 0

        for acc in accounts:
            ok, msg_reply, _ = _refresh_one_code_account(
                config, sender, userid, acc, is_admin=True
            )
            sender.reply(msg_reply)
            if ok:
                if "跳过续期" in msg_reply:
                    skip += 1
                else:
                    succ += 1
            else:
                fail += 1

        sender.reply(f"📊 批量续期完成：成功 {succ}，有效跳过 {skip}，失败 {fail}")
        return

    if msg not in ("登录", "登陆", "上车"):
        return

    if not check_platform_enabled(config, sender):
        sender.reply("❌ 当前平台未启用登录")
        return

    if not check_white_list(sender, config):
        sender.reply("❌ 当前群未开启登录功能")
        return

    if config.get("code_api_type") != "yyb":
        sender.reply(
            "❌ 当前插件仅保留YYB微信登录\n"
            "请将【Code接口模式】设置为 yyb"
        )
        return

    run_code_qr_login(sender, userid)


try:
    main()
except Exception as e:
    _log("插件执行异常:", friendly_err(e))
    try:
        if sender:
            sender.reply(f"❌ 京东微信登录插件异常：{friendly_err(e)}")
    except Exception:
        pass
