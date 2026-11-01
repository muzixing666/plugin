// [title: 网易云扫码登录]
// [language: javascript]
// [rule: ^网易云(登录|手机登录|Cookie登录|查询|删除)$]
// [platform: qq,qb,wx,gw,sb,wb,tg,tb,qx,xy,ip]
// [admin: false]
// [public: true]
// [disable: false]
// [version: 1.6.0]
// [author: muzixing666]
// [description: 支持网易云登录、账号资产与今日运行查询、删除青龙绑定。依赖 Node.js qrcode。]
// [param: {"required":true,"key":"netease_login.ql_config","bool":false,"name":"青龙连接","placeholder":"地址丨Client ID丨Client Secret","desc":"填写青龙开放平台应用信息，用中文竖线丨分隔；应用需有环境变量的查看、新增、修改、删除权限。"}]
// [param: {"required":false,"key":"netease_login.ncmm_url","bool":false,"name":"NCMM 地址","placeholder":"http://服务器:10239","desc":"羽化容器可访问的 NCMM Web 地址。"}]
// [param: {"required":false,"key":"netease_login.ncmm_password","bool":false,"name":"NCMM 管理密码","placeholder":"NCMM 管理密码","desc":"仅保存在羽化面板配置中，不要填写在插件源代码里。"}]
// [param: {"required":false,"key":"netease_login.ncmm_ql_path","bool":false,"name":"NCMM 青龙脚本目录","placeholder":"3899_ncmm_main/scripts","desc":"NCMM 的工作目录相对于青龙 scripts 的路径；青龙开放平台应用需要脚本及环境变量权限。"}]
'use strict';
const crypto = require('crypto');
const https = require('https');
const http = require('http');
const { URL, URLSearchParams } = require('url');
const middleware = require('middleware');
const MOD = BigInt('0x00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7');
const NAME = 'NETEASE_MUSIC_U';
function power(a, n, m) { let r = 1n; for (a %= m; n; n >>= 1n, a = a * a % m) if (n & 1n) r = r * a % m; return r; }
function encrypted(data) {
  const secret = crypto.randomBytes(16).toString('hex').slice(0, 16);
  function aes(value, key) { const c = crypto.createCipheriv('aes-128-cbc', key, '0102030405060708'); return c.update(value, 'utf8', 'base64') + c.final('base64'); }
  const reverse = Buffer.from(secret.split('').reverse().join('')).toString('hex');
  return { params: aes(aes(JSON.stringify(data), '0CoJUm6Qyw8W8jud'), secret), encSecKey: power(BigInt('0x' + reverse), 65537n, MOD).toString(16).padStart(256, '0') };
}
function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url); const body = options.body || ''; const headers = {...(options.headers || {})};
    if (body) headers['Content-Length'] = Buffer.byteLength(body);
    const req = (u.protocol === 'https:' ? https : http).request(u, { method: options.method || 'GET', headers, timeout: 15000 }, res => {
      let chunks = []; let size = 0;
      res.on('data', b => { size += b.length; if (size > 4 * 1024 * 1024) req.destroy(new Error('响应过大')); else chunks.push(b); });
      res.on('end', () => { try { const data = JSON.parse(Buffer.concat(chunks).toString()); if (res.statusCode !== 200) return reject(new Error('HTTP ' + res.statusCode)); resolve({data, cookies: res.headers['set-cookie'] || []}); } catch (_) { reject(new Error('服务返回异常')); } });
    });
    req.on('timeout', () => req.destroy(new Error('连接超时'))); req.on('error', reject); if (body) req.write(body); req.end();
  });
}
async function music(path, data, musicU = "") {
  const body = new URLSearchParams(encrypted(data)).toString();
  return request('https://music.163.com/weapi/' + path, {method:'POST', body, headers:{'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36','Referer':'https://music.163.com/','Origin':'https://music.163.com','Cookie':'os=pc; appver=2.10.6;' + (musicU ? ' MUSIC_U=' + musicU + ';' : '')}});
}
function checkQL(r, action) { if (!r || r.code !== 200) throw new Error('青龙' + action + '失败，请检查开放平台权限'); return r.data; }
function fields(env) { return String(env.remarks || '').split('丨'); }
function ownerFields(owner) { return ['绑定平台:' + encodeURIComponent(owner.platform), '绑定用户:' + encodeURIComponent(owner.user)]; }
function owns(env, owner) { const parts = fields(env); return ownerFields(owner).every(x => parts.includes(x)); }
function envUID(env) { const field = fields(env).find(x => /^网易云UID:[0-9]+$/.test(x)); return field ? field.slice(7) : ''; }
async function connectQL(config) {
  const p = config.split('丨').map(x => x.trim());
  if (p.length !== 3 || p.some(x => !x)) throw new Error('请先正确配置青龙连接：地址丨Client ID丨Client Secret');
  const base = p[0].replace(/\/+$/, ''); const u = new URL(base); if (!['http:', 'https:'].includes(u.protocol)) throw new Error('青龙地址格式不正确');
  const tokenUrl = new URL(base + '/open/auth/token'); tokenUrl.searchParams.set('client_id', p[1]); tokenUrl.searchParams.set('client_secret', p[2]);
  const auth = checkQL((await request(tokenUrl.toString())).data, '认证'); if (!auth || !auth.token) throw new Error('青龙认证未返回令牌');
  return {base, headers: {'Authorization':'Bearer ' + auth.token, 'Content-Type':'application/json'}};
}
async function listQL(ql) {
  const envs = checkQL((await request(ql.base + '/open/envs?searchValue=' + NAME, {headers:ql.headers})).data, '读取变量');
  if (!Array.isArray(envs)) throw new Error('青龙变量列表格式异常');
  return envs.filter(e => e.name === NAME);
}
async function qinglong(ql, value, uid, owner) {
  const matches = await listQL(ql); const marker = '网易云UID:' + uid;
  const same = matches.filter(e => fields(e).includes(marker));
  if (same.length > 1) throw new Error('青龙存在多条相同账号的变量，请管理员整理后重试');
  const record = {name:NAME, value}; let method = 'POST', payload = [record];
  if (same.length) {
    const old = same[0], parts = fields(old);
    const hasOwner = parts.some(x => x.startsWith('绑定平台:') || x.startsWith('绑定用户:'));
    if (hasOwner && !owns(old, owner)) throw new Error('该网易云账号已绑定其他用户，请联系管理员处理');
    const id = old.id || old._id; if (!id) throw new Error('青龙变量缺少 ID');
    record.id = id; record.remarks = hasOwner ? old.remarks : parts.filter(Boolean).concat(ownerFields(owner)).join('丨');
    method = 'PUT'; payload = record;
  } else record.remarks = [marker, ...ownerFields(owner)].join('丨');
  checkQL((await request(ql.base + '/open/envs', {method, headers:ql.headers, body:JSON.stringify(payload)})).data, '保存变量');
  return same.length ? '更新' : '新增';
}
async function accountMenu(sender, ql, owner, deleting) {
  const accounts = (await listQL(ql)).filter(e => owns(e, owner) && envUID(e) && (e.id || e._id));
  if (!accounts.length) { await sender.reply('你还没有绑定网易云账号。请私聊发送“网易云登录”。'); return; }
  const lines = accounts.map((e, i) => `${i + 1}. 网易云 UID：${envUID(e)}${Number(e.status) === 1 ? '（青龙变量已禁用）' : ''}`);
  await sender.reply('你绑定的网易云账号：\n' + lines.join('\n') + (deleting ? '\n回复序号选择要删除的账号，回复 q 取消（60 秒内有效）。' : ''));
  if (!deleting) return;
  const choice = String(await sender.listen(60000) || '').trim();
  if (!/^[1-9][0-9]*$/.test(choice) || Number(choice) > accounts.length) { await sender.reply('已取消删除。'); return; }
  const selected = accounts[Number(choice) - 1]; const selectedId = String(selected.id || selected._id); const uid = envUID(selected);
  await sender.reply('将删除网易云 UID：' + uid + ' 的青龙登录信息。回复“确认删除”继续，其他内容取消（60 秒内有效）。');
  if (String(await sender.listen(60000) || '').trim() !== '确认删除') { await sender.reply('已取消删除。'); return; }
  const current = (await listQL(ql)).filter(e => String(e.id || e._id || '') === selectedId && owns(e, owner) && envUID(e) === uid);
  if (current.length !== 1) throw new Error('账号信息已变化，未执行删除，请重新查询');
  checkQL((await request(ql.base + '/open/envs', {method:'DELETE', headers:ql.headers, body:JSON.stringify([selected.id || selected._id])})).data, '删除变量');
  await sender.reply('已删除网易云 UID：' + uid + ' 的青龙登录信息及绑定；如曾通过手机号登录，NCMM 中的账号和文件仍需由管理员处理。');
}
function dateCN(value) {
  const d = new Date(value); if (!Number.isFinite(d.getTime())) return '';
  return new Intl.DateTimeFormat('en-CA', {timeZone:'Asia/Shanghai', year:'numeric', month:'2-digit', day:'2-digit'}).format(d);
}
function dailyNCMM(runs, uid, now = Date.now()) {
  const today = dateCN(now), matched = [];
  for (const run of Array.isArray(runs) ? runs : []) {
    if (dateCN(run.triggeredAt || run.startedAt) !== today) continue;
    for (const item of Array.isArray(run.rewards) ? run.rewards : []) {
      if (item.uid != null && String(item.uid) === uid) matched.push({run, item});
    }
  }
  matched.sort((a,b) => new Date(a.run.triggeredAt || a.run.startedAt) - new Date(b.run.triggeredAt || b.run.startedAt));
  const out = {count:matched.length, statuses:[], yunbeiKnown:false, yunbei:0};
  for (const {run,item} of matched) {
    if (item.yunbeiKnown) { const n=Number(item.yunbei); if (Number.isFinite(n)) { out.yunbei = item.yunbeiCumulative ? n : out.yunbei+n; out.yunbeiKnown=true; } }
    for (const [known,fields] of [['growthKnown',['growthToday','growthTotal']],['effectiveKnown',['effectivePlays','effectiveTarget']],['signKnown',['signed']]]) {
      if (item[known]) { out[known]=true; for (const f of fields) out[f]=item[f]; }
    }
    if (run.jobName && run.status) out.statuses.push(String(run.jobName).replace(/[\r\n]/g,' ').slice(0,50) + '：' + ({success:'成功',failed:'失败',running:'运行中',queued:'排队中',stopped:'已停止'}[run.status] || String(run.status).replace(/[\r\n]/g,' ').slice(0,20)));
  }
  return out;
}
async function queryAccounts(sender, ql, owner) {
  const accounts = (await listQL(ql)).filter(e => owns(e, owner) && envUID(e));
  if (!accounts.length) { await sender.reply('你还没有绑定网易云账号。请私聊发送“网易云登录”。'); return; }
  let runs = null;
  try { const ncmm = await ncmmLogin(); const result = await request(ncmm.base + '/api/v1/runs', {headers:ncmm.headers}); if (Array.isArray(result.data)) runs = result.data; } catch (_) {}
  for (const e of accounts) {
    const uid=envUID(e), lines=['===== 网易云账号 =====', 'UID：' + uid];
    if (Number(e.status) === 1) lines.push('青龙变量：已禁用');
    const token=extractMusicU(e.value);
    if (!token) { await sender.reply(lines.concat('登录信息缺失，请重新登录。').join('\n')); continue; }
    let account;
    try { account = (await music('nuser/account/get', {}, token)).data; } catch (_) {}
    const actual=account && (account.account?.id || account.profile?.userId);
    if (!actual || String(actual)!==uid || account.code!==200) { await sender.reply(lines.concat('账号验证失败或账号不匹配，请重新登录。').join('\n')); continue; }
    if (account.profile?.nickname) lines.push('昵称：' + String(account.profile.nickname).replace(/[\r\n]/g,' ').slice(0,60));
    let info, level;
    try { info=(await music('v1/user/info',{},token)).data; } catch (_) {}
    try { level=(await music('user/level',{},token)).data; } catch (_) {}
    if (level?.code===200 && level.data?.level != null) lines.push('账号等级：Lv.' + level.data.level);
    if (info?.code===200) {
      if (info.userPoint?.balance != null) lines.push('云贝余额：' + info.userPoint.balance);
      if (typeof info.viptype==='number') lines.push('会员状态：' + (info.viptype>0 ? '会员' : '非会员'));
      if (typeof info.pcSign==='boolean' && typeof info.mobileSign==='boolean') lines.push('今日签到：电脑端' + (info.pcSign?'已签到':'未签到') + '，手机端' + (info.mobileSign?'已签到':'未签到'));
    } else lines.push('实时资产：暂时无法获取');
    lines.push('----- 今日 NCMM 运行记录 -----');
    if (!runs) lines.push('无法读取 NCMM 运行记录，请检查插件中的 NCMM 配置。');
    else {
      const daily=dailyNCMM(runs,uid);
      if (!daily.count) lines.push('暂无可按 UID 确认属于此账号的记录。');
      else {
        if (daily.yunbeiKnown) lines.push('今日获得云贝：' + daily.yunbei);
        if (daily.growthKnown) lines.push('成长值：今日 ' + (daily.growthToday ?? '未知') + '，累计 ' + (daily.growthTotal ?? '未知'));
        if (daily.effectiveKnown) lines.push('有效播放：' + (daily.effectivePlays ?? '未知') + ' / ' + (daily.effectiveTarget ?? '未知'));
        if (daily.signKnown) lines.push('任务记录签到：' + (daily.signed ? '已签到' : '未签到'));
        if (daily.statuses.length) lines.push('任务整体状态：' + daily.statuses.slice(-5).join('；'));
        lines.push('仅统计带本账号 UID 的记录；任务状态为整次运行状态。');
      }
    }
    await sender.reply(lines.join('\n'));
  }
}
function extractMusicU(input) {
  const text = String(input || '').trim();
  if (!text || /[\r\n]/.test(text) || text.length > 16000) return '';
  const match = /(?:^|;\s*)MUSIC_U=([^;\s]+)/i.exec(text);
  const value = match ? match[1] : (/^[^=;\s]+$/.test(text) ? text : '');
  return value && /^[\x21-\x7e]+$/.test(value) && !/[;,]/.test(value) && value.length <= 8192 ? value : '';
}
function cookieFromResponse(result) {
  const item = (result.cookies || []).find(c => /^MUSIC_U=/i.test(c));
  return item ? extractMusicU(item) : '';
}
async function saveLogin(sender, ql, owner, value) {
  if (!value) throw new Error('未取得有效的 MUSIC_U，青龙变量未修改');
  const account = await music('nuser/account/get', {}, value);
  const uid = account.data && account.data.account && account.data.account.id;
  if (account.data.code !== 200 || !uid) throw new Error('登录信息无效或已过期，青龙变量未修改');
  const action = await qinglong(ql, value, String(uid), owner);
  await sender.reply('网易云登录成功，已绑定当前用户并' + action + '青龙变量 NETEASE_MUSIC_U。');
}
async function privateInput(sender, prompt, timeout = 120000) {
  await sender.reply(prompt + '\n请在私聊中发送，回复 q 取消；机器人会尝试撤回你的消息。');
  const text = String(await sender.input(timeout, 1000, false) || '').trim();
  if (!text) { await sender.reply('等待输入超时，已退出。'); return ''; }
  if (/^(q|取消)$/i.test(text)) { await sender.reply('已退出登录。'); return ''; }
  return text;
}
async function cookieLogin(sender, ql, owner) {
  const input = await privateInput(sender, '请发送完整 Cookie 或 MUSIC_U 的值（2 分钟内有效）。');
  if (!input) return;
  const value = extractMusicU(input);
  if (!value) { await sender.reply('未找到有效的 MUSIC_U，请检查输入后重试。'); return; }
  await saveLogin(sender, ql, owner, value);
}
async function ncmmLogin() {
  const base = String(await middleware.bucketGet('netease_login', 'ncmm_url') || '').trim().replace(/\/+$/, '');
  const password = String(await middleware.bucketGet('netease_login', 'ncmm_password') || '');
  const path = String(await middleware.bucketGet('netease_login', 'ncmm_ql_path') || '').trim().replace(/^\/+|\/+$/g, '');
  if (!base || !password || !path || path.split('/').some(x => !x || x === '.' || x === '..') || path.includes('\\')) throw new Error('请联系管理员配置 NCMM 地址、密码和青龙脚本目录');
  const u = new URL(base); if (!['http:', 'https:'].includes(u.protocol)) throw new Error('NCMM 地址不正确');
  const login = await request(base + '/api/v1/auth/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({password})});
  const cookie = login.cookies.map(x => x.split(';')[0]).join('; '); const csrf = login.data && login.data.csrfToken;
  if (!cookie || !csrf) throw new Error('NCMM 登录失败，请管理员检查连接配置');
  return {base, path, headers:{'Content-Type':'application/json','Cookie':cookie,'X-NCMM-CSRF':csrf}};
}
async function ncmmPost(ncmm, endpoint, data) {
  return (await request(ncmm.base + endpoint, {method:'POST', headers:ncmm.headers, body:JSON.stringify(data)})).data;
}
async function phoneLogin(sender, ql, owner) {
  const ncmm = await ncmmLogin();
  const directory = ql.base + '/open/scripts?path=' + encodeURIComponent(ncmm.path);
  checkQL((await request(directory, {headers:ql.headers})).data, '读取 NCMM 目录');
  const phone = await privateInput(sender, '请输入中国大陆手机号（2 分钟内有效）。');
  if (!phone) return;
  if (!/^1[0-9]{10}$/.test(phone)) { await sender.reply('手机号格式不正确，请重新发送“网易云手机登录”。'); return; }
  const identity = crypto.createHash('sha256').update(JSON.stringify([owner.platform,owner.user,phone])).digest('hex').slice(0,24);
  const filename = 'yuhua_' + identity + '.json';
  await ncmmPost(ncmm, '/api/v1/accounts/phone/send-sms', {phone, ctcode:86, countrycode:86});
  const captcha = await privateInput(sender, '验证码已发送，请输入短信验证码（2 分钟内有效）。');
  if (!captcha) return;
  if (!/^[0-9]{4,8}$/.test(captcha)) { await sender.reply('验证码格式不正确，请重新发送“网易云手机登录”。'); return; }
  const result = await ncmmPost(ncmm, '/api/v1/accounts/phone/verify', {phone, captcha, ctcode:86, countrycode:86, nickname:'', filename, main:false});
  if (result.needNickname) throw new Error('该号码需要先在 NCMM 完成注册或设置昵称，未同步青龙');
  if (result.filename && result.filename !== filename) throw new Error('NCMM 返回的文件名不匹配，账号已保存但未同步青龙，请联系管理员');
  try {
    const url = ql.base + '/open/scripts/detail?file=' + encodeURIComponent(filename) + '&path=' + encodeURIComponent(ncmm.path);
    const raw = checkQL((await request(url, {headers:ql.headers})).data, '读取 NCMM 账号');
    const obj = typeof raw === 'string' ? JSON.parse(raw) : raw;
    const cookie = obj && obj['163.com'] && obj['163.com']['music.163.com;/;MUSIC_U'];
    const value = cookie && typeof cookie === 'object' ? cookie.Value : '';
    if (!value) throw new Error('账号文件中没有 MUSIC_U');
    await saveLogin(sender, ql, owner, extractMusicU(value));
  } catch (_) { throw new Error('NCMM 已保存账号，但未能同步青龙，请联系管理员检查脚本读取权限和目录'); }
}
async function main() {
  const sender = new middleware.Sender(middleware.getSenderID());
  const chat = String((await sender.getChatID()) || '').trim();
  if (chat && chat !== '0') { await sender.reply('请私聊机器人使用网易云账号管理功能。'); return; }
  const owner = {platform:String(await sender.getImtype() || '').trim(), user:String(await sender.getUserID() || '').trim()};
  if (!owner.platform || !owner.user) { await sender.reply('无法识别当前用户，请换用支持私聊的平台。'); return; }
  let command = String(await sender.getMessage() || '').trim();
  if (command === '网易云登录') {
    await sender.reply('请选择网易云登录方式：\n1. 扫码登录\n2. 手机号验证码登录\n3. Cookie 登录\n回复数字选择，发送 q 退出（60 秒内有效）。');
    const choice = String(await sender.listen(60000) || '').trim();
    if (!choice) { await sender.reply('选择超时，已退出。'); return; }
    if (/^(q|取消)$/i.test(choice)) { await sender.reply('已退出登录。'); return; }
    const commands = {'1':'网易云扫码登录', '2':'网易云手机登录', '3':'网易云Cookie登录'};
    if (!commands[choice]) { await sender.reply('选择无效，已退出。请重新发送“网易云登录”。'); return; }
    command = commands[choice];
  }
  const config = String((await middleware.bucketGet('netease_login', 'ql_config')) || '').trim();
  if (config.split('丨').length !== 3 || config.split('丨').some(x => !x.trim())) { await sender.reply('插件尚未配置青龙连接，请联系管理员。'); return; }
  try {
    const ql = await connectQL(config);
    if (command === '网易云查询') { await queryAccounts(sender, ql, owner); return; }
    if (command === '网易云删除') { await accountMenu(sender, ql, owner, true); return; }
    if (command === '网易云Cookie登录') { await cookieLogin(sender, ql, owner); return; }
    if (command === '网易云手机登录') { await phoneLogin(sender, ql, owner); return; }
    if (command !== '网易云扫码登录') return;
    let QRCode; try { QRCode = require('qrcode'); } catch (_) { await sender.reply('缺少 Node.js 依赖 qrcode，请在羽化面板依赖管理中安装后重试。'); return; }
    const created = await music('login/qrcode/unikey', {type:3}); const key = created.data && created.data.unikey;
    if (created.data.code !== 200 || !key) throw new Error('获取网易云登录二维码失败');
    const qr = await QRCode.toDataURL('https://music.163.com/login?codekey=' + encodeURIComponent(key));
    await sender.reply('请用网易云音乐 App 扫码并确认登录，等待时间最多 3 分钟；发送 q 退出。');
    await sender.replyImage('base64://' + qr.split(',')[1]);
    let scanned = false; const end = Date.now() + 180000;
    while (Date.now() < end) {
      const remaining = end - Date.now();
      if (remaining <= 0) break;
      const input = String(await sender.listen(Math.min(3000, remaining)) || '').trim();
      if (/^(q|取消)$/i.test(input)) { await sender.reply('已退出登录。'); return; }
      if (Date.now() >= end) break;
      const result = await music('login/qrcode/client/login', {key, type:3}); const code = result.data.code;
      if (code === 800) { await sender.reply('二维码已过期，请重新发送“网易云登录”。'); return; }
      if (code === 802 && !scanned) { scanned = true; await sender.reply('已扫码，请在网易云音乐 App 中确认。'); }
      if (code === 803) {
        await saveLogin(sender, ql, owner, cookieFromResponse(result)); return;
      }
      if (![801,802].includes(code)) throw new Error('网易云登录状态异常（' + String(code) + '）');
    }
    await sender.reply('等待扫码超时，请重新发送“网易云登录”。');
  } catch (e) { await sender.reply('网易云操作未完成：' + (e.message || '请求失败')); }
}
if (require.main === module) main().catch(() => {});

