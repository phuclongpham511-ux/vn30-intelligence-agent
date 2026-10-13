import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
const require=createRequire(import.meta.url);
const exports={};
const compiled=transformSync(readFileSync(new URL('../app/components/stock/FundamentalTrends.tsx',import.meta.url),'utf8'),{filename:'FundamentalTrends.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
new Function('require','exports',compiled)(name=>name==='../ui/button'?{Button:({variant,...props})=>React.createElement('button',props)}:name==='../ui/skeleton'?{Skeleton:props=>React.createElement('div',props)}:require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
const row={ticker:'ABC',period:'2025',source:'Reported source',currency:'VND',revenue:0,net_profit:null,gross_margin:null,net_margin:null,roe:null,revenue_growth_yoy:null,net_profit_growth_yoy:null};
const render=(props={},language='en')=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(exports.FundamentalTrendsView,{rows:[],loading:false,error:false,retry(){},...props})));
test('financial empty, loading and provider failure do not fabricate zero metrics',()=>{
  assert.match(render(),/No annual financial observations/);
  assert.match(render({loading:true}),/Loading annual financial history/);
  assert.match(render({error:true}),/temporarily unavailable/);
  assert.doesNotMatch(render({error:true}),/No annual financial observations|0 VND/);
});
test('reported real zero stays distinct from missing profit, ROE and growth',()=>{
  const html=render({rows:[row]});
  assert.match(html,/Reported source/);assert.match(html,/0 <span[^>]*>VND/);
  assert.match(html,/Net Profit data is unavailable/);assert.match(html,/ROE is unavailable/);
  assert.doesNotMatch(html,/>0%<|>0 VND<\/td>/);
  assert.match(render({},'vi'),/chưa có dữ liệu tài chính năm/);
});
