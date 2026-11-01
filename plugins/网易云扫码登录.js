// [icon: https://cdn.jsdelivr.net/gh/muzixing666/plugin@main/icons/netease.svg]
// [title: 网易云扫码登录]
// [language: javascript]
// [rule: ^网易云(登录|手机登录|Cookie登录|查询|删除)$]
// [platform: qq,qb,wx,gw,sb,wb,tg,tb,qx,xy,ip]
// [admin: false]
// [public: true]
// [disable: false]
// [version: 1.8.1]
// [author: muzixing666]
// [description: 支持网易云登录、官方账号资产及任务状态查询、删除青龙绑定。依赖 Node.js qrcode。]
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
function todayCN() { return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date()); }
function dayOfTimestamp(value) {
  const d=new Date(value); if(!Number.isFinite(d.getTime())) return '';
  return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(d);
}
function summarizeToday(records, hasMore, dateOf, amountOf) {
  if(!Array.isArray(records) || typeof hasMore!=='boolean') return null;
  const today=todayCN(); let sum=0, previous='', ordered=true, older=false, valid=true;
  for(const item of records) {
    const day=dateOf(item); if(!/^\d{4}-\d{2}-\d{2}$/.test(day)) {valid=false;continue;}
    if(previous && day>previous) ordered=false; previous=day;
    if(day<today) older=true;
    if(day===today) {const n=amountOf(item); if(typeof n==='number' && Number.isFinite(n)) sum+=n; else valid=false;}
  }
  return {sum,complete:valid && (!hasMore || (older && ordered))};
}
async function yunbeiReceipts(token) {
  const body=new URLSearchParams(encrypted({limit:100,offset:0})).toString();
  return (await request('https://music.163.com/store/api/point/receipt',{method:'POST',body,headers:{'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36','Referer':'https://music.163.com/','Cookie':'os=pc; appver=2.10.6; MUSIC_U='+token+';'}})).data;
}
async function queryAccounts(sender, ql, owner) {
  const accounts=(await listQL(ql)).filter(e=>owns(e,owner) && envUID(e));
  if(!accounts.length) {await sender.reply('你还没有绑定网易云账号。请私聊发送“网易云登录”。');return;}
  for(const e of accounts) {
    const uid=envUID(e), lines=['===== 网易云账号 =====','UID：'+uid];
    if(Number(e.status)===1) lines.push('青龙变量：已禁用');
    const token=extractMusicU(e.value);
    if(!token) {await sender.reply(lines.concat('登录信息缺失，请重新登录。').join('\n'));continue;}
    let account;try{account=(await music('nuser/account/get',{},token)).data;}catch(_){}
    const actual=account && (account.account?.id || account.profile?.userId);
    if(!actual || String(actual)!==uid || account.code!==200) {await sender.reply(lines.concat('账号验证失败或账号不匹配，请重新登录。').join('\n'));continue;}
    if(account.profile?.nickname) lines.push('昵称：'+String(account.profile.nickname).replace(/[\r\n]/g,' ').slice(0,60));
    const requests=[()=>music('v1/user/info',{},token).then(r=>r.data),()=>music('user/level',{},token).then(r=>r.data),()=>music('point/today/get',{},token).then(r=>r.data),()=>music('usertool/task/todo/query',{},token).then(r=>r.data),()=>music('vipnewcenter/app/level/task/newlist',{},token).then(r=>r.data),()=>music('vipnewcenter/app/level/growth/details',{limit:100,offset:0},token).then(r=>r.data),()=>music('nmusician/workbench/musician/role/get',{},token).then(r=>r.data),()=>yunbeiReceipts(token)];
    const settled=await Promise.allSettled(requests.map(f=>f()));
    const data=settled.map(r=>r.status==='fulfilled' && r.value?.code===200?r.value:null);
    const [info,level,today,tasks,vip,growth,role,receipt]=data;
    if(level?.data?.level!=null) lines.push('账号等级：Lv.'+level.data.level);
    if(info?.userPoint?.balance!=null) lines.push('云贝余额：'+info.userPoint.balance);
    if(typeof info?.viptype==='number') lines.push('会员状态：'+(info.viptype>0?'会员':'非会员'));
    lines.push('----- 今日数据 -----');
    if(typeof info?.pcSign==='boolean' && typeof info?.mobileSign==='boolean') lines.push('签到：电脑端'+(info.pcSign?'已签到':'未签到')+'，手机端'+(info.mobileSign?'已签到':'未签到'));
    if(typeof today?.data?.shells==='number') lines.push('今日签到所得云贝：'+today.data.shells);
    const income=receipt?summarizeToday(receipt.data,receipt.hasmore,x=>String(x.date || '').slice(0,10),x=>x.pointCost):null;
    if(income) lines.push('今日增加云贝：'+(income.complete?'':'至少 ')+income.sum+(income.complete?'':'（记录未完整）')); else lines.push('今日增加云贝：暂未获取');
    const gained=growth?.data?summarizeToday(growth.data.details,growth.data.hasMore,x=>dayOfTimestamp(x.time),x=>x.growthPoint):null;
    if(gained) lines.push('今日增加会员成长值：'+(gained.complete?'':'至少 ')+gained.sum+(gained.complete?'':'（记录未完整）')); else lines.push('今日增加会员成长值：暂未获取');
    if(Array.isArray(tasks?.data)) {const known=tasks.data.filter(t=>typeof t.completed==='boolean');if(known.length) lines.push('云贝待办任务：'+known.filter(t=>t.completed).length+'/'+known.length+' 已完成（接口返回的任务）');}
    if(typeof vip?.data?.unGetAllScore==='number') lines.push('会员成长值待领取：'+vip.data.unGetAllScore);
    lines.push('----- 音乐人状态 -----');
    if(typeof role?.data?.isMusician!=='boolean') lines.push('音乐人身份：暂未获取');
    else if(!role.data.isMusician) lines.push('当前账号不是音乐人');
    else {
      const extra=await Promise.allSettled([music('nmusician/workbench/mission/cycle/list',{platform:1},token),music('cloudbean/get',{},token)]);
      const missions=extra[0].status==='fulfilled' && extra[0].value?.data?.code===200?extra[0].value.data.data?.list:null;
      const bean=extra[1].status==='fulfilled' && extra[1].value?.data?.code===200?extra[1].value.data.data:null;
      if(typeof bean?.cloudBean==='number') lines.push('云豆余额：'+bean.cloudBean);
      if(typeof bean?.signed==='boolean') lines.push('音乐人签到：'+(bean.signed?'已签到':'未签到'));
      if(Array.isArray(missions) && missions.length) {
        for(const task of missions.slice(0,12)) {const name=String(task.name || task.description || '任务').replace(/[\r\n]/g,' ').slice(0,45);const state=Number(task.status)===100?'已完成':Number(task.status)===0?'未完成':'状态 '+String(task.status ?? '未知');lines.push(name+'：'+state);}
        if(missions.length>12) lines.push('其余任务请在网易云音乐人中心查看');
      } else lines.push('音乐人任务：暂未获取');
    }
    lines.push('数据以网易云接口返回为准。');
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

