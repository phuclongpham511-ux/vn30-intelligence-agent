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
const summaryComponent=(language='en')=>component('FundamentalTrends',language,{'./FinancialAnalysisPanel':{__esModule:true,default:()=>null},'./FinancialResearchCharts':{__esModule:true,default:()=>null},'./FinancialStatementTable':{__esModule:true,default:()=>null},'../ui/button':{Button:'button'},'../ui/skeleton':{Skeleton:'div'}});
const descendants=node=>!node||typeof node!=='object'?[]:Array.isArray(node)?node.flatMap(descendants):[node,...descendants(node.props?.children)];
const text=node=>Array.isArray(node)?node.map(text).join(''):node&&typeof node==='object'?text(node.props?.children):node==null?'':String(node);
function component(name,language='en',overrides={}){
 const values=[];let cursor=0;
 const react={...React,useState(initial){const key=cursor++;if(!(key in values))values[key]=typeof initial==='function'?initial():initial;return [values[key],next=>{values[key]=typeof next==='function'?next(values[key]):next;}];}};
 const exports={},code=transformSync(readFileSync(new URL(`../app/components/stock/${name}.tsx`,import.meta.url),'utf8'),{filename:name+'.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 new Function('require','exports',code)(id=>id==='react'?react:id==='@/lib/i18n'?{useLocale:()=>localeTools(language)}:id==='@/lib/chart-motion'?{useChartMotion:()=>false}:overrides[id]||require(id.startsWith('@/lib/')?`../lib/${id.slice(6)}.ts`:id),exports);
 return (props,key='default')=>{cursor=0;return exports[key](props);};
}

test('research snapshot retains reported zero, period, basis and historical freshness in EN/VI',()=>{
 for(const language of ['en','vi']){
  const render=summaryComponent(language),data=fixture();let opened=0;
  const tree=render({data,loading:false,error:false,retry(){},onOpen(){opened++;}},'FinancialResearchSnapshot');
  const html=renderToStaticMarkup(tree);
  assert.match(html,/2025/);assert.match(html,/Synthetic:VCI/);assert.match(html,/0 /);
  assert.ok(html.includes(localeTools(language).t('Read at')));
  assert.ok(html.includes(localeTools(language).t('Qualification applies to the reported period; current freshness is not certified. Inspect each metric for its definition and limitations.')));
  descendants(tree).find(n=>n.type==='button').props.onClick();assert.equal(opened,1);
 }
});

test('research snapshot never promotes unqualified or unknown-basis financial values',()=>{
 for(const mutate of [d=>d.fundamental_summary.metrics[2].status='UNQUALIFIED',d=>d.fundamental_summary.consolidation=null]){
  const data=fixture();data.fundamental_summary.metrics[2].value=987654321000;mutate(data);
  const tree=summaryComponent()({data,loading:false,error:false,retry(){},onOpen(){}},'FinancialResearchSnapshot');
  const html=renderToStaticMarkup(tree);assert.doesNotMatch(html,/987/);assert.match(html,/—/);
 }
});

test('research snapshot has distinct loading, retry and missing-coverage states',()=>{
 for(const language of ['en','vi']){
  const render=summaryComponent(language);let retried=0;
  for(const state of [{loading:true,error:false},{loading:false,error:true},{loading:false,error:false}]){
   const tree=render({data:null,...state,retry(){retried++;},onOpen(){}},'FinancialResearchSnapshot');
   const html=renderToStaticMarkup(tree);assert.doesNotMatch(html,/data-financial-qualification/);
   if(state.loading)assert.match(html,/aria-busy="true"/);
   if(state.error){assert.match(html,/role="alert"/);descendants(tree).find(n=>n.type==='button'&&text(n)===localeTools(language).t('Retry')).props.onClick();}
  }
  assert.equal(retried,1);
 }
});

