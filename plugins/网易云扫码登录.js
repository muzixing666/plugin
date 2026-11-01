// [title: 网易云扫码登录]
// [language: javascript]
// [rule: ^网易云登录$]
// [platform: qq,qb,wx,gw,sb,wb,tg,tb,qx,xy,ip]
// [admin: false]
// [public: true]
// [disable: false]
// [version: 1.0.0]
// [author: muzixing666]
// [description: 私聊发送“网易云登录”，使用网易云音乐 App 扫码，将 MUSIC_U 写入青龙 NETEASE_MUSIC_U。依赖 Node.js qrcode。]
// [param: {"required":true,"key":"netease_login.ql_config","bool":false,"name":"青龙连接","placeholder":"地址丨Client ID丨Client Secret","desc":"填写青龙开放平台应用信息，用中文竖线丨分隔；应用需有环境变量的查看、新增、修改权限。"}]
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
async function qinglong(config, value, uid) {
  const p = config.split('丨').map(x => x.trim());
  if (p.length !== 3 || p.some(x => !x)) throw new Error('请先正确配置青龙连接：地址丨Client ID丨Client Secret');
  const base = p[0].replace(/\/+$/, ''); const u = new URL(base); if (!['http:', 'https:'].includes(u.protocol)) throw new Error('青龙地址格式不正确');
  const tokenUrl = new URL(base + '/open/auth/token'); tokenUrl.searchParams.set('client_id', p[1]); tokenUrl.searchParams.set('client_secret', p[2]);
  const auth = checkQL((await request(tokenUrl.toString())).data, '认证'); if (!auth || !auth.token) throw new Error('青龙认证未返回令牌');
  const headers = {'Authorization':'Bearer ' + auth.token, 'Content-Type':'application/json'};
  const envs = checkQL((await request(base + '/open/envs?searchValue=' + NAME, {headers})).data, '读取变量');
  if (!Array.isArray(envs)) throw new Error('青龙变量列表格式异常');
  const matches = envs.filter(e => e.name === NAME);
  const marker = '网易云UID:' + uid;
  const same = matches.filter(e => String(e.remarks || '').split('丨').includes(marker));
  if (same.length > 1) throw new Error('青龙存在多条相同账号的变量，请管理员整理后重试');
  const record = {name: NAME, value};
  let method = 'POST', payload = [record];
  if (same.length === 1) { const old = same[0]; const id = old.id || old._id; if (!id) throw new Error('青龙变量缺少 ID'); record.id = id; record.remarks = old.remarks || ''; method = 'PUT'; payload = record; }
  else record.remarks = marker;
  checkQL((await request(base + '/open/envs', {method, headers, body:JSON.stringify(payload)})).data, '保存变量');
  return same.length ? '更新' : '新增';
}
async function main() {
  const sender = new middleware.Sender(middleware.getSenderID());
  const chat = String((await sender.getChatID()) || '').trim();
  if (chat && chat !== '0') { await sender.reply('请私聊机器人发送“网易云登录”，不要在群聊中扫码。'); return; }
  const config = String((await middleware.bucketGet('netease_login', 'ql_config')) || '').trim();
  if (config.split('丨').length !== 3 || config.split('丨').some(x => !x.trim())) { await sender.reply('插件尚未配置青龙连接，请联系管理员。'); return; }
  let QRCode; try { QRCode = require('qrcode'); } catch (_) { await sender.reply('缺少 Node.js 依赖 qrcode，请在羽化面板依赖管理中安装后重试。'); return; }
  try {
    const created = await music('login/qrcode/unikey', {type:3}); const key = created.data && created.data.unikey;
    if (created.data.code !== 200 || !key) throw new Error('获取网易云登录二维码失败');
    const qr = await QRCode.toDataURL('https://music.163.com/login?codekey=' + encodeURIComponent(key));
    await sender.reply('请用网易云音乐 App 扫码并确认登录，二维码有效期约 3 分钟。');
    await sender.replyImage('base64://' + qr.split(',')[1]);
    let scanned = false; const end = Date.now() + 180000;
    while (Date.now() < end) {
      await new Promise(r => setTimeout(r, 3000));
      const result = await music('login/qrcode/client/login', {key, type:3}); const code = result.data.code;
      if (code === 800) { await sender.reply('二维码已过期，请重新发送“网易云登录”。'); return; }
      if (code === 802 && !scanned) { scanned = true; await sender.reply('已扫码，请在网易云音乐 App 中确认。'); }
      if (code === 803) {
        const item = result.cookies.find(c => /^MUSIC_U=/i.test(c));
        const value = item ? item.slice(item.indexOf('=') + 1).split(';')[0] : '';
        if (!value) throw new Error('登录成功但未取得 MUSIC_U，青龙变量未修改');
        const account = await music('nuser/account/get', {}, value);
        const uid = account.data && account.data.account && account.data.account.id;
        if (account.data.code !== 200 || !uid) throw new Error('无法确认网易云账号，青龙变量未修改');
        const action = await qinglong(config, value, String(uid));
        await sender.reply('网易云登录成功，已' + action + '青龙变量 NETEASE_MUSIC_U。'); return;
      }
      if (![801,802].includes(code)) throw new Error('网易云登录状态异常（' + String(code) + '）');
    }
    await sender.reply('等待扫码超时，请重新发送“网易云登录”。');
  } catch (e) { await sender.reply('网易云登录未完成：' + (e.message || '请求失败')); }
}
if (require.main === module) main().catch(() => {});

