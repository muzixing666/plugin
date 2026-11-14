# [title: 必应积分任务]
# [language: python]
# [rule: ^必应(登录|Cookie登录|账号登录|查询|积分|运行|删除)$]
# [cron: 20 8 * * *]
# [platform: qq,qb,wx,gw,sb,wb,tg,tb,qx,xy,ip]
# [admin: false]
# [public: true]
# [disable: false]
# [author: muzixing666]
# [version: 1.8.0-yh]
# [description: 自动完成积分任务，可兑换所在地区提供的礼品卡等。 教程：打开这个网址先注册 https://rewards.bing.com/welcome?rh=5aIZctyKXxw&ref=rafsrchae。Cookie 获取：电脑 Edge 或 Chrome 登录 https://rewards.bing.com/welcome?rh=5aIZctyKXxw&ref=rafsrchae并打开积分面板，按 F12 选择网络并刷新，点击 cn.bing.com 网页请求，在标头的请求标头中复制 Cookie 完整内容；私聊机器人发送必应登录后按提示发送 Cookie。或者通过手机可以获取cookie的浏览器登录获取 ]
# [param: {"required":false,"key":"bing_rewards.cookie","bool":false,"name":"必应 Cookie","placeholder":"必应登录 Cookie，多账号用换行分隔","desc":"保存在羽化面板，勿发送到聊天群或上传仓库。"}]
# [param: {"required":false,"key":"bing_rewards.search_times","bool":false,"name":"每日搜索目标","placeholder":"15","desc":"最多20次；按微软页面进度补足。"}]
# [param: {"required":false,"key":"bing_rewards.delay","bool":false,"name":"请求间隔","placeholder":"3-8","desc":"单位秒，例如 3-8。"}]
# [param: {"required":false,"key":"bing_rewards.wait_seconds","bool":false,"name":"积分到账等待","placeholder":"60","desc":"执行完成后等待积分到账的秒数。"}]
# [param: {"required":false,"key":"bing_rewards.offers","bool":false,"name":"执行每日精选","placeholder":"1 开启，0 关闭","desc":"默认开启。"}]
# [param: {"required":false,"key":"bing_rewards.checkin","bool":false,"name":"尝试签到","placeholder":"1 开启，0 关闭","desc":"网页签到不一定有效。"}]
# [param: {"required":false,"key":"bing_rewards.claim","bool":false,"name":"领取待领取积分","placeholder":"1 开启，0 关闭","desc":"默认开启。"}]
# [param: {"required":false,"key":"bing_rewards.proxy_mode","bool":false,"name":"代理模式","placeholder":"direct / fixed / pool / api","desc":"direct 直连；fixed 固定代理；pool 代理池；api 代理接口。留空默认直连。"}]
# [param: {"required":false,"key":"bing_rewards.proxy_fixed","bool":false,"name":"固定代理","placeholder":"http://地址:端口","desc":"仅 fixed 模式使用；支持用户名密码。"}]
# [param: {"required":false,"key":"bing_rewards.proxy_pool","bool":false,"name":"代理池","placeholder":"http://地址1:端口, http://地址2:端口","desc":"仅 pool 模式使用；多个代理用逗号或换行分隔。按账号稳定选择。"}]
# [param: {"required":false,"key":"bing_rewards.proxy_api","bool":false,"name":"代理 API 地址","placeholder":"https://代理商接口地址","desc":"仅 api 模式使用；接口返回 IP:端口 或包含代理地址的 JSON。每次执行获取一次。"}]



import json
import os
import re
import time
import random
import sys
_vendor = "/data/plugins/python_packages/bing_rewards_vendor"
if os.path.isdir(_vendor): sys.path.insert(0, _vendor)
import requests
from urllib.parse import unquote_plus

# ============== 配置 ============
BASE = "https://cn.bing.com"
REWARDS_PANEL = "https://cn.bing.com/rewards/panelflyout?channel=bingflyout&partnerId=BingRewards"
REWARDS_API = "https://rewards.bing.com/api/getuserinfo?type=1"
# v1.4.0：earn 页面（含全部 offer 列表 + 积分 + 连续打卡），dashboard 用于解析连续打卡
EARN_PANEL = "https://rewards.bing.com/earn"
DASHBOARD = "https://rewards.bing.com/dashboard"

PC_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0")
MOBILE_UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36")

# 正常人类搜索词库（分类随机，避免一言 API 的奇怪句子）
NORMAL_SEARCH_TERMS = [
    # ========= 生活日常 =======
    "今天天气", "天气预报", "附近美食推荐", "家常菜做法", "早餐吃什么",
    "晚餐食谱", "减肥餐", "快递查询", "火车票", "机票价格",
    "附近酒店", "超市营业时间", "药店", "医院挂号", "公交路线",
    "地铁线路", "打车优惠", "外卖优惠券", "家政服务", "搬家公司",
    "水电缴费", "燃气费查询", "物业费", "停车位", "洗车",
    "汽车保养", "违章查询", "驾照换证", "身份证办理", "社保查询",
    "公积金", "个税计算", "银行利率", "理财产品", "保险推荐",
    # ========= 科技数码 =======
    "最新手机推荐", "笔记本电脑排行", "科技新闻", "AI工具", "Python教程",
    "软件下载", "电脑技巧", "WiFi设置", "路由器推荐", "固态硬盘",
    "机械键盘", "鼠标推荐", "显示器推荐", "显卡排行", "CPU对比",
    "主板推荐", "电源推荐", "机箱推荐", "散热器", "耳机推荐",
    "音箱推荐", "智能手表", "手环推荐", "平板推荐", "电子书阅读器",
    "投影仪", "扫地机器人", "空气净化器", "加湿器", "电动牙刷",
    # ========= 娱乐休闲 =======
    "电影推荐", "电视剧排行", "音乐排行榜", "游戏攻略", "小说推荐",
    "旅游攻略", "景点推荐", "拍照技巧", "综艺推荐", "演唱会门票",
    "话剧演出", "展览推荐", "博物馆", "动物园", "游乐园",
    "滑雪场", "温泉", "民宿推荐", "露营装备", "钓鱼技巧",
    "宠物饲养", "花卉养殖", "手工DIY", "绘画教程", "书法入门",
    "吉他教程", "钢琴入门", "舞蹈教学", "健身计划", "瑜伽入门",
    # ========= 学习提升 =======
    "英语学习", "考研资料", "公务员考试", "在线课程", "学习方法",
    "知识问答", "读书笔记", "考证", "雅思", "托福",
    "四六级", "教师资格证", "会计证", "心理咨询师", "健康管理师",
    "编程入门", "数据分析", "设计教程", "办公软件技巧", "PPT模板",
    "Excel技巧", "Word教程", "简历模板", "面试技巧", "职场沟通",
    # ========= 购物消费 =======
    "淘宝热销", "京东比价", "优惠券", "打折", "性价比推荐",
    "商品评价", "品牌对比", "拼多多", "双十一", "618",
    "年货节", "双十二", "会员日", "秒杀", "团购",
    "海淘", "代购", "奢侈品", "二手交易", "闲鱼",
    "转转", "得物", "小红书种草", "什么值得买", "慢慢买",
    # ========= 热点资讯 =======
    "今日新闻", "热点事件", "热搜榜", "微博热搜", "知乎热榜",
    "抖音热点", "B站热门", "头条新闻", "澎湃新闻", "36氪",
    "虎嗅", "知乎日报", "少数派", "差评", "酷安",
    "IT之家", "快科技", "太平洋电脑网", "中关村在线", "汽车之家",
]

used_terms = set()


# ============== 工具 ============
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def log_title(msg):
    print(f"\n{msg}", flush=True)


