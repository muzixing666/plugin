// [title: 简洁功能菜单]
// [language: javascript]
// [rule: ^功能菜单$]
// [platform: qq,qb,wx,gw,sb,wb,tg,tb,qx,xy,ip,web,wxmp]
// [public: true]
// [admin: false]
// [disable: false]
// [version: 1.1.0]
// [author: muzixing666]
// [description: 发送功能菜单，按编号查看已启用插件的指令。]
// [param: {"required":false,"key":"simple_menu.panel_url","bool":false,"name":"面板内部地址","placeholder":"http://127.0.0.1:6060","desc":"默认使用羽化面板容器内部地址，无需填写。"}]
'use strict';
const fs = require('fs');
const path = require('path');
const middleware = require('middleware');

function branches(text) {
  const result=[]; let depth=0, start=0;
  for(let i=0;i<text.length;i++) {
    if(text[i]==='(') depth++;
    else if(text[i]===')') { if(--depth<0) return []; }
    else if(text[i]==='|' && depth===0) { result.push(text.slice(start,i)); start=i+1; }
  }
  if(depth!==0) return [];
  result.push(text.slice(start)); return result;
}
function expand(text) {
  const alts=branches(text); if(!alts.length) return [];
  if(alts.length>1) return alts.flatMap(expand).slice(0,40);
  let result=[''];
  for(let i=0;i<text.length;) {
    const ch=text[i];
    if(ch==='(') {
      let end=i+1, depth=1;
      while(end<text.length && depth) {if(text[end]==='(') depth++; if(text[end]===')') depth--; end++;}
      if(depth) return [];
      const choices=expand(text.slice(i+1,end-1)); if(!choices.length) return [];
      result=result.flatMap(prefix=>choices.map(choice=>prefix+choice)).slice(0,40); i=end;
    } else {
      if(!/[\p{L}\p{N}_\- ]/u.test(ch)) return [];
      result=result.map(v=>v+ch); i++;
    }
  }
  return result;
}
function commands(rule) {
  const parts=branches(String(rule || '')); const out=[];
  for(const part of parts) {
    if(!part.startsWith('^') || !part.endsWith('$')) continue;
    for(const item of expand(part.slice(1,-1))) {
      const command=item.trim();
      if(command && command.length<=35 && !out.includes(command)) out.push(command);
    }
  }
  return out;
}
function sourceMetadata(dir) {
  const out=new Map();
  try {
    for(const entry of fs.readdirSync(dir,{withFileTypes:true})) {
      if(!entry.isFile() || !/\.(js|py)$/i.test(entry.name)) continue;
      try {
        const header=fs.readFileSync(path.join(dir,entry.name),'utf8').split(/\r?\n/,60).join('\n');
        const title=header.match(/^\s*(?:#|\/\/)\s*\[title:\s*([^\]]+)\]/im)?.[1]?.trim();
        const platforms=header.match(/^\s*(?:#|\/\/)\s*\[platform:\s*([^\]]+)\]/im)?.[1]?.split(',').map(x=>x.trim().toLowerCase()).filter(Boolean);
        const hidden=/^\s*(?:#|\/\/)\s*\[menu_hidden:\s*true\s*\]/im.test(header);
        if(title) { const current=out.get(title)||[]; current.push({platforms,hidden}); out.set(title,current); }
      } catch (_) {}
    }
  } catch (_) {}
  return out;
}
function visibleRows(rows, meta, platform, admin) {
  const output=[];
  for(const p of rows) {
    if(![2,6].includes(Number(p.status)) || p.disable || (!admin && (p.admin_only || p.public === false))) continue;
    const title=String(p.title||'').trim(); if(!title || title==='简洁功能菜单') continue;
    const sources=meta.get(title)||[];
    if(sources.length && !sources.some(x=>!x.hidden && (!x.platforms || x.platforms.includes(platform)))) continue;
    const list=commands(p.rule); if(!list.length) continue;
    output.push({title,commands:list});
  }
  return output.sort((a,b)=>a.title.localeCompare(b.title,'zh-CN'));
}
async function showMenu(sender, plugins) {
  const pageSize=8, pageCount=Math.ceil(plugins.length/pageSize);
  let page=0;
  const chat=String(await sender.getChatID() || '').trim();
  while(true) {
    const start=page*pageSize;
    const lines=['📋 功能菜单（'+(page+1)+'/'+pageCount+'）'];
    for(let i=start;i<Math.min(start+pageSize,plugins.length);i++) lines.push((i+1)+'. '+plugins[i].title);
    lines.push('\n回复编号查看指令'+(pageCount>1?'；n 下一页，p 上一页':'')+'；q 退出。');
    await sender.reply(lines.join('\n'));
    const input=String(await sender.input(60000,0,!!chat && chat!=='0') || '').trim().toLowerCase();
    if(!input) {await sender.reply('菜单已超时退出。'); return;}
    if(['q','取消','退出'].includes(input)) {await sender.reply('已退出菜单。'); return;}
    if(input==='n' && pageCount>1) {page=Math.min(page+1,pageCount-1);continue;}
    if(input==='p' && pageCount>1) {page=Math.max(page-1,0);continue;}
    const n=/^[1-9][0-9]*$/.test(input)?Number(input):0;
    if(n>=1 && n<=plugins.length) {
      const selected=plugins[n-1];
      await sender.reply('【'+selected.title+'】\n'+selected.commands.join('\n')+'\n\n发送对应指令即可使用；发送“功能菜单”返回菜单。');
      return;
    }
    await sender.reply('请输入菜单编号，或发送 q 退出。');
  }
}
async function main() {
  const sender=new middleware.Sender(middleware.getSenderID());
  const platform=String(await sender.getImtype() || '').toLowerCase(); const admin=!!(await sender.isAdmin());
  const base=String(await middleware.bucketGet('simple_menu','panel_url') || 'http://127.0.0.1:6060').trim().replace(/\/+$/,'');
  try {
    const u=new URL(base); if(!['http:','https:'].includes(u.protocol)) throw new Error('地址无效');
    const rows=[]; let current=1,total=0;
    do {
      const url=base+'/api/plugins/list.json?current='+current+'&pageSize=500&activeKey=installed';
      const response=await fetch(url,{signal:AbortSignal.timeout(8000)});
      if(!response.ok) throw new Error('插件列表不可用');
      const payload=await response.json(), data=payload?.data;
      if(!Array.isArray(data?.data)) throw new Error('插件列表格式异常');
      rows.push(...data.data); total=Number(data.total)||0; current++;
      if(!data.data.length) break;
    } while(rows.length<total && current<=10);
    const plugins=visibleRows(rows,sourceMetadata('/data/plugins'),platform,admin);
    if(!plugins.length) {await sender.reply('暂无可展示的插件指令。'); return;}
    await showMenu(sender,plugins);
  } catch (_) { await sender.reply('暂时无法读取插件列表，请稍后再试。'); }
}
if(require.main===module) main().catch(()=>{});

