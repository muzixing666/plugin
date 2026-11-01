// [title: 简洁功能菜单]
// [language: javascript]
// [rule: ^功能菜单$]
// [platform: qq,qb,wx,gw,sb,wb,tg,tb,qx,xy,ip,web,wxmp]
// [public: true]
// [admin: false]
// [disable: false]
// [version: 1.0.0]
// [author: muzixing666]
// [description: 发送功能菜单，自动列出已启用插件的常用文字指令。]
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
    const lines=['📋 功能菜单'];
    for(const p of plugins) {
      const selected=p.commands.slice(0,6);
      lines.push('\n'+p.title+'\n'+selected.join(' · ')+(p.commands.length>selected.length?' 等':''));
    }
    lines.push('\n发送对应指令使用，账号操作请私聊。');
    let part='';
    for(const line of lines) {
      if(part && part.length+line.length+1>3000) {await sender.reply(part);part='';}
      part+=(part?'\n':'')+line;
    }
    if(part) await sender.reply(part);
  } catch (_) { await sender.reply('暂时无法读取插件列表，请稍后再试。'); }
}
if(require.main===module) main().catch(()=>{});