def parse_cookie(s):
    c = {}
    for part in s.split(";"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            c[k.strip()] = v.strip()
    return c


def get_search_term():
    """生成正常人类搜索词，随机词库 + 随机修饰，去重"""
    for _ in range(30):
        base = random.choice(NORMAL_SEARCH_TERMS)
        modifier = random.choice(["", "", "", "", "2026", "最新", "推荐", "攻略",
                                   "大全", "哪个好", "怎么样", "2026年", "排行"])
        term = f"{base} {modifier}".strip() if modifier else base
        if term not in used_terms and 0 < len(term) <= 30:
            return term
    return f"{random.choice(NORMAL_SEARCH_TERMS)} {int(time.time()) % 1000}"


def make_session(cookie_str):
    session = requests.Session()
    session.trust_env = False
    proxy = os.getenv("BING_PROXY", "").strip()
    if proxy: session.proxies.update({"http": proxy, "https": proxy})
    for key, value in parse_cookie(cookie_str).items():
        session.cookies.set(key, value, domain=".bing.com", path="/")
    return session


def get_headers(ua, referer=None):
    h = {
        "User-Agent": ua,
        "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,"
                   "image/avif,image/webp,*/*;q=0.8"),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if referer:
        h["Referer"] = referer
    return h


def get_username(session):
    """从必应首页获取账号名称"""
    try:
        r = session.get("https://cn.bing.com/", headers=get_headers(PC_UA), timeout=10)
        m = re.search(r'id="id_n"[^>]*>([^<]+)<', r.text)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return None


# ============== 核心功能 ============
def do_search(session, term, ua=PC_UA):
    """执行一次搜索（必须带 form=QBRE 才会计入每日搜索积分）"""
    try:
        r = session.get(f"{BASE}/search", params={"q": term, "form": "QBRE"},
                        headers=get_headers(ua, f"{BASE}/"), timeout=15)
        return r.status_code == 200
    except Exception as e:
        log(f"  搜索异常: {e}")
        return False


def extract_daily_set_activities(html):
    """
    提取每日集活动（v1.4.1 重写）。
    2026-11 新页面结构：dailySetItems 数组里每个元素自带
      destination / isCompleted / offerId / points / hash
    老页面是 "destinationUrl"，两种都兼容。
    """
    activities = []
    if not html:
        return activities
    text = html.replace('\\"', '"')
    seen = set()

    # 新结构：按 offerId 定位，向前回溯取同一对象里的字段
    for m in re.finditer(r'"offerId"\s*:\s*"(Gamification_DailySet[^"]*)"', text):
        oid = m.group(1)
        if oid in seen:
            continue
        start = text.rfind('{"date"', max(0, m.start() - 2000), m.start())
        block = text[start if start > 0 else max(0, m.start() - 1500):m.end() + 300]
        dest = re.search(r'"destination"\s*:\s*"(https?://[^"]+)"', block)
        if not dest:
            continue
        done = re.search(r'"isCompleted"\s*:\s*(true|false)', block)
        pts = re.search(r'"points"\s*:\s*([0-9]+)', block)
        title = re.search(r'"title"\s*:\s*"([^"]*)"', block)
        hs = re.search(r'"hash"\s*:\s*"([0-9a-f]{40,64})"', block)
        seen.add(oid)
        activities.append({
            "hash": hs.group(1) if hs else "",
            "url": dest.group(1).replace("\\u0026", "&").replace("&amp;", "&").replace('\\"', '"'),
            "complete": bool(done and done.group(1) == "true"),
            "offer_id": oid,
            "points": int(pts.group(1)) if pts else 0,
            "title": title.group(1) if title else oid[-8:],
        })
    if activities:
        return activities

    # 老结构兜底：destinationUrl + rnoreward 关键字
    urls = re.findall(r'"destinationUrl"\s*:\s*"(https?://[^"]*bing\.com/search\?[^"]*)"', html)
    for url in urls:
        url = url.replace("\\u0026", "&").replace("&amp;", "&").replace("\\u0022", "%22")
        if any(k in url for k in ["rnoreward", "DailySet", "ML2X9E", "ML2X9F", "tgrew4", "ML2G76"]):
            if url not in seen:
                seen.add(url)
                activities.append({"url": url, "complete": False, "offer_id": "",
                                   "points": 0, "title": ""})
    return activities


def get_daily_set_status(html):
    """获取每日集完成状态，如 '1/3'（兼容新旧两种页面）"""
    text = (html or "").replace('\\"', '"')
    # 新页面：dailyset 卡片的 streak 模型（先定位 type=dailyset，避免抓到 edge/bingapp 的进度）
    m = re.search(r'"type"\s*:\s*"dailyset"[^}]*?"activitiesCompleted"\s*:\s*(\d+)[^}]*?"activitiesTotal"\s*:\s*(\d+)', text, re.S)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r'partner_dset_titleArg0"\s*:\s*"(\d+)"', html)
    m2 = re.search(r'partner_dset_titleArg1"\s*:\s*"(\d+)"', html)
    if m and m2:
        return int(m.group(1)), int(m2.group(1))
    # 备用：从文本匹配
    m = re.search(r'每日集\((\d+)/(\d+)\s*活动\)', html)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def get_daily_search_status(html):
    """获取每日搜索积分状态，返回 (已赚, 上限)

    v1.4.0：兼容微软调整每日上限、以及 earn/dashboard 页面的新字段写法。
    """
    if not html:
        return None, None
    # 1. 面板里用 pointProgress/pointProgressMax 表示进度，每日搜索上限是 15
    for m in re.finditer(r'"pointProgressMax"\s*:\s*15\s*,\s*"pointProgress"\s*:\s*(\d+)', html):
        return int(m.group(1)), 15
    for m in re.finditer(r'"pointProgress"\s*:\s*(\d+)\s*,\s*"pointProgressMax"\s*:\s*15', html):
        return int(m.group(1)), 15
    # 2. earn/dashboard 页面的写法（2026-11-08 抓包）：
    #    "pointsCounters":{"dailyOffer":7,"pc":{"max":15,"progress":15,"originalMax":15},...}
    text = html.replace('\\"', '"')
    m = re.search(r'"pc"\s*:\s*\{\s*"max"\s*:\s*(\d+)\s*,\s*"progress"\s*:\s*(\d+)', text)
    if m:
        return int(m.group(2)), int(m.group(1))
    # 3. 泛化兜底：任意上限顺序颠倒的写法
    for m in re.finditer(r'pointProgressMax\\?"\s*:\s*(\d+)\s*,\s*\\?"pointProgress\\?"\s*:\s*(\d+)', html):
        mx, cur = int(m.group(1)), int(m.group(2))
        if 0 < cur <= mx <= 60:
            return cur, mx
    return None, None


def extract_ig_iid(html):
    """从搜索页面 HTML 提取 IG 和 IID"""
    ig = ""
    iid = "SERP.5057"
    m = re.search(r'IG["\s:=]+([A-Fa-f0-9]{32})', html)
    if m:
        ig = m.group(1)
    m = re.search(r'IID["\s:=]+(SERP\.\d+)', html)
    if m:
        iid = m.group(1)
    return ig, iid


def extract_quiz_total(html):
    """从Quiz页面提取总题数"""
    for m in re.finditer(r'(\d+)\s*/\s*(\d+)', html):
        cur, tot = int(m.group(1)), int(m.group(2))
        if tot in (3, 5, 7, 10) and 1 <= cur <= tot:
            return tot
    return None


def get_quiz_panel_status(html, quiz_url):
    """从面板提取指定Quiz的完成状态，返回 (已完成布尔值, 总积分)"""
    q_match = re.search(r'[?&]q=([^&]+)', quiz_url)
    if not q_match:
        return None, None
    q_text = q_match.group(1)
    for m in re.finditer(r'destinationUrl"\s*:\s*"([^"]*)"', html, re.I):
        if q_text in m.group(1):
            start = max(0, m.start() - 2000)
            end = min(len(html), m.end() + 300)
            block = html[start:end]
            prog = re.search(r'"pointProgress"\s*:\s*(\d+)', block)
            pmax = re.search(r'"pointProgressMax"\s*:\s*(\d+)', block)
            if prog and pmax:
                return int(prog.group(1)) >= int(pmax.group(1)), int(pmax.group(1))
    return None, None


