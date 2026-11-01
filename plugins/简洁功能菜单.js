// [title: 简洁功能菜单]
// [language: javascript]
// [rule: ^菜单$]
// [platform: qq,qb,wx,gw,sb,wb,tg,tb,qx,xy,ip,web,wxmp]
// [public: true]
// [admin: false]
// [disable: false]
// [version: 2.2.0]
// [author: muzixing666]
// [description: 发送菜单查看项目；在插件配置中直接编辑自动获取的项目并新增自定义项目。]
'use strict';
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { SillyGirlPluginConfig } = require('sillygirl');
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
  function mapping(value) { const out={}; for(const item of String(value || '').split(/[；\n]/)) { const i=item.indexOf('='); if(i>0) out[item.slice(0,i).trim()]=item.slice(i+1).trim(); } return out; }
  const intros=mapping(settings.intros), names=mapping(settings.names), customCommands=mapping(settings.commands);
  const order=String(settings.order || '').split(/[,，;；\n]/).map(x=>x.trim()).filter(Boolean);
  const output=[];
  for(const p of rows) {
    if(![2,6].includes(Number(p.status)) || p.disable || (!admin && (p.admin_only || p.public === false))) continue;
    const title=String(p.title||'').trim(); if(!title || title==='简洁功能菜单' || hidden.has(title)) continue;
    const sources=meta.get(title)||[];
    if(sources.length && !sources.some(x=>!x.hidden && (!platform || !x.platforms || x.platforms.includes(platform)))) continue;
    const list=Object.prototype.hasOwnProperty.call(customCommands,title) ? customCommands[title].split(/[,，、]/).map(x=>x.trim()).filter(Boolean) : commands(p.rule);
    if(!list.length) continue;
    const displayName=String(names[title] || title).replace(/[\r\n]/g,' ').slice(0,80);
    output.push({title:displayName,originalTitle:title,sourceId:String(p.id || title),commands:list,description:briefDescription(intros[title] || p.desc)});
  }
  return output.sort((a,b)=>{const ai=order.indexOf(a.originalTitle),bi=order.indexOf(b.originalTitle); if(ai!==bi) return (ai<0?Infinity:ai)-(bi<0?Infinity:bi); return a.title.localeCompare(b.title,'zh-CN');});
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
async function fetchRows(base) {
  const u=new URL(base);if(!['http:','https:'].includes(u.protocol)) throw new Error('面板地址无效');
  const rows=[];let current=1,total=0;
  do {
    const url=base+'/api/plugins/list.json?current='+current+'&pageSize=500&activeKey=installed';
    const response=await fetch(url,{signal:AbortSignal.timeout(8000)});
    if(!response.ok) throw new Error('插件列表不可用');
    const payload=await response.json(),data=payload?.data;
    if(!Array.isArray(data?.data)) throw new Error('插件列表格式异常');
    rows.push(...data.data);total=Number(data.total)||0;current++;
    if(!data.data.length) break;
  } while(rows.length<total && current<=10);
  return rows;
}
function fieldKey(item) {return 'item_'+crypto.createHash('sha256').update(item.sourceId).digest('hex').slice(0,16);}
function valueOr(values,key,fallback) {return Object.prototype.hasOwnProperty.call(values || {},key) ? values[key] : fallback;}
function schemaFor(items,legacy={},customCount=3) {
  const prop={
    group_basics:{type:'null',title:'基本设置','x-autman-spliter':true},
    panel_url:{type:'string',title:'面板内部地址',default:String(legacy.panel_url || 'http://127.0.0.1:6060'),description:'插件列表地址，一般无需修改。'},
    menu_title:{type:'string',title:'菜单标题',default:String(legacy.title || '📋 功能菜单')},
    menu_footer:{type:'string',title:'菜单提示',default:String(legacy.footer || '回复编号查看介绍和指令；q 退出。')},
    custom_count:{type:'string',title:'自定义项目数量',default:'3',description:'默认 3 项，最多 20 项。修改数量并保存后，发送一次“菜单”，重新打开设置即可看到新项目。'},
  };
  const oldItems=new Map(visibleRows(items.rows,items.meta,'',true,legacy).map(x=>[x.originalTitle,x]));
  const all=visibleRows(items.rows,items.meta,'',true,{});
  all.forEach((item,i)=>{
    const key=fieldKey(item),old=oldItems.get(item.originalTitle),base=old || item;
    prop['group_'+key]={type:'null',title:'📌 '+item.originalTitle,'x-autman-spliter':true};
    prop[key+'_enabled']={type:'boolean',title:'显示此项目',default:!!old || !String(legacy.hidden||'').split(/[,，;；\n]/).map(x=>x.trim()).includes(item.originalTitle)};
    prop[key+'_title']={type:'string',title:'名称',default:base.title};
    prop[key+'_intro']={type:'string',title:'简介',default:base.description};
    prop[key+'_commands']={type:'string',title:'指令',default:base.commands.join('，'),description:'用逗号分隔；仅修改显示，不会修改插件的实际指令。'};
    prop[key+'_order']={type:'string',title:'排序',default:String((old ? Array.from(oldItems.keys()).indexOf(item.originalTitle) : i)+1),description:'数字越小越靠前。'};
  });
  for(let i=1;i<=customCount;i++) {
    const key='custom_'+i;
    prop['group_'+key]={type:'null',title:'✏️ 自定义项目 '+i,'x-autman-spliter':true};
    prop[key+'_enabled']={type:'boolean',title:'启用此项目',default:false};
    prop[key+'_title']={type:'string',title:'名称',default:''};
    prop[key+'_intro']={type:'string',title:'简介',default:''};
    prop[key+'_commands']={type:'string',title:'指令',default:'',description:'用逗号分隔；需要已存在的插件响应相应指令。'};
    prop[key+'_order']={type:'string',title:'排序',default:String(1000+i)};
  }
  return {type:'object',properties:prop};
}
function defaultValues(schema) {const out={};for(const [k,v] of Object.entries(schema.properties))if(Object.prototype.hasOwnProperty.call(v,'default'))out[k]=v.default;return out;}
function renderedItems(rows,meta,platform,admin,values,schema,customCount) {
  const defaults=defaultValues(schema), all=visibleRows(rows,meta,platform,admin,{}), out=[];
  for(const item of all) {
    const key=fieldKey(item), get=suffix=>valueOr(values,key+'_'+suffix,defaults[key+'_'+suffix]);
    if(!get('enabled')) continue;
    const title=String(get('title') || '').trim(), list=String(get('commands') || '').split(/[,，、\n]/).map(x=>x.trim()).filter(Boolean);
    if(!title || !list.length) continue;
    out.push({title:title.slice(0,80),description:briefDescription(get('intro')),commands:list,order:Number(get('order'))||0});
  }
  for(let i=1;i<=customCount;i++) {
    const key='custom_'+i,get=suffix=>valueOr(values,key+'_'+suffix,defaults[key+'_'+suffix]);
    if(!get('enabled')) continue;
    const title=String(get('title') || '').trim(),list=String(get('commands') || '').split(/[,，、\n]/).map(x=>x.trim()).filter(Boolean);
    if(title && list.length) out.push({title:title.slice(0,80),description:briefDescription(get('intro')),commands:list,order:Number(get('order'))||0});
  }
  return out.sort((a,b)=>a.order-b.order || a.title.localeCompare(b.title,'zh-CN'));
}
async function legacySettings() {
  const keys=['panel_url','title','footer','hidden','intros','names','commands','order'];
  const result={};for(const key of keys) {try{result[key]=await middleware.bucketGet('simple_menu',key);}catch(_){}}
  return result;
}
function customCount(value) {const n=Number.parseInt(String(value || '3'),10);return Number.isFinite(n)?Math.max(1,Math.min(20,n)):3;}
async function prepareConfig(registerOnly=false) {
  const legacy=registerOnly?{}:await legacySettings();
  let prior={};
  try {if(!registerOnly && process.env.PLUGIN_CONFIG_JSON) prior=JSON.parse(process.env.PLUGIN_CONFIG_JSON);}catch(_){}
  const base=String(prior.panel_url || legacy.panel_url || 'http://127.0.0.1:6060').trim().replace(/\/+$/,'');
  const rows=await fetchRows(base),meta=sourceMetadata('/data/plugins'),items={rows,meta};
  let schema=schemaFor(items,legacy,3), cfg=new SillyGirlPluginConfig(schema);
  if(registerOnly) return {rows,meta,schema,values:{},count:3};
  let values=await cfg.get();const count=customCount(values.custom_count);
  if(count!==3) {schema=schemaFor(items,legacy,count);cfg=new SillyGirlPluginConfig(schema);values=await cfg.get();}
  return {rows,meta,schema,values:values || {},count};
}
async function main() {
  const sender=new middleware.Sender(middleware.getSenderID());
  try {
    const platform=String(await sender.getImtype() || '').toLowerCase(),admin=!!(await sender.isAdmin());
    const {rows,meta,schema,values,count}=await prepareConfig(false);
    const plugins=renderedItems(rows,meta,platform,admin,values,schema,count);
    if(!plugins.length) {await sender.reply('暂无可展示的插件指令。');return;}
    const defaults=defaultValues(schema),settings={title:valueOr(values,'menu_title',defaults.menu_title),footer:valueOr(values,'menu_footer',defaults.menu_footer)};
    await showMenu(sender,plugins,settings);
  } catch (_) {await sender.reply('暂时无法读取插件列表或配置，请稍后再试。');}
}
if(require.main===module) {
  if(process.env.SILLYGIRL_CONFIG_REGISTER_ONLY==='true') prepareConfig(true).catch(()=>{});
  else main().catch(()=>{});
}
