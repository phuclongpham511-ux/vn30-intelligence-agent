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
const require=createRequire(import.meta.url);
let section='overview',statement='income';
const react={...React,useState(initial){if(initial==='overview')return [section,()=>{}];if(initial==='income')return [statement,()=>{}];return React.useState(initial);}};
function load(file){
 const exports={};
 const compiled=transformSync(readFileSync(new URL(`../app/components/stock/${file}.tsx`,import.meta.url),'utf8'),{filename:`${file}.tsx`,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 new Function('require','exports',compiled)(name=>name==='react'?react:name==='./FinancialStatementTable'?load('FinancialStatementTable'):name==='./FinancialResearchCharts'?{__esModule:true,default:()=>null}:name==='../ui/button'?{Button:({variant,size,...props})=>React.createElement('button',props)}:name==='../ui/skeleton'?{Skeleton:props=>React.createElement('div',props)}:require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
 return exports;
}
const view=load('FundamentalTrends').FundamentalTrendsView;
const row=period=>({ticker:'ABC',period,frequency:period.includes('Q')?'quarterly':'annual',source:'Fixture:VCI',currency:'VND',...Object.fromEntries(Object.keys(FINANCIAL_LABELS).map(key=>[key,null])),revenue:0,net_profit:12,equity:80,roe:.15,calculations:{roe:{formula:'total profit / average total equity',inputs:[{code:'isa20',value:12}],reason:null}},is_fixture:true});
const data={data_engine:'financial-engine-v1',ticker:'ABC',source:'Fixture:VCI',currency:'VND',period_type:'annual',profile:'non_financial',financial_identity_guard:false,rows:[row('2025')],chart_rows:[row('2025')],changes:[],statements:{income:{status:'healthy',basis:'reported',periods:[{ticker:'ABC',source:'Fixture:VCI',currency:'VND',period:'2025',basis:'annual',consolidation:null,source_dates:{publicDate:'2026-02-01T00:00:00'},diagnostics:[],items:[{code:'isa3',name_en:'Net sales',name_vi:'Doanh thu thuần',parent:null,unit:'VND',value:0,raw_value:0,semantic_status:'reported'}]}]}},source_receipts:[],available_period_types:['annual','quarterly','ttm'],is_fixture:true,read_at:'2026-10-13T10:00:00Z',sector:null,industry:null};
function render(props={},language='en',tab='overview',kind='income'){
 section=tab;statement=kind;
 return renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(view,{data,loading:false,error:false,retry(){},...props})));
}
test('engine contract checks currency, ownership, period frequency and chart/source consistency',()=>{
 assert.equal(financialEngineData(data,'ABC','annual').rows[0].revenue,0);
 for(const mutation of [{currency:'USD'},{ticker:'OTHER'},{period_type:'quarterly'},{rows:[{...row('2025'),roe:Infinity}]},{chart_rows:[{...row('2025'),revenue:10}]},{statements:{income:{periods:[{...data.statements.income.periods[0],ticker:'OTHER'}]}}}])assert.throws(()=>financialEngineData({...data,...mutation},'ABC','annual'));
});
test('quarterly/TTM presentation accepts qualified periods without frontend financial calculations',()=>{
 const quarter={...data,period_type:'quarterly',rows:[row('2026-Q2')],chart_rows:[row('2026-Q2')],statements:{},changes:[]};
 assert.equal(financialEngineData(quarter,'ABC','quarterly').rows[0].net_profit,12);
 assert.match(render({data:quarter,frequency:'quarterly'}),/not annualized/);
 assert.match(render({data:{...quarter,period_type:'ttm'},frequency:'ttm'}),/four contiguous qualified quarters/);
});
test('existing four sections, frequency and units remain visible; source fixtures and missing values are honest',()=>{
 const html=render();
 for(const label of ['Financial overview','Business performance','Financial statements','Financial ratios','Annual','Quarterly','TTM','VND bn','Fixture data'])assert.match(html,new RegExp(label));
 assert.match(html,/ROE uses total profit/);assert.match(html,/Calculation evidence/);assert.match(html,/>0<\/dd>/);
 assert.match(render({},'vi'),/Bằng chứng tính toán/);assert.match(render({loading:true}),/Loading financial statements/);
 assert.match(render({error:true}),/temporarily unavailable/);assert.match(render({data:{...data,rows:[]}}),/No financial observations/);
});
test('source statement table preserves original labels, per-share units and unqualified conflict disclosure',()=>{
 const statement=data.statements.income.periods[0];
 const conflict={code:'cfa34',name_en:'Conflicting field',name_vi:'Nhãn mâu thuẫn',unit:'VND',value:null,raw_value:25,semantic_status:'conflicted',source_labels:[{en_name:'First label',name:'Nhãn 1',parent:'Group'},{en_name:'Second label',name:'Nhãn 2',parent:'Group'}]};
 const eps={code:'isa23',name_en:'EPS basic (VND)',name_vi:'EPS cơ bản',unit:'VND/share',value:1234,raw_value:1234,semantic_status:'reported'};
 const enriched={...data,statements:{income:{...data.statements.income,periods:[{...statement,items:[...statement.items,conflict,eps]}]}}};
 const html=render({data:enriched},'en','statements');
 assert.match(html,/Net sales/);assert.match(html,/<td>0<\/td>/);assert.match(html,/1,234/);assert.match(html,/VND\/share/);assert.match(html,/Unqualified raw amount/);assert.match(html,/First label/);
 assert.match(render({data:enriched},'vi','statements'),/Doanh thu thuần/);
 assert.match(render({},'en','statements','balance'),/unavailable for the selected periods/);
 assert.throws(()=>financialEngineData({...enriched,statements:{income:{periods:[{...statement,items:[{...conflict,value:25}]}]}}},'ABC','annual'));
});
test('bank rendering presents operating income, excludes generic revenue and liquidity, and keeps valuation unavailable',()=>{
 const bank={...data,profile:'bank',financial_identity_guard:true,rows:[{...row('2025'),revenue:null,operating_income:100,operating_income_growth_yoy:.1}],chart_rows:[{...row('2025'),revenue:null,operating_income:100,operating_income_growth_yoy:.1}],statements:{}};
 assert.doesNotThrow(()=>financialEngineData(bank,'ABC','annual'));
 assert.match(render({data:bank}),/Operating income/);
 const html=render({data:bank},'en','ratios');
 assert.doesNotMatch(html,/<th[^>]*>Revenue|<th[^>]*>Current ratio|<th[^>]*>Quick ratio/);
 assert.match(html,/Valuation, NIM, NPL and CASA/);
});