def report_activity(session, activity_url, page_html, ig, iid):
    """调用 reportActivity API 触发积分"""
    from urllib.parse import urlparse, parse_qs, urlencode
    parsed = urlparse(activity_url.replace("www.bing.com", "cn.bing.com"))
    params = parse_qs(parsed.query)
    report_params = {
        "IG": ig,
        "IID": iid,
        "q": params.get("q", [""])[0],
    }
    for k in ["form", "FORM", "OCID", "PUBL", "CREA", "filters"]:
        if k in params:
            report_params[k] = params[k][0]
    report_params["rnoreward"] = "1"
    report_params["ajaxreq"] = "1"

    report_url = "https://cn.bing.com/rewardsapp/reportActivity?" + urlencode(report_params)
    try:
        r = session.post(report_url, headers={
            "User-Agent": PC_UA,
            "Referer": activity_url.replace("www.bing.com", "cn.bing.com"),
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }, timeout=15)
        return r.status_code == 200
    except Exception:
        return False


# /earn 路由的 Next Router State Tree（与账号无关，路由结构固定）
EARN_ROUTER_TREE = "%5B%22%22%2C%7B%22children%22%3A%5B%22(nav)%22%2C%7B%22children%22%3A%5B%22earn%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%2C0%5D%7D%2Cnull%2Cnull%2C0%5D%7D%2Cnull%2Cnull%2C0%5D%7D%2Cnull%2Cnull%2C16%5D"


def report_offer_v2(session, page_html, offer_hash, offer_id, referer=None):
    """
    v1.4.1：走 Rewards 新版 Server Action 上报活动完成。
    真机抓包（2026-11-08）确认：
      POST https://rewards.bing.com/earn?section=streaks
      next-action: <REPORT_ACTION_ID>
      体: ["<offer 的 hash>",11,{"offerid":"<offerId>","isPromotional":"$undefined","timezoneOffset":"-480"}]
      回: 0:{...}\n1:true     ← 1:true 即成功
    比旧的 cn.bing.com/rewardsapp/reportActivity 稳定得多。
    """
    url = "https://rewards.bing.com/earn?section=streaks"
    body = json.dumps([offer_hash, 11, {
        "offerid": offer_id,
        "isPromotional": "$undefined",
        "timezoneOffset": "-480",
    }], ensure_ascii=False, separators=(",", ":"))
    h = _action_headers(page_html, referer or url, REPORT_ACTION_ID)
    h["next-router-state-tree"] = EARN_ROUTER_TREE
    try:
        r = session.post(url, headers=h, data=body, timeout=20)
        if r.status_code >= 400:
            return False
        return "1:true" in (r.text or "")
    except Exception:
        return False


def complete_daily_set(session, delay_min, delay_max):
    """完成每日集活动（v1.4.1：改走 earn 页面 + 新版 Server Action 上报）"""
    log_title("======== 每日集 ========")
    html = get_earn_page(session)
    if not html:
        try:
            r = session.get(REWARDS_PANEL, headers=get_headers(PC_UA), timeout=15)
            html = r.text if r.status_code == 200 else ""
        except Exception as e:
            log(f"  面板访问异常: {e}")
            return 0
    if not html:
        log("  面板访问失败")
        return 0

    done, total = get_daily_set_status(html)
    if done is not None:
        log(f" 当前进度: {done}/{total}")
        if done >= total:
            log(" ✅ 每日集已全部完成")
            return total

    activities = extract_daily_set_activities(html)
    log(f"  提取到 {len(activities)} 个活动")
    pending = [a for a in activities if not a["complete"]]
    log(f"  未完成: {len(pending)} 个")

    for i, act in enumerate(pending):
        url = act["url"]
        log(f"  活动[{i+1}]: {act['title'] or url[:50]} (+{act['points']}分)")
        # 1. 先访问活动页（拿到 IG/IID，也让微软记录浏览行为）
        page = ""
        try:
            r = session.get(url, headers=get_headers(PC_UA, "https://rewards.bing.com/earn"), timeout=20)
            if r.status_code == 200:
                page = r.text
            else:
                log(f"    页面 status={r.status_code}")
        except Exception as e:
            log(f"    页面异常: {e}")

        # 2. 新版上报（hash + offerId）
        ok = False
        h = act.get("hash", "")
        if h and act.get("offer_id"):
            ok = report_offer_v2(session, html, h, act["offer_id"], "https://rewards.bing.com/earn?section=streaks")
            log(f"    {'✅ 积分已触发' if ok else '❌ 新版上报失败'}")

        # 3. 旧版兜底
        if not ok and page:
            ig, iid = extract_ig_iid(page)
            if ig:
                ok = report_activity(session, url, page, ig, iid)
                log(f"    {'✅ 旧接口已触发' if ok else '❌ 旧接口失败'}")
        time.sleep(random.randint(delay_min, delay_max))

    # 复查
    html2 = get_earn_page(session)
    done2, total2 = get_daily_set_status(html2)
    if done2 is not None:
        log(f"  最终进度: {done2}/{total2}")
        return done2
    return done or 0


def extract_quiz_from_html(html):
    """从页面 HTML 提取 quiz 问题和选项，返回 (question, options, user_id)"""
    # 提取选项：支持单引号和双引号属性
    opt_pattern = (r'''class=["'][^"']*btq_opt[^"']*["'][\s\S]*?'''
                   r'''href=["']([^"']+)["'][\s\S]*?'''
                   r'''acf-button-standard__label["'][^>]*>([^<]+)</div>''')
    options = []
    for m in re.finditer(opt_pattern, html):
        href = m.group(1).replace("&amp;", "&")
        text = m.group(2).strip()
        q_match = re.search(r'[?&]q=([^&]+)', href)
        correct = unquote_plus(q_match[1]) if q_match else ""
        options.append({"text": text, "href": href, "correct": correct})

    if not options:
        return None, None, ""

    # 提取问题文本（btq_opts 之前的最后一段文本）
    question = ""
    q_match = re.search(r'([^<>]{10,200})</div>\s*</div>\s*<div class=["\']btq_opts', html)
    if q_match:
        question = q_match.group(1).strip()
    if not question:
        # 备用：找 btq_title 之后的文本
        q_match = re.search(r'btq_title["\'][^>]*>([\s\S]{0,300})', html)
        if q_match:
            t = re.sub(r'<[^>]+>', '', q_match.group(1)).strip()
            question = t[:100]

    # 提取 UserId
    uid_match = re.search(r'"UserId"\s*:\s*"([^"]+)"', html)
    user_id = uid_match.group(1) if uid_match else ""

    return question, options, user_id


