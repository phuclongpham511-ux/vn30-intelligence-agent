// Synthetic component interactions only; no browser, provider, DB or saved reviews.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {localeTools} from '../lib/i18n.ts';
import {fixture} from './fixtures/fundamental-summary.mjs';
const require=createRequire(import.meta.url);
const descendants=node=>!node||typeof node!=='object'?[]:Array.isArray(node)?node.flatMap(descendants):[node,...descendants(node.props?.children)];
const text=node=>Array.isArray(node)?node.map(text).join(''):node&&typeof node==='object'?text(node.props?.children):node==null?'':String(node);
function component(name,language='en',overrides={}){
 const values=[];let cursor=0;
 const react={...React,useState(initial){const key=cursor++;if(!(key in values))values[key]=typeof initial==='function'?initial():initial;return [values[key],next=>{values[key]=typeof next==='function'?next(values[key]):next;}];}};
 const exports={},code=transformSync(readFileSync(new URL(`../app/components/stock/${name}.tsx`,import.meta.url),'utf8'),{filename:name+'.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 new Function('require','exports',code)(id=>id==='react'?react:id==='@/lib/i18n'?{useLocale:()=>localeTools(language)}:overrides[id]||require(id.startsWith('@/lib/')?`../lib/${id.slice(6)}.ts`:id),exports);
 return (props,key='default')=>{cursor=0;return exports[key](props);};
}

test('hiding amount series leaves a percent axis, never a misleading currency axis',()=>{
 const recharts=Object.fromEntries(['ResponsiveContainer','ComposedChart','Bar','Line','XAxis','YAxis','CartesianGrid','Tooltip','ReferenceLine'].map(name=>[name,'test-'+name]));
 const render=component('FinancialAnalysisPanel','en',{recharts});
 const panel={key:'funding',source:'Synthetic test',frequency:'annual',status:'QUALIFIED',chart:'stacked',partial:false,methodology:'Synthetic contract',reasons:[],series:[{key:'total_liabilities',label:'Total liabilities',unit:'VND'},{key:'equity',label:'Total equity',unit:'VND'},{key:'liabilities_assets',label:'Liabilities / assets',unit:'fraction'}],rows:[{period:'2025',values:{total_liabilities:70,equity:30,liabilities_assets:.7},statuses:{total_liabilities:'QUALIFIED',equity:'QUALIFIED',liabilities_assets:'QUALIFIED'},bases:{total_liabilities:'consolidated',equity:'consolidated',liabilities_assets:'consolidated'}}]};
 const props={panel,kind:'funding',unit:'billions'};
 for(const label of ['Total liabilities','Total equity']){
  const button=descendants(render(props)).find(n=>n.type==='button'&&text(n).startsWith(label));assert.ok(button);button.props.onClick();
 }
 const nodes=descendants(render(props)),axes=nodes.filter(n=>n.type==='test-YAxis');
 assert.equal(axes.length,1);assert.equal(axes[0].props.yAxisId,'rate');assert.equal(axes[0].props.orientation,'left');
 assert.equal(nodes.find(n=>n.type==='test-ReferenceLine').props.yAxisId,'rate');
 assert.match(text(nodes.find(n=>n.type==='header')),/% · Annual/);
 assert.doesNotMatch(text(nodes.find(n=>n.type==='header')),/VND bn/);
 nodes.find(n=>n.type==='button'&&text(n).startsWith('Liabilities / assets')).props.onClick();
 const empty=render(props);assert.equal(descendants(empty).some(n=>n.props?.['data-financial-chart']),false);
 assert.match(text(empty),/Select a series/);
});

test('unqualified chart offers the source action without any plotted observations in EN/VI',()=>{
 for(const language of ['en','vi']){
  let actions=0;const render=component('FinancialAnalysisPanel',language);
  const tree=render({kind:'assets',unit:'billions',onSources:()=>actions++});
  assert.equal(descendants(tree).some(n=>n.props?.['data-financial-chart']),false);
  const button=descendants(tree).find(n=>n.type==='button');assert.ok(button);button.props.onClick();assert.equal(actions,1);
  assert.match(text(tree),language==='vi'?/Xem nguồn tài chính/:/Inspect financial sources/);
 }
});

test('statement collapse/expand affects only real source-parent descendants and preserves zero',()=>{
 const render=component('FinancialStatementTable');
 const line=(code,parent=null)=>({code,parent,name_en:code,name_vi:code,unit:'VND',value:0,raw_value:0,semantic_status:'reported'});
 const props={periods:[{period:'2025',basis:'annual',consolidation:'consolidated',items:[line('parent'),line('child','parent'),line('independent')]}],unit:'vnd',label:'Balance sheet'};
 let tree=render(props);descendants(tree).find(n=>n.type==='button'&&text(n)==='Collapse groups').props.onClick();
 tree=render(props);let html=renderToStaticMarkup(tree);assert.doesNotMatch(html,/>child</);assert.match(html,/>independent</);assert.match(html,/<td>0<\/td>/);
 descendants(tree).find(n=>n.type==='button'&&text(n)==='Expand all').props.onClick();
 html=renderToStaticMarkup(render(props));assert.match(html,/>child</);assert.match(html,/VND/);
});

test('bank growth labels follow supported operating income, without an industrial revenue label',()=>{
 for(const language of ['en','vi']){
  const render=component('FinancialAnalysisPanel',language);
  const tree=render({kind:'growth',unit:'billions',panel:{key:'growth',frequency:'annual',status:'UNAVAILABLE',source:'Synthetic bank contract',methodology:'No qualified values',reasons:[],rows:[],series:[{key:'operating_income',label:'Operating income',unit:'VND'}]}});
  const heading=text(descendants(tree).find(n=>n.type==='h3'));
  assert.equal(heading,language==='en'?'Operating income and profit trends':'Xu hướng thu nhập hoạt động và lợi nhuận');
 }
});

test('financial source action navigates the existing section and period controls retain callbacks',()=>{
 const render=component('FundamentalTrends','en',{'./FinancialAnalysisPanel':{__esModule:true,default:'test-panel'},'./FinancialResearchCharts':{__esModule:true,default:()=>null},'./FinancialStatementTable':{__esModule:true,default:()=>null},'../ui/button':{Button:'button'},'../ui/skeleton':{Skeleton:'div'}});
 const data=fixture();data.available_period_types=['annual','quarterly'];let selected;
 const props={data,loading:false,error:false,retry(){},onFrequency:value=>selected=value};
 let tree=render(props,'FundamentalTrendsView');const nodes=descendants(tree);
 nodes.find(n=>n.type==='button'&&text(n)==='Quarterly').props.onClick();assert.equal(selected,'quarterly');
 nodes.find(n=>n.type==='button'&&text(n)==='Inspect financial sources').props.onClick();
 tree=render(props,'FundamentalTrendsView');assert.match(text(tree),/Documents and sources/);
 assert.match(text(tree),/Provider receipts are available evidence, not original issuer filings/);
 assert.equal(descendants(tree).some(n=>n.type==='test-panel'),false);
});

test('empty charts share one disclosure while a qualified historical series remains visible',()=>{
 for(const language of ['en','vi']){
  const render=component('FundamentalTrends',language,{'./FinancialAnalysisPanel':{__esModule:true,default:'test-panel'},'./FinancialResearchCharts':{__esModule:true,default:()=>null},'./FinancialStatementTable':{__esModule:true,default:()=>null},'../ui/button':{Button:'button'},'../ui/skeleton':{Skeleton:'div'}});
  const data=fixture(),props={data,loading:false,error:false,retry(){}};
  let tree=render(props,'FundamentalTrendsView');
  assert.equal(descendants(tree).filter(n=>n.props?.['data-financial-unavailable-group']!==undefined).length,1);
  assert.equal(descendants(tree).filter(n=>n.type==='test-panel').length,0);
  data.research_panels=[{key:'funding',status:'QUALIFIED',rows:[{period:'2025',values:{equity:0},statuses:{equity:'QUALIFIED'},bases:{equity:'consolidated'}}],reasons:[]}];
  tree=render(props,'FundamentalTrendsView');
  const panels=descendants(tree).filter(n=>n.type==='test-panel');
  assert.equal(panels.length,1);assert.equal(panels[0].props.kind,'funding');
  assert.equal(panels[0].props.panel.rows[0].values.equity,0);
  data.profile='bank';data.financial_identity_guard=true;
  descendants(tree).find(n=>n.type==='button'&&text(n)===localeTools(language).t('Revenue, earnings & growth')).props.onClick();
  tree=render(props,'FundamentalTrendsView');
  const disclosure=descendants(tree).find(n=>n.props?.['data-financial-unavailable-group']!==undefined);
  assert.ok(text(disclosure).includes(localeTools(language).ui('Operating income and profit trends')));
  assert.ok(!text(disclosure).includes(localeTools(language).ui('Revenue and profit trends')));
 }
});
