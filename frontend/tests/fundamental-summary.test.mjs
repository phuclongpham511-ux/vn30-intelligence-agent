import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
import {FINANCIAL_LABELS} from '../lib/fundamental-data.ts';
import {financialEngineData} from '../lib/financial-engine-data.ts';
const require=createRequire(import.meta.url),exports={};
const code=transformSync(readFileSync(new URL('../app/components/stock/FundamentalTrends.tsx',import.meta.url),'utf8'),{filename:'FundamentalTrends.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
new Function('require','exports',code)(name=>['./FinancialStatementTable','./FinancialResearchCharts','./FinancialAnalysisPanel','../ui/button','../ui/skeleton'].includes(name)?{}:require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);

import {fixture} from './fixtures/fundamental-summary.mjs';
test('missing or malformed reporting frequency metadata is rejected before the view can dereference it',()=>{
 for(const available_period_types of [undefined,null,'annual',{},['unrecognized'],[null]])assert.throws(()=>financialEngineData({...fixture(),available_period_types},'ABC','annual',true),/frequency metadata/);
});
function render(data=fixture(),unit='billions',language='en'){
 return renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools(language)},React.createElement(exports.FundamentalOverview,{data,unit})));
}
test('compact four-part snapshot preserves VND, per-share and fractional units independently',()=>{
 const html=render();
 for(const label of ['Valuation','Business performance','Profitability','Financial health','1,500 VND/share','1.2 VND bn','0 VND bn','12.5%'])assert.ok(html.includes(label),label);
 assert.match(render(fixture(),'millions'),/1,200 VND mn/);
 assert.match(render(fixture(),'vnd'),/1,200,000,000 VND/);
 assert.match(html,/Reported EPS is not a valuation ratio/);assert.doesNotMatch(html,/1500×|1,500 VND bn/);
 assert.match(render(fixture(),'billions','vi'),/Định giá|Sức khỏe tài chính/);
});
test('current client requires display qualification and rejects mismatched periods, units and values',()=>{
 assert.doesNotThrow(()=>financialEngineData(fixture(),'ABC','annual',true));
 assert.throws(()=>financialEngineData({...fixture(),fundamental_summary:null},'ABC','annual',true));
 for(const mutate of [d=>d.fundamental_summary.period='2024',d=>d.fundamental_summary.frequency='quarterly',d=>d.fundamental_summary.metrics[0].unit='VND',d=>d.fundamental_summary.metrics[0].value=500,d=>d.fundamental_summary.metrics[1].value=10]){
  const data=fixture();mutate(data);assert.throws(()=>financialEngineData(data,'ABC','annual',true));
 }
});
test('unqualified data, consolidation conflicts and DEMO cannot masquerade as live qualified values',()=>{
 for(const mutate of [d=>d.fundamental_summary.metrics[0].status='UNQUALIFIED',d=>d.fundamental_summary.consolidation=null,d=>d.fundamental_summary.consolidation='conflicting',d=>d.fundamental_summary.metrics[0].status='DEMO',d=>d.is_fixture=true]){
  const data=fixture();mutate(data);assert.throws(()=>financialEngineData(data,'ABC','annual',true));
 }
 const data=fixture();data.fundamental_summary.metrics[0].status='UNQUALIFIED';
 assert.doesNotMatch(render(data),/1,500 VND\/share/,'renderer also withholds a malformed unqualified value');
});
test('explicit DEMO contract is rendered and never upgraded to QUALIFIED',()=>{
 const data=fixture();data.is_fixture=true;data.rows[0].is_fixture=true;data.fundamental_summary.consolidation=null;
 for(const item of data.fundamental_summary.metrics)if(item.value!==null)item.status='DEMO';
 assert.doesNotThrow(()=>financialEngineData(data,'ABC','annual',true));
 const html=render(data);assert.match(html,/DEMO/);assert.match(html,/1,500 VND\/share/);assert.doesNotMatch(html,/data-financial-qualification="QUALIFIED"/);
});
test('missing and unqualified fields remain separate, with definitions and no fabricated valuation',()=>{
 const data=fixture();data.fundamental_summary.metrics[0]={...data.fundamental_summary.metrics[0],value:null,status:'UNQUALIFIED',reason:'Reporting basis is not qualified'};
 const html=render(data);
 assert.match(html,/UNAVAILABLE/);assert.match(html,/UNQUALIFIED/);assert.match(html,/Reporting basis is not qualified/);assert.match(html,/reported source field/);
 assert.doesNotMatch(html,/1,500 VND\/share|0×/);
});
test('standalone consolidation is separate reporting, never a standalone-quarter label',()=>{
 const data=fixture();data.fundamental_summary.consolidation='standalone';
 assert.match(render(data,'billions','vi'),/Báo cáo riêng/);
 assert.doesNotMatch(render(data,'billions','vi'),/Riêng quý/);
});

test('field-owned consolidation supports independent qualified metrics without certifying mixed-basis ratios',()=>{
 const data=fixture();data.fundamental_summary.consolidation=null;
 for(const item of data.fundamental_summary.metrics)if(item.status==='QUALIFIED')item.consolidation='consolidated';
 assert.doesNotThrow(()=>financialEngineData(data,'ABC','annual',true));
 assert.match(render(data),/1,500 VND\/share/);
 data.fundamental_summary.metrics[0].consolidation=null;
 assert.throws(()=>financialEngineData(data,'ABC','annual',true),/qualification/);
 assert.doesNotMatch(render(data),/1,500 VND\/share/);
});