def complete_quiz(session, quiz_url, delay_min, delay_max):
    """完成一个 Quiz 的所有题目（自动提取正确答案）"""
    quiz_url = quiz_url.replace("www.bing.com", "cn.bing.com")
    current_url = quiz_url
    completed = 0

    for round_num in range(10):  # 最多 10 题，防止死循环
        try:
            r = session.get(current_url, headers=get_headers(PC_UA), timeout=15)
            if r.status_code != 200:
                break

            question, options, user_id = extract_quiz_from_html(r.text)
            if not options:
                # 只有第一次访问就没题目时，才提示已完成
                if round_num == 0:
                    log_title("======= 每日问答 =======")
                    total_q = extract_quiz_total(r.text)
                    if total_q:
                        log(f" 当前进度: {total_q}/{total_q}")
                    log(" ✅ 每日问答已全部完成")
                return 0

            # 有题目，第一次输出标题
            if round_num == 0:
                log_title("======= 每日问答 =======")

            # 正确答案 = 所有选项的 q 参数（都一样）
            correct_answer = options[0]["correct"]
            # 找到显示文本匹配正确答案的选项
            correct_opt = None
            for opt in options:
                if correct_answer in opt["text"]:
                    correct_opt = opt
                    break
            if not correct_opt:
                # 兜底：选最后一个
                correct_opt = options[-1]

            log(f"  {round_num+1}. {question[:45]}")
            log(f"     正在查找正确答案→ {correct_opt['text']}")

            # 1. POST quiz/record 记录答案
            try:
                record_body = {
                    "PartnerId": "BingQAUX",
                    "QuestionText": question,
                    "OptionText": correct_opt["text"],
                    "UserId": user_id,
                }
                session.post("https://www.bing.com/funapi/api/quiz/record?ajaxreq=1",
                             json=record_body,
                             headers={
                                 "User-Agent": PC_UA,
                                 "Content-Type": "application/json",
                                 "Referer": current_url,
                                 "X-Requested-With": "XMLHttpRequest",
                             }, timeout=10)
            except Exception as e:
                log(f"    quiz/record 异常: {e}")

            # 2. 提取 IG/IID，调用 reportActivity 触发积分
            ig, iid = extract_ig_iid(r.text)
            opt_full_url = correct_opt["href"]
            if opt_full_url.startswith("/"):
                opt_full_url = "https://cn.bing.com" + opt_full_url
            report_activity(session, opt_full_url, r.text, ig, iid)

            completed += 1

            # 3. 访问正确选项链接，获取下一题
            current_url = opt_full_url
            time.sleep(random.randint(delay_min, delay_max))

        except Exception as e:
            log(f"  第{round_num+1}题异常: {e}")
            break

    if completed > 0:
        log(f"  🎉 全部答完（共 {completed} 题）")
    return completed


def extract_quiz_urls(html):
    """从 Rewards 面板提取所有 Quiz URL（排除每日集活动）"""
    urls = []
    for m in re.finditer(r'"destinationUrl"\s*:\s*"(https?://[^"]*bing\.com/search\?[^"]*)"', html, re.I):
        url = m.group(1).replace("\\u0026", "&")
        low = url.lower()
        # 只取 quiz / quote 类型，排除每日集（含 DailySet）
        if ("quiz" in low or "quote" in low) and "dailyset" not in low and "rnoreward" not in low:
            if url not in urls:
                urls.append(url)
    return urls


def check_points(session):
    """查询积分（容错，rewards.bing.com 不通时从 cn.bing.com 面板提取）"""
    # 方式1：rewards.bing.com API（国际版，国内服务器可能不通）
    try:
        r = session.get(REWARDS_API, timeout=8, headers={
            "Accept": "application/json",
            "Referer": "https://rewards.bing.com/",
            "User-Agent": PC_UA,
        })
        if r.status_code == 200:
            data = r.json()
            pts = data.get("dashboard", {}).get("userStatus", {}).get("availablePoints")
            if isinstance(pts, (int, float)) and not isinstance(pts, bool):
                return pts
    except Exception:
        pass
    # 方式2：从 cn.bing.com 面板 HTML 提取（国内服务器可通）
    try:
        r = session.get(REWARDS_PANEL, headers=get_headers(PC_UA), timeout=8)
        if r.status_code == 200:
            for pat in [r'"availablePoints"\s*:\s*(\d+)',
                        r'"Balance"\s*:\s*(\d+)']:
                m = re.search(pat, r.text)
                if m:
                    return int(m.group(1).replace(",", ""))
    except Exception:
        pass
    return None

# ============== 新增 v1.4.0：earn 页面（精选任务 / 签到 / 连续打卡） ==============
DEFAULT_POINTS_RE = re.compile(r'"availablePoints"\s*:\s*"?([0-9]{1,6})')
ESCAPED_Q = re.compile(r'\\\"')


def _unescape_html(html):
    """Rewards 页面里内嵌的 RSC 数据是双重转义的 JSON，统一还原成普通 JSON 文本

    注意：只替换「反斜杠+引号」这种转义序列，别动 \\u0022（那是 URL 里的 %22，
    一旦被还原会导致后面的正则处理出错）。
    """
    return html.replace('\\"', '"')


def _offer_points(block):
    """取 offer 积分；优先取 offerId 那一行的 points，避免被同级其它 offer 的积分串味"""
    head = block[:block.find('"offerId"') if '"offerId"' in block else len(block)]
    m = re.search(r'"points"\s*:\s*([0-9]{1,4})', head) or re.search(r'"points"\s*:\s*([0-9]{1,4})', block)
    return int(m.group(1)) if m else 0


def get_points_from_html(html):
    """从 earn/dashboard 页面取当前可用积分（真机页面字段名是 balance）"""
    if not html:
        return None
    text = _unescape_html(html)
    for pat in (r'"balance"\s*:\s*([0-9]+)', r'"availablePoints"\s*:\s*"?([0-9]+)'):
        m = re.search(pat, text)
        if m:
            return int(m.group(1))
    return None


def get_earn_page(session):
    """抓 earn 页面（提供全部 offer 列表 + 积分 + 连续打卡数据）"""
    try:
        r = session.get(EARN_PANEL, headers=get_headers(PC_UA, DASHBOARD), timeout=20)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        log(f"  earn 页面访问异常: {e}")
    return ""


def get_dashboard(session):
    """抓 dashboard 页面（连续打卡卡片数据最全）"""
    try:
        r = session.get(DASHBOARD, headers=get_headers(PC_UA, EARN_PANEL), timeout=20)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        log(f"  dashboard 访问异常: {e}")
    return ""


def _find_hash(block):
    """从 offer 片段里取 hash（新版 Server Action 上报要用）"""
    m = re.search(r'"hash"\s*:\s*"([0-9a-f]{40,64})"', block)
    return m.group(1) if m else ""


def extract_offers(html):
    """
    解析 earn 页 offer 列表。
    真实结构（2026-11-08 抓包）：
      {"destination":"...","imageUrl":"...","isCompleted":false,"name":"WW_..._BingOffer4",
       "points":5,"priority":1,"title":"晚餐创意","offerId":"WW_..._BingOffer4",...}
    注意字段顺序不固定，所以每个字段单独在片段里找，不依赖顺序。
    """
    offers = []
    if not html:
        return offers
    text = _unescape_html(html)
    seen = set()
    for m in re.finditer(r'"offerId"\s*:\s*"([^"]+)', text):
        oid = m.group(1)
        if oid in seen:
            continue
        seen.add(oid)
        start = text.rfind('{"', max(0, m.start() - 2500), m.start())
        if start < 0:
            start = max(0, m.start() - 2000)
        block = text[start:m.end() + 200]

        dest = re.search(r'"destination"\s*:\s*"(https?://[^"]+)"', block)
        title = re.search(r'"title"\s*:\s*"([^"]*)"', block)
        desc = re.search(r'"description"\s*:\s*"([^"]*)"', block)
        oc = re.search(r'"isCompleted"\s*:\s*(true|false)', block)
        lk = re.search(r'"isLocked"\s*:\s*(true|false)', block)
        offers.append({
            "id": oid,
            "dest": dest.group(1) if dest else "",
            "title": (title.group(1) if title else oid)[:24],
            "desc": desc.group(1) if desc else "",
            "points": _offer_points(block),
            "completed": (oc.group(1) == "true") if oc else False,
            "locked": (lk.group(1) == "true") if lk else False,
            "hash": _find_hash(block),
            "raw": block,
        })
    return offers


