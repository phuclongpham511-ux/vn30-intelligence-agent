import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
const require=createRequire(import.meta.url);
let section='overview',statement='income';
const react={...React,useState(initial){if(initial==='overview')return [section,()=>{}];if(initial==='income')return [statement,()=>{}];return React.useState(initial);}};
const exports={};
const compiled=transformSync(readFileSync(new URL('../app/components/stock/FundamentalTrends.tsx',import.meta.url),'utf8'),{filename:'FundamentalTrends.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
new Function('require','exports',compiled)(name=>name==='react'?react:['./FinancialResearchCharts','./FinancialStatementTable'].includes(name)?{__esModule:true,default:()=>null}:name==='../ui/button'?{Button:({variant,...props})=>React.createElement('button',props)}:name==='../ui/skeleton'?{Skeleton:props=>React.createElement('div',props)}:require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
const row={ticker:'ABC',period:'2025',source:'Reported source',currency:'VND',revenue:0,net_profit:null,gross_margin:null,net_margin:null,roe:null,revenue_growth_yoy:null,net_profit_growth_yoy:null};
const data={available_period_types:['annual'],ticker:'ABC',source:'Reported source',currency:'VND',period_type:'annual',rows:[row],changes:[],financial_identity_guard:false,sector:null,industry:null,publication_date:null,consolidation:null,read_at:'2026-10-13T13:00:00Z'};
const render=(props={},language='en',view='overview',kind='income')=>{section=view;statement=kind;return renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(exports.FundamentalTrendsView,{data:null,loading:false,error:false,retry(){},...props})));};
test('financial empty, loading and provider failure do not fabricate zero metrics',()=>{
  assert.match(render(),/No financial observations/);
  assert.match(render({loading:true}),/Loading financial statements/);
  assert.match(render({error:true}),/temporarily unavailable/);
  assert.doesNotMatch(render({error:true}),/No financial observations|0 VND/);
});
test('reported real zero stays distinct from missing profit, ROE and growth',()=>{
  const html=render({data});
  assert.match(html,/Reported source/);assert.match(html,/financial mt-2 break-words text-lg font-semibold">0</);
  assert.match(html,/Profit after tax/);assert.match(html,/ROE/);assert.match(html,/financial mt-2 break-words text-lg font-semibold">—</);
  assert.doesNotMatch(html,/>0%<|>0 VND<\/td>/);
  assert.match(render({},'vi'),/Chưa có số liệu tài chính/);
});
test('financial institutions have limited coverage without generic revenue or margin metrics',()=>{
  const limited={...data,financial_identity_guard:true,rows:[{...row,revenue:null,net_profit:12}]};
  const html=render({data:limited},'en','ratios');
  assert.match(html,/Financial issuer metrics/);assert.doesNotMatch(html,/<th[^>]*>Revenue|<th[^>]*>Gross Margin|<th[^>]*>Net Margin/);
  assert.match(html,/Valuation, NIM, NPL and CASA/);
});
test('missing source statement tables remain unavailable without fabricated rows',()=>{
  for(const kind of ['income','balance','cash']){const empty=render({data},'en','statements',kind);assert.match(empty,/unavailable for the selected periods/);assert.doesNotMatch(empty,/class="fundamental-table/);}
});
test('unknown consolidation stays disclosed and unsupported quarterly controls are disabled',()=>{
  const html=render({data},'vi');
  assert.match(html,/Theo quý/);assert.match(html,/disabled=""/);assert.match(html,/Chưa có thông tin báo cáo hợp nhất/);assert.match(html,/không phải thời điểm công bố/);
});
