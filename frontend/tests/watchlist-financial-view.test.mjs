import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {createRequire} from 'node:module';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
import {emptyWatchlist,followStock} from '../lib/watchlist.ts';
const require=createRequire(import.meta.url), exports={};
const code=transformSync(readFileSync(new URL('../app/components/WatchlistFinancial.tsx',import.meta.url),'utf8'),{filename:'WatchlistFinancial.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
new Function('require','exports',code)(id=>require(id.startsWith('@/lib/')?'../lib/'+id.slice(6)+'.ts':id),exports);
const render=(page,lang='en')=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(lang),setLanguage(){}}},React.createElement(exports.default,{page,symbol:'ABC',state:followStock(emptyWatchlist(),'ABC'),disabled:false,review(){}})));
test('private financial change shows periods, canonical numbers, criteria, limitations and evidence in both locales',()=>{
 const page={status:'READY',reasons:[],items:[{id:'financial:a',kind:'financial',revision:'one',evidence:{source:'issuer:synthetic',limitations:['Private synthetic evidence'],capture_id:'test',insight:{metric:'revenue',current_period:'2025',comparison_period:'2024',current_value:1000,comparison_value:800,absolute_change:200,percentage_change:.25,unit:'VND',missing_information:['public_display_permission'],attention_reason:{criteria:['RELATIVE_MOVEMENT'],thresholds:{relative_movement:.2}},evidence_references:[{source_url:'https://example.test/report.pdf',page:1}]}}}]};
 for(const lang of ['en','vi']){
  const html=render(page,lang);
  for(const text of ['2025','2024','25%','20%','VND','RELATIVE_MOVEMENT','public_display_permission','https://example.test/report.pdf'])assert.ok(html.includes(text),text);
  assert.match(html,/data-review-financial/);
 }
 assert.match(render(page,'vi'),/Thay đổi tài chính/);
});
test('insufficient, missing and unreadable evidence never masquerade as no change',()=>{
 for(const status of ['INSUFFICIENT_COMPARISON','MISSING_DATA','UNAVAILABLE','NOT_CHECKED']){
  const html=render({status,items:[],reasons:['synthetic_reason']});
  assert.ok(html.includes('synthetic_reason'));
  assert.doesNotMatch(html,/No eligible noteworthy annual revenue change/);
 }
});

test('qualified profile explains historical evidence and distinguishes quiet metrics from withheld ones',()=>{
 const page={profile:'qualified-v58',status:'READY',items:[],reasons:[],checks:[
  {metric:'revenue',status:'READY',current_period:'2024',comparison_period:'2023',noteworthy:false,reasons:[]},
  {metric:'net_profit',status:'INSUFFICIENT_COMPARISON',current_period:'2024',comparison_period:'2023',noteworthy:false,reasons:['unverified_reporting_scope']}]};
 const en=render(page),vi=render(page,'vi');
 assert.match(en,/Historical evidence, not new filings/);
 assert.match(en,/Comparable, below the existing attention rule/);
 assert.match(en,/unverified_reporting_scope/);
 assert.match(vi,/bằng chứng lịch sử/);
 assert.match(vi,/Lợi nhuận sau thuế/);
 assert.doesNotMatch(en,/Saved annual revenue only/);
});