def extract_streaks(html):
    """解析 /dashboard 或 /earn 里的 streak 卡片（各产品连续打卡进度）"""
    streaks = []
    if not html:
        return streaks
    text = _unescape_html(html)
    for m in re.finditer(r'"type"\s*:\s*"streak"\s*,\s*"model"\s*:\s*\{"streak"\s*:\s*\{', text):
        block = text[m.end():m.end() + 1200]
        ac = re.search(r'"activitiesCompleted"\s*:\s*([0-9]+)', block)
        at = re.search(r'"activitiesTotal"\s*:\s*([0-9]+)', block)
        part = re.search(r'"partner"\s*:\s*"([^"]+)"', block)
        day = re.search(r'"currentDay"\s*:\s*([0-9]+)', block)
        td = re.search(r'"totalDays"\s*:\s*([0-9]+)', block)
        sys_ = {"partner": part.group(1) if part else "?", "done": 0, "total": 0,
                "day": 0, "total_days": 0}
        if ac:
            sys_["done"] = int(ac.group(1))
        if at:
            sys_["total"] = int(at.group(1))
        if day:
            sys_["day"] = int(day.group(1))
        if td:
            sys_["total_days"] = int(td.group(1))
        streaks.append(sys_)
    m = re.search(r'"streakCounter"\s*:\s*([0-9]+)', text)
    if m:
        streaks.append({"partner": "dailystreak", "done": int(m.group(1)), "total": 0,
                        "day": 0, "total_days": 0})
    return streaks


STREAK_LABELS = {
    "bing": "必应搜索", "dailyset": "每日集", "edge": "Edge 浏览 30 分钟",
    "bingapp": "必应App 签到", "dailystreak": "每日连续打卡总天数",
    "msn": "MSN 文章", "outlook": "Outlook", "visualsearch": "视觉搜索",
}


def show_streaks(html):
    """打印连续打卡进度"""
    log_title("======= 连续打卡 =======")
    shown = False
    for s in extract_streaks(html):
        part = s["partner"]
        if part == "dailystreak":
            log(f"  {STREAK_LABELS[part]}: {s['done']} 天")
            shown = True
            continue
        if s["total"] <= 0:
            continue
        day_info = f" 第{s['day']}/{s['total_days']}天" if s["total_days"] else ""
        flag = "✅" if s["done"] >= s["total"] else "·"
        log(f"  {flag} {STREAK_LABELS.get(part, part)}: {s['done']}/{s['total']}{day_info}")
        shown = True
    if not shown:
        log("  未获取到连续打卡数据")


def _streak_of(html, partner):
    for s in extract_streaks(html):
        if s["partner"] == partner:
            return s
    return None


