// [title: 简洁功能菜单]
// [language: javascript]
// [rule: ^菜单$]
// [platform: qq,qb,wx,gw,sb,wb,tg,tb,qx,xy,ip,web,wxmp]
// [public: true]
// [admin: false]
// [disable: false]
// [version: 1.3.0]
// [author: muzixing666]
// [description: 发送菜单查看插件列表；标题、页脚、隐藏项目和项目简介可在设置中修改。]
// [param: {"required":false,"key":"simple_menu.panel_url","bool":false,"name":"面板内部地址","placeholder":"http://127.0.0.1:6060","desc":"默认使用羽化面板容器内部地址，无需填写。"}]
// [param: {"required":false,"key":"simple_menu.title","bool":false,"name":"菜单标题","placeholder":"📋 功能菜单","desc":"一级菜单顶部的文字。"}]
// [param: {"required":false,"key":"simple_menu.footer","bool":false,"name":"菜单提示","placeholder":"回复编号查看介绍和指令；q 退出。","desc":"一级菜单底部显示的文字。"}]
// [param: {"required":false,"key":"simple_menu.hidden","bool":false,"name":"隐藏项目","placeholder":"项目一,项目二","desc":"按插件标题填写，多个标题用逗号或中文逗号分隔。"}]
// [param: {"required":false,"key":"simple_menu.intros","bool":false,"name":"自定义项目简介","placeholder":"网易云扫码登录=登录网易云并查询账号；京东登录=京东账号登录","desc":"格式：插件标题=简介；多个用中文分号分隔。未填写的项目使用插件原有介绍。"}]
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
function briefDescription(value) {
  const text=String(value || '').replace(/<\s*br\s*\/?\s*>/gi,'。').replace(/<[^>]*>/g,' ').replace(/https?:\/\/\S+/gi,'').replace(/&nbsp;|&#160;/gi,' ').replace(/&amp;/gi,'&').replace(/[❶❷❸❹❺]/g,' ').replace(/\s+/g,' ').trim();
  if(!text) return '暂无介绍';
  const first=text.split(/[。；;]/).map(x=>x.trim()).find(Boolean) || text;
  const chars=Array.from(first); return chars.length>70?chars.slice(0,70).join('')+'…':first;
}
function visibleRows(rows, meta, platform, admin, settings={}) {
  const hidden = new Set(String(settings.hidden || "").split(/[,，;；\n]/).map(x=>x.trim()).filter(Boolean));
  const intros = {};
  for(const item of String(settings.intros || "").split(/[；\n]/)) { const i=item.indexOf("="); if(i>0) intros[item.slice(0,i).trim()]=item.slice(i+1).trim(); }
  const output=[];
  for(const p of rows) {
    if(![2,6].includes(Number(p.status)) || p.disable || (!admin && (p.admin_only || p.public === false))) continue;
    const title=String(p.title||'').trim(); if(!title || title==='简洁功能菜单' || hidden.has(title)) continue;
    const sources=meta.get(title)||[];
    if(sources.length && !sources.some(x=>!x.hidden && (!x.platforms || x.platforms.includes(platform)))) continue;
    const list=commands(p.rule); if(!list.length) continue;
    output.push({title,commands:list,description:briefDescription(intros[title] || p.desc)});
  }
  return output.sort((a,b)=>a.title.localeCompare(b.title,'zh-CN'));
}
async function showMenu(sender, plugins, settings={}) {
  const chat=String(await sender.getChatID() || '').trim();
  while(true) {
    const lines=[String(settings.title || '📋 功能菜单').slice(0,100)];
    for(let i=0;i<plugins.length;i++) lines.push((i+1)+'. '+plugins[i].title);
    lines.push('\n'+String(settings.footer || '回复编号查看介绍和指令；q 退出。').slice(0,160));
    let part='';
    for(const line of lines) {
      if(part && part.length+line.length+1>3000) {await sender.reply(part);part='';}
      part+=(part?'\n':'')+line;
    }
    if(part) await sender.reply(part);
    const input=String(await sender.input(60000,0,!!chat && chat!=='0') || '').trim().toLowerCase();
    if(!input) {await sender.reply('菜单已超时退出。'); return;}
    if(['q','取消','退出'].includes(input)) {await sender.reply('已退出菜单。'); return;}
    const n=/^[1-9][0-9]*$/.test(input)?Number(input):0;
    if(n>=1 && n<=plugins.length) {
      const selected=plugins[n-1];
      await sender.reply('【'+selected.title+'】\n'+selected.description+'\n\n指令：\n'+selected.commands.join('\n')+'\n\n发送对应指令即可使用；发送“菜单”返回菜单。');
      return;
    }
    await sender.reply('请输入菜单编号，或发送 q 退出。');
  }
}
async function main() {
  const sender=new middleware.Sender(middleware.getSenderID());
  const platform=String(await sender.getImtype() || '').toLowerCase(); const admin=!!(await sender.isAdmin());
  const values=await Promise.all(['panel_url','title','footer','hidden','intros'].map(k=>middleware.bucketGet('simple_menu',k)));
  const [panel_url,title,footer,hidden,intros]=values; const settings={title,footer,hidden,intros};
  const base=String(panel_url || 'http://127.0.0.1:6060').trim().replace(/\/+$/,'');
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
    const plugins=visibleRows(rows,sourceMetadata('/data/plugins'),platform,admin,settings);
    if(!plugins.length) {await sender.reply('暂无可展示的插件指令。'); return;}
    await showMenu(sender,plugins,settings);
  } catch (_) { await sender.reply('暂时无法读取插件列表，请稍后再试。'); }
}
if(require.main===module) main().catch(()=>{});