def do_checkin(session):
    """
    每日签到尝试。
    真机抓包（2026-11-08）：签到靠 POST /earn?section=streaks 这个 Next.js Server Action 触发，
    签到结果体现在 streak 卡片的「签到: x/1」上。
    Server Action 需要页面里现生成的 action id（next-action 头），否则服务端直接拒绝，
    所以这里：先 GET 抓 action id → 带上它 POST → 复查 streak 卡片。
    """
    log_title("======= 每日签到 =======")
    html = get_dashboard(session) or get_earn_page(session)
    app = _streak_of(html, "bingapp")
    if app and app["total"] > 0 and app["done"] >= app["total"]:
        log(f" 当前进度: {app['done']}/{app['total']}")
        log(" ✅ 每日签到已完成")
        return True

    # 1. 抓 Server Action id
    action_id = None
    try:
        r = session.get("https://rewards.bing.com/earn?section=streaks",
                        headers=get_headers(PC_UA), timeout=20)
        m = re.search(r'"([0-9a-f]{40})"', r.text)
        if m:
            action_id = m.group(1)
    except Exception:
        pass

    # 2. 提交签到
    headers = get_headers(PC_UA, "https://rewards.bing.com/earn?section=streaks")
    headers.update({
        "Accept": "text/x-component",
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": "https://rewards.bing.com",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    })
    if action_id:
        headers["Next-Action"] = action_id
    try:
        r = session.post("https://rewards.bing.com/earn?section=streaks",
                         headers=headers, data="[]", timeout=15)
        log(f"  签到请求: HTTP {r.status_code}" + ("" if action_id else "（未取到 action id）"))
    except Exception as e:
        log(f"  签到请求异常: {e}")

    # 3. 复查
    time.sleep(2)
    html2 = get_dashboard(session) or get_earn_page(session)
    app2 = _streak_of(html2, "bingapp")
    if app2:
        log(f" 当前进度: {app2['done']}/{app2['total']}")
        if app2["total"] > 0 and app2["done"] >= app2["total"]:
            log(" ✅ 每日签到已完成")
            return True
    log(" ⚠️ 签到未生效（该签到需必应App端，网页接口通常无效）")
    return False


def complete_offers(session, earn_html, skip_ids, delay_min, delay_max, notes):
    """
    完成 earn 页的「每日精选任务」：
    每日箴言 / 某某的图片 / 旅行策划 这类每天固定 5 分的小任务，
    与每日集同机制（rnoreward=1 搜索页 + /rewardsapp/reportActivity）。
    """
    log_title("======= 每日精选任务 =======")
    offers = extract_offers(earn_html)
    if not offers:
        log("  未解析到任务列表（earn 页面异常）")
        notes.append("每日精选任务: 未解析到任务列表")
        return 0

    pending, done_cnt, locked_cnt = [], 0, 0
    for o in offers:
        if o["id"] in skip_ids or not re.search(r"bing\.com/search\?", o["dest"]):
            continue          # 每日集 / Quiz 已由前面处理
        if o["completed"]:
            done_cnt += 1
            continue
        if o["locked"]:
            locked_cnt += 1
            continue
        if o["points"] <= 0:
            continue
        pending.append(o)

    log(f"  共 {len(offers)} 个任务，已完成 {done_cnt} 个，待做 {len(pending)} 个，锁定 {locked_cnt} 个")

    ok_cnt = 0
    for i, o in enumerate(pending):
        url = o["dest"].replace("https://www.bing.com", "https://cn.bing.com")
        try:
            r = session.get(url, headers=get_headers(PC_UA, EARN_PANEL), timeout=15)
            page = r.text if r.status_code == 200 else ""
            ok = False
            # v1.4.1：优先走新版 Server Action（hash + offerId）
            if o.get("hash"):
                ok = report_offer_v2(session, earn_html, o["hash"], o["id"],
                                     "https://rewards.bing.com/earn?section=streaks")
            # 旧接口兜底
            if not ok and page:
                ig, iid = extract_ig_iid(page)
                if ig:
                    ok = report_activity(session, url, page, ig, iid)
            log(f"  任务[{i+1}/{len(pending)}] {o['title']} (+{o['points']}分): "
                f"{'✅ 已触发' if ok else '❌ 触发失败'}")
            if ok:
                ok_cnt += 1
                notes.append(f"精选任务「{o['title']}」已提交(+{o['points']})")
        except Exception as e:
            log(f"  任务[{i+1}/{len(pending)}] {o['title']} ❌ 异常: {e}")
        if i < len(pending) - 1:
            time.sleep(random.randint(delay_min, delay_max))
    return ok_cnt


SKIP_LABEL_KEYS = ("Edg", "Edge", "banner", "Sweeps", "RAF", "Duolingo", "Refer")


# ============== v1.4.0：领取积分（待领取 → 可用） ==============
# 领取按钮走 Next.js Server Action：POST /dashboard，头里带 Next-Action。
# 2026-11-08 从线上 JS chunk 里挖出来的稳定 action id（函数名 reportClaimAllPoints）。
CLAIM_ACTION_ID = "00491296f1d668ad46b65342c95cb9d72a62c1fa9d"
# 每日集/精选任务点击上报（reportActivity），备用
REPORT_ACTION_ID = "707e6eb15bdfdd5fba193f0a77e934f7018faf87ce"


def get_claimable(html):
    """解析「可领取」积分数（解析不到返回 None）

    真机页面结构（2026-11-08 抓包）：
      instrument.name = DashboardHeader_ClaimablePoints
      data = {"points":582,"hasPointClaimEntryExpiringSoon":true}
      没有待领取时 points 是 "$undefined"
    """
    if not html:
        return None
    text = _unescape_html(html)
    m = re.search(r'DashboardHeader_ClaimablePoints.{0,300}?"points"\s*:\s*"?(\d+|\$undefined)', text, re.S)
    if not m:
        return None
    v = m.group(1)
    return 0 if v == "$undefined" else int(v)


def _deployment_id(html):
    """从页面里取部署版本号（Server Action 要带 x-deployment-id，版本不符会被拒）"""
    m = re.search(r"dpl=(\d{8}-\d+)", html or "")
    return m.group(1) if m else None


def _action_headers(html, referer, action_id):
    h = get_headers(PC_UA, referer)
    h.update({
        "Accept": "text/x-component",
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": "https://rewards.bing.com",
        "Next-Action": action_id,
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    })
    dpl = _deployment_id(html)
    if dpl:
        h["x-deployment-id"] = dpl
    return h


def discover_action_id(session, page_html, func_name, max_chunks=40):
    """
    自动挖 Server Action id。
    action id 是构建产物的一部分，微软每次发版都会换，所以这里从线上 JS 里现挖：
      1. 页面里列出的 chunk 先扫一遍
      2. 没找到就顺着 chunk 里的 chunk 映射表继续找（领取面板是懒加载的独立 chunk）
    找到 createServerReference("<id>",...,"<func_name>") 就返回 id。
    """
    if not page_html:
        return None
    seen, todo, fetched = set(), [], 0
    for m in re.finditer(r"/_next/static/chunks/[^\"'\s]+\.js", page_html):
        if m.group(0) not in seen:
            seen.add(m.group(0))
            todo.append(m.group(0))

    pat = re.compile(r'createServerReference\)\("([0-9a-f]{40,44})"[^)]*?"' + re.escape(func_name) + r'"')
    checked = set()
    while todo and fetched < max_chunks:
        path = todo.pop(0)
        if path in checked:
            continue
        checked.add(path)
        try:
            r = session.get("https://rewards.bing.com" + path, headers=get_headers(PC_UA), timeout=20)
            if r.status_code != 200:
                continue
            fetched += 1
            text = r.text or ""
        except Exception:
            continue
        m = pat.search(text)
        if m:
            log(f"  已挖到 action id: {func_name} = {m.group(1)[:12]}...")
            return m.group(1)
        # 顺着 chunk 映射表继续找
        for mm in re.finditer(r'static/chunks/([^"\'\s]+\.js)', text):
            p2 = "/_next/static/chunks/" + mm.group(1)
            if p2 not in seen:
                seen.add(p2)
                todo.append(p2)
    return None


def claim_points(session):
    """
    领取积分：把「可领取」里的积分转成可用积分。
    流程：抓 dashboard → 解析可领取数 → POST Server Action → 复查归零。
    没有待领取积分时直接跳过，不浪费请求。
    """
    log_title("======= 领取积分 =======")
    html = get_dashboard(session)
    if not html:
        log("  无法获取 dashboard，跳过")
        return None
    before = get_claimable(html)
    if before is None:
        log("  未解析到「可领取」积分，跳过")
        return None
    if before <= 0:
        log("  当前可领取: 0")
        log(" ✅ 暂无待领取积分")
        return 0

    log(f"  当前可领取: {before} 分，开始领取...")
    headers = _action_headers(html, DASHBOARD, CLAIM_ACTION_ID)
    ok = False
    try:
        r = session.post(DASHBOARD, headers=headers, data="[]", timeout=20)
        if r.status_code >= 400:
            # action id 可能随版本失效 → 现挖一个再试
            log("  内置 action id 失效，尝试从线上 JS 重新提取...")
            aid = discover_action_id(session, html, "reportClaimAllPoints")
            if aid:
                r = session.post(DASHBOARD, headers=_action_headers(html, DASHBOARD, aid), data="[]", timeout=20)
        body = r.text or ""
        log(f"  领取请求: HTTP {r.status_code}")
        if "NEXT_REDIRECT" in body and "login" in body:
            log("  ⚠️ 登录态失效（被重定向到登录页），请更新 Cookie")
            return None
        if r.status_code in (200, 204):
            ok = True
    except Exception as e:
        log(f"  领取请求异常: {e}")
        return None

    # 复查：可领取是否归零
    time.sleep(2)
    after = get_claimable(get_dashboard(session))
    if after is not None and after < before:
        log(f" ✅ 领取成功: {before} → {after}（+{before - after} 分）")
        return before
    if after == 0:
        log(f" ✅ 领取成功: {before} → 0")
        return before
    if ok:
        log(f" ⚠️ 已发送领取请求，但复查仍显示可领取 {after} 分")
        log("   可能原因: 积分刚到账有延迟，稍后重跑本脚本即可")
    return before


def collect_pending(earn_html, search_progress, daily_set_done, quiz_pending, notes):
    """汇总今日未完成的任务"""
    items = []
    s_done, s_max = search_progress
    if s_done is not None and s_max and s_done < s_max:
        items.append(f"每日搜索 仅 {s_done}/{s_max} 分")
    if daily_set_done is False:
        items.append("每日集 未全部完成")
    for t in quiz_pending:
        items.append(f"问答「{t}」未完成")
    for o in extract_offers(earn_html):
        # 每日集活动单独统计（进度由 daily_set_done 反映），这里不重复列出
        if "Gamification_DailySet" in o["id"]:
            continue
        if o["completed"] or not re.search(r"bing\.com/search\?", o["dest"]):
            continue
        if any(k in o["dest"] for k in ("rewards.bing.com", "microsoft.com")):
            continue
        if o["locked"]:
            items.append(f"{o['title']}（等级不够，已锁定）")
        elif o["points"] > 0:
            items.append(f"{o['title']}(+{o['points']})")
    # 已提交的任务不再算「未完成」
    for n in notes:
        m = re.match(r"精选任务「(.+?)」已提交", n)
        if m:
            t = m.group(1)
            items = [it for it in items if not it.startswith(t + "(")]
    return items


def show_pending(items):
    """打印未完成任务汇总"""
    if not items:
        log_title("======= 今日任务汇总 =======")
        log(" 🎉 能自动做的任务已全部完成")
        return
    log_title("======= 今日未完成 =======")
    for it in items:
        log(f"  · {it}")


# ============== 主流程 ============
def run_rewards():
    print("必应积分助手，基于满天星 v1.4.1 适配羽化面板")
    cookie_str = os.getenv("by", "").strip()
    if not cookie_str:
        log("❌ 未设置环境变量 by")
        return

    # 支持多账号，用换行或 # 分隔
    cookies = [c.strip() for c in re.split(r'[\n#]', cookie_str) if c.strip()]
    total_accounts = len(cookies)

    delay_cfg = os.getenv("BING_DELAY", "3-8")
    try:
        d_min, d_max = map(int, delay_cfg.split("-"))
        if d_min > d_max:
            d_min, d_max = d_max, d_min
    except Exception:
        d_min, d_max = 3, 8

    # 每日搜索次数（国内版每天最多 15 点 = 5 次搜索有积分，可通过环境变量调整）
    try:
        search_times = int(os.getenv("BING_SEARCH_TIMES", "15"))
        search_times = max(1, min(search_times, 20))
    except Exception:
        search_times = 15

    # 最终积分查询前等待秒数（等积分延迟到账）
    try:
        wait_sec = int(os.getenv("BING_WAIT_SECONDS", "60"))
        wait_sec = max(0, min(wait_sec, 300))
    except Exception:
        wait_sec = 60

    # v1.4.0 新增开关
    do_offers = os.getenv("BING_OFFERS", "1").strip() not in ("0", "false", "False", "no")
    do_checkin_flag = os.getenv("BING_CHECKIN", "1").strip() not in ("0", "false", "False", "no")
    do_claim_flag = os.getenv("BING_CLAIM", "1").strip() not in ("0", "false", "False", "no")

    for acc_idx, cookie in enumerate(cookies, 1):
        session = make_session(cookie)
        used_terms = set()
        notes = []

        # 账号名称和积分（第一行不用时间戳，第一个账号带总共X账号前缀）
        username = get_username(session)
        earn_html = get_earn_page(session)
        pts = check_points(session)
        if pts is None and earn_html:
            pts = get_points_from_html(earn_html)
        if acc_idx == 1:
            line = f"总共{total_accounts}账号,第{acc_idx}个账号: {username}" if username else f"总共{total_accounts}账号,第{acc_idx}个账号:"
        else:
            line = f"第{acc_idx}个账号: {username}" if username else f"第{acc_idx}个账号:"
        if pts is not None:
            line += f"  💰 当前积分: {pts}"
        else:
            line += "  💰 积分查询失败"
        print(line)

        # 0. 每日签到 + 连续打卡（v1.4.0 新增，BING_CHECKIN=0 可关闭签到）
        if do_checkin_flag:
            do_checkin(session)
        dash_html = get_dashboard(session)
        if dash_html:
            show_streaks(dash_html)
        # 0.5 领取积分（v1.4.1 新增，BING_CLAIM=0 可关闭）
        if do_claim_flag:
            claim_points(session)

        # 1. 每日搜索（先检查是否已搜满，已满则显示进度并跳过；未满则只补差额）
        search_done = False
        s_earned, s_limit = None, None
        need_times = search_times
        try:
            r_panel = session.get(REWARDS_PANEL, headers=get_headers(PC_UA), timeout=15)
            s_earned, s_limit = get_daily_search_status(r_panel.text)
        except Exception:
            r_panel = None
        if s_earned is None and earn_html:
            s_earned, s_limit = get_daily_search_status(earn_html)
        if s_earned is not None and s_limit:
            # 每点积分约需 1 次搜索（国内版上限 15 点），按未完成积分补搜索次数
            remain_pts = max(0, s_limit - s_earned)
            need_times = min(search_times, max(0, remain_pts))
        if s_earned is not None and s_limit and s_earned >= s_limit:
            search_done = True

        if search_done:
            log_title("======= 每日搜索 =======")
            log(f" 当前进度: {s_earned}/{s_limit}")
            log(" ✅ 每日搜索已全部完成")
        else:
            if s_earned is not None and s_limit:
                log_title(f"===== 每日搜索（{s_earned}/{s_limit} 分，补 {need_times} 次） =====")
            else:
                log_title(f"===== 每日搜索（{need_times} 次） =====")
            ok_n = 0
            for i in range(need_times):
                term = get_search_term()
                used_terms.add(term)
                ok = do_search(session, term)
                ok_n += 1 if ok else 0
                log(f"  搜索[{i+1}/{need_times}] '{term[:25]}': {'✅' if ok else '❌'}")
                if i < need_times - 1:
                    time.sleep(random.randint(d_min, d_max))
            notes.append(f"每日搜索 补 {ok_n}/{need_times} 次")

        # 2. 每日集活动
        ds_done = complete_daily_set(session, d_min, d_max)

        # 3. 问答 Quiz（自动答题，已完成则显示进度并跳过）
        quiz_pending = []
        try:
            r = session.get(REWARDS_PANEL, headers=get_headers(PC_UA), timeout=15)
            quiz_urls = extract_quiz_urls(r.text)
            for qurl in quiz_urls:
                done, _ = get_quiz_panel_status(r.text, qurl)
                if done:
                    log_title("======= 每日问答 =======")
                    # 从Quiz页面提取总题数
                    total_q = None
                    try:
                        rq = session.get(qurl.replace("www.bing.com", "cn.bing.com"),
                                         headers=get_headers(PC_UA), timeout=10)
                        total_q = extract_quiz_total(rq.text)
                    except Exception:
                        pass
                    if total_q:
                        log(f" 当前进度: {total_q}/{total_q}")
                    log(" ✅ 每日问答已全部完成")
                    continue
                complete_quiz(session, qurl, d_min, d_max)
                time.sleep(random.randint(d_min, d_max))
        except Exception:
            pass

        # 4. 每日精选任务（每日箴言 / 图片搜索等，v1.4.0 新增）
        skip_ids = set()
        earn_html2 = get_earn_page(session)
        if earn_html2:
            earn_html = earn_html2
        if do_offers:
            # 每日集活动 ID 不再重复处理
            for o in extract_offers(earn_html):
                if re.search(r"rnoreward=1|Gamification_DailySet", o["raw"]) and "search?" in o["dest"]:
                    skip_ids.add(o["id"])
            complete_offers(session, earn_html, skip_ids, d_min, d_max, notes)

        # 等积分延迟到账后再统计
        if wait_sec > 0:
            log(f"⏳ 等待 {wait_sec} 秒让积分到账...")
            time.sleep(wait_sec)

        # 7. 未完成任务汇总（v1.4.0 新增）：用等待后重新抓的页面，状态最准
        earn_html3 = get_earn_page(session) or earn_html
        sp = get_daily_search_status(earn_html3)
        if sp[0] is None and s_earned is not None:
            sp = (min(s_limit, s_earned + need_times) if s_limit else s_earned, s_limit)
        pending = collect_pending(earn_html3, sp, None if ds_done else False, quiz_pending, notes)

        # 最终积分（不带时间戳）
        pts2 = check_points(session)
        if pts2 is None:
            pts2 = get_points_from_html(earn_html3)
        show_pending(pending)
        if pts is not None and pts2 is not None:
            print(f"任务执行结束，积分: {pts} → {pts2} (+{pts2 - pts})")
        elif pts2 is not None:
            print(f"任务执行结束，当前积分: {pts2}")
        else:
            print("任务执行结束（积分查询不可用）")

        # 账号之间加空行分隔
        if acc_idx < total_accounts:
            print()




# === 脚本来自于 http://ql.xmox.cn 脚本库 ===




def normalize_proxy(value):
    from urllib.parse import urlsplit
    value = str(value or '').strip()
    if not value: raise ValueError('代理为空')
    if '://' not in value: value = 'http://' + value
    try:
        u = urlsplit(value)
        if u.scheme not in ('http', 'https') or not u.hostname or not u.port or u.path not in ('', '/') or u.query or u.fragment:
            raise ValueError('代理格式错误')
    except ValueError:
        raise ValueError('代理格式错误')
    return value.rstrip('/')

def parse_proxy_response(value):
    if isinstance(value, str):
        value = value.strip()
        if not value: raise ValueError('代理 API 返回空内容')
        try: return parse_proxy_response(json.loads(value))
        except json.JSONDecodeError: return normalize_proxy(value.splitlines()[0].strip())
    if isinstance(value, list):
        if not value: raise ValueError('代理 API 返回空列表')
        return parse_proxy_response(value[0])
    if isinstance(value, dict):
        if value.get('ip') and value.get('port'):
            return normalize_proxy(str(value['ip']) + ':' + str(value['port']))
        for key in ('proxy', 'address', 'server', 'data', 'result', 'list', 'proxies', 'proxy_list', 'ip_list'):
            if key in value: return parse_proxy_response(value[key])
    raise ValueError('无法识别代理 API 返回内容')

def choose_proxy(mode, fixed, pool, api, account_key):
    import hashlib
    from urllib.parse import urlsplit
    mode = str(mode or 'direct').strip().lower()
    if mode in ('', 'direct', 'off', '0'): return ''
    if mode == 'fixed': return normalize_proxy(fixed)
    if mode == 'pool':
        items = [normalize_proxy(x) for x in re.split(r'[,\n\r]+', str(pool or '')) if x.strip()]
        if not items: raise ValueError('代理池为空')
        index = int(hashlib.sha256(str(account_key).encode()).hexdigest(), 16) % len(items)
        return items[index]
    if mode == 'api':
        url = str(api or '').strip()
        u = urlsplit(url)
        if u.scheme not in ('http', 'https') or not u.hostname: raise ValueError('代理 API 地址无效')
        client = requests.Session()
        client.trust_env = False
        try:
            response = client.get(url, timeout=15, allow_redirects=False, stream=True)
            response.raise_for_status()
            data = response.raw.read(65537)
            if len(data) > 65536: raise ValueError('代理 API 返回过大')
            return parse_proxy_response(data.decode('utf-8-sig'))
        finally:
            client.close()
    raise ValueError('代理模式无效')

def panel_main():
    import contextlib
    import io
    import hashlib
    import sys
    from urllib.parse import urlsplit
    from autman import middleware

    sender = middleware.Sender(middleware.getSenderID())
    msg = str(sender.getMessage() or '').strip()
    commands = ('必应登录', '必应Cookie登录', '必应账号登录', '必应查询', '必应积分', '必应运行', '必应删除')
    interactive = msg in commands
    owner = ''
    if interactive:
        chat = str(sender.getChatID() or '').strip()
        if chat and chat != '0':
            sender.reply('请私聊机器人管理必应账号。')
            return
        platform = str(sender.getImtype() or '').strip()
        user = str(sender.getUserID() or '').strip()
        if not platform or not user:
            sender.reply('无法识别用户，请使用支持私聊的平台。')
            return
        owner = hashlib.sha256((platform + '\x00' + user).encode()).hexdigest()

    bucket = 'bing_rewards_accounts'
    def load(key):
        try:
            obj = json.loads(str(middleware.bucketGet(bucket, key) or '{}'))
            return obj if isinstance(obj, dict) else {}
        except (ValueError, TypeError):
            return {}
    def save(key, value):
        return middleware.bucketSet(bucket, key, json.dumps(value, ensure_ascii=False))
    def set_proxy(key):
        # 管理员配置的代理失败时停止该账号，避免悄悄切换为直连。
        os.environ.pop('BING_PROXY', None)
        value = choose_proxy(middleware.bucketGet('bing_rewards', 'proxy_mode'),
                             middleware.bucketGet('bing_rewards', 'proxy_fixed'),
                             middleware.bucketGet('bing_rewards', 'proxy_pool'),
                             middleware.bucketGet('bing_rewards', 'proxy_api'), key)
        if value: os.environ['BING_PROXY'] = value
        return value
    def receive(timeout=120000):
        return str(sender.input(timeout, 1000, False) or '').strip()
    def reply(text):
        if interactive: sender.reply(text)
        else: print(text)
    if msg in ('必应登录', '必应Cookie登录'):
        sender.reply('请私聊发送 cn.bing.com 登录后的完整 Cookie；发送 q 取消。输入消息将尝试撤回。')
        value = receive()
        if not value or value.lower() in ('q', '取消'):
            sender.reply('已取消或等待超时。'); return
        if len(value) > 20000 or not parse_cookie(value):
            sender.reply('Cookie 格式无效，请重新发送“必应登录”。'); return
        record = load(owner)
        try: set_proxy(owner)
        except Exception:
            sender.reply('代理配置不可用，请联系管理员检查。'); return
        score = check_points(make_session(value))
        if score is None:
            sender.reply('未能验证 Cookie，请确认账号已开通积分并检查代理与网络；原账号未更改。'); return
        record.update({'cookie': value, 'platform': platform, 'user': user})
        if not save(owner, record):
            sender.reply('保存失败，请联系管理员检查面板存储。'); return
        sender.reply('登录成功，当前积分：%s。' % score); return
    if msg == '必应账号登录':
        sender.reply('微软账号密码登录可能需要验证码或多重验证，目前请先在微软官方页面登录，再发送“必应Cookie登录”。请勿在聊天中发送密码。'); return
    if msg == '必应删除':
        sender.reply('回复“确认删除”删除你的必应账号；回复其他内容取消。')
        if receive(60000) != '确认删除':
            sender.reply('已取消删除。'); return
        ok = middleware.bucketDel(bucket, owner)
        middleware.bucketDel('bing_rewards_results', owner)
        sender.reply('已删除。' if ok else '删除失败，请联系管理员。'); return
    if msg in ('必应查询', '必应积分'):
        record = load(owner)
        if not record.get('cookie'):
            sender.reply('你还没有绑定账号，请发送“必应登录”。'); return
        try: set_proxy(owner)
        except Exception:
            sender.reply('代理配置不可用，请联系管理员检查。'); return
        score = check_points(make_session(record['cookie']))
        sender.reply('Cookie 验证通过，当前积分：%s' % score if score is not None else '无法验证 Cookie，可能是登录失效、代理或网络问题；请检查后重试。'); return

    config = {'BING_SEARCH_TIMES': middleware.bucketGet('bing_rewards', 'search_times'),
              'BING_DELAY': middleware.bucketGet('bing_rewards', 'delay'),
              'BING_WAIT_SECONDS': middleware.bucketGet('bing_rewards', 'wait_seconds'),
              'BING_OFFERS': middleware.bucketGet('bing_rewards', 'offers'),
              'BING_CHECKIN': middleware.bucketGet('bing_rewards', 'checkin'),
              'BING_CLAIM': middleware.bucketGet('bing_rewards', 'claim')}
    for key, value in config.items():
        if value is not None and str(value).strip(): os.environ[key] = str(value).strip()
        else: os.environ.pop(key, None)
    class Capture:
        def __init__(self, secrets): self.buffer = io.StringIO(); self.secrets = secrets
        def write(self, text):
            for secret in self.secrets:
                if secret: text = text.replace(secret, "[已隐藏]")
            self.buffer.write(text); sys.__stdout__.write(text); return len(text)
        def flush(self): sys.__stdout__.flush()
    def execute(key, record):
        cookie = record.get('cookie') or ''
        if not cookie: return False
        try: proxy = set_proxy(key)
        except Exception:
            print('代理配置不可用，本账号未执行。')
            return False
        cookies = [item.strip() for item in re.split(r'[\n#]', cookie) if item.strip()]
        valid = []
        checks = []
        for index, item in enumerate(cookies, 1):
            score = check_points(make_session(item))
            checks.append({'account': index, 'status': 'valid' if score is not None else 'unconfirmed'})
            if score is not None: valid.append(item)
            else: print('账号%s的 Cookie 无法验证，请检查登录状态、代理与网络，已跳过。' % index)
        check_saved = middleware.bucketSet('bing_rewards_results', key + ':cookie_check', json.dumps({
            'time': time.strftime('%Y-%m-%d %H:%M:%S'), 'accounts': checks
        }, ensure_ascii=False))
        if not check_saved: print('Cookie 检测结果保存失败。')
        if not valid: return False
        os.environ['by'] = '\n'.join(valid)
        capture, error = Capture([cookie, proxy] + cookies), ''
        try:
            with contextlib.redirect_stdout(capture): run_rewards()
        except Exception as exc:
            error = type(exc).__name__
        result = {'time': time.strftime('%Y-%m-%d %H:%M:%S'), 'output': capture.buffer.getvalue()[-30000:], 'error': error}
        saved = middleware.bucketSet('bing_rewards_results', key, json.dumps(result, ensure_ascii=False))
        return not error and bool(saved)
    if msg == '必应运行':
        record = load(owner)
        if not record.get('cookie'):
            sender.reply('你还没有绑定账号，请发送“必应登录”。'); return
        sender.reply('开始执行，请稍候。')
        ok = execute(owner, record)
        sender.reply('执行结束，积分到账请以微软页面为准。' if ok else '任务未执行或记录保存失败；请检查 Cookie、代理和网络，或联系管理员查看日志。')
        return
    # 定时任务逐个处理社媒用户；保留原有管理员面板 Cookie 的兼容性。
    keys = list(middleware.bucketAllKeys(bucket))
    seen = set()
    for key in keys:
        record = load(str(key))
        cookie = record.get('cookie') or ''
        digest = hashlib.sha256(cookie.encode()).hexdigest() if cookie else ''
        if digest and digest not in seen:
            seen.add(digest)
            execute(str(key), record)
    legacy = str(middleware.bucketGet('bing_rewards', 'cookie') or '').strip()
    if legacy and hashlib.sha256(legacy.encode()).hexdigest() not in seen:
        execute('legacy', {'cookie': legacy})
    print('必应积分定时任务结束。')

if __name__ == '__main__': panel_main()
