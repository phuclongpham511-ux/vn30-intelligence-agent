// Synthetic contracts only. No browser or provider acquisition.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
import {fixture} from './fixtures/fundamental-summary.mjs';
import {financialEngineData} from '../lib/financial-engine-data.ts';
import {selectFinancialPanel,financialSourceLink,validateFinancialPanels} from '../lib/financial-panels.ts';
import {statementHierarchy} from '../lib/financial-statement-rows.ts';
const require=createRequire(import.meta.url);
function load(name){const exports={};const compiled=transformSync(readFileSync(new URL(`../app/components/stock/${name}.tsx`,import.meta.url),'utf8'),{filename:`${name}.tsx`,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;new Function('require','exports',compiled)(id=>require(id.startsWith('@/lib/')?`../lib/${id.slice(6)}.ts`:id),exports);return exports.default;}
const Panel=load('FinancialAnalysisPanel'),Table=load('FinancialStatementTable'),ResearchChart=load('FinancialResearchCharts');
function example(){
 const data=fixture();data.rows[0].total_liabilities=70;data.rows[0].equity=30;data.rows[0].liabilities_assets=.7;
 data.research_panels=[{key:'funding',title:'Funding composition',chart:'stacked',source:data.source,frequency:'annual',status:'QUALIFIED',partial:false,methodology:'Components only',reasons:[],series:[{key:'total_liabilities',label:'Total liabilities',unit:'VND'},{key:'equity',label:'Total equity',unit:'VND'},{key:'liabilities_assets',label:'Liabilities / assets',unit:'fraction'}],rows:[{period:'2025',values:{total_liabilities:70,equity:30,liabilities_assets:.7},statuses:{total_liabilities:'QUALIFIED',equity:'QUALIFIED',liabilities_assets:'QUALIFIED'},bases:{total_liabilities:'consolidated',equity:'consolidated',liabilities_assets:'consolidated'}}]}];return data;
}
function render(Component,props,language='en'){return renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools(language)},React.createElement(Component,props)));}

test('server chart values must match their displayed period and qualified inputs',()=>{
 assert.doesNotThrow(()=>financialEngineData(example(),'ABC','annual',true));
 for(const mutate of [d=>d.research_panels[0].source='OTHER',d=>d.research_panels[0].rows[0].period='2024',d=>d.research_panels[0].rows[0].values.equity=31,d=>d.research_panels[0].series[0].unit='multiple',d=>d.research_panels[0].rows[0].statuses.equity='UNQUALIFIED',d=>d.research_panels[0].rows[0].bases.equity='standalone',d=>d.research_panels[0].rows[0].bases.liabilities_assets='standalone',d=>d.research_panels[0].status='DEMO']){
  const data=example();mutate(data);assert.throws(()=>financialEngineData(data,'ABC','annual',true));
 }
});

test('personal VCI hierarchy panels preserve sibling values and never mix public data',()=>{
 const line=(code,parent,value)=>({code,name_en:code,name_vi:code,parent,unit:'VND',value,raw_value:value,semantic_status:'reported'});
 const data={display_scope:'personal_research',access_classification:'PERSONAL_RESEARCH',source:'vnstock:VCI',period_type:'annual',is_fixture:false,
  chart_rows:[{period:'2025'}],statements:{balance:{periods:[{period:'2025',basis:'point_in_time',items:[line('bsa900',null,100),line('bsa901','BSA900',60),line('bsa902','BSA900',40),line('bsa903',null,55),line('bsa904',null,45)]}]}},
  research_panels:[{key:'components:balance:bsa900',title:'Reported components · Total',statement:'balance',parent_code:'bsa900',component_scope:'reported_parent',chart:'stacked',source:'vnstock:VCI',frequency:'annual',status:'SOURCE_REPORTED',partial:true,methodology:'Sibling source lines; no derived total.',reasons:[],
   series:[{key:'bsa901',label:'Cash',unit:'VND'},{key:'bsa902',label:'Other',unit:'VND'}],rows:[{period:'2025',statement_basis:'point_in_time',values:{bsa901:60,bsa902:40},statuses:{bsa901:'SOURCE_REPORTED',bsa902:'SOURCE_REPORTED'},bases:{bsa901:null,bsa902:null}}]},
   {key:'components:balance:root',title:'Top-level balance lines',statement:'balance',component_scope:'unparented_lines',chart:'performance',source:'vnstock:VCI',frequency:'annual',status:'SOURCE_REPORTED',partial:true,methodology:'Independent unparented source lines.',reasons:[],series:[{key:'bsa903',label:'Current assets',unit:'VND'},{key:'bsa904',label:'Other assets',unit:'VND'}],rows:[{period:'2025',statement_basis:'point_in_time',values:{bsa903:55,bsa904:45},statuses:{bsa903:'SOURCE_REPORTED',bsa904:'SOURCE_REPORTED'},bases:{bsa903:null,bsa904:null}}]}]};
 assert.doesNotThrow(()=>validateFinancialPanels(data));
 const selected=selectFinancialPanel(data,'components:balance:bsa900',['2025']);
 assert.equal(selected.title,'Reported components · Total');
 const componentHtml=render(Panel,{kind:'components:balance:bsa900',panel:selected,unit:'billions',personalResearch:true});
 assert.match(componentHtml,/data-financial-chart="stacked"/);assert.match(componentHtml,/Cash/);assert.match(componentHtml,/SOURCE_REPORTED/);
 assert.doesNotThrow(()=>selectFinancialPanel(data,'components:balance:root',['2025']));
 const bad=structuredClone(data);bad.display_scope='public';assert.throws(()=>validateFinancialPanels(bad),/hierarchy/);
 const wrongParent=structuredClone(data);wrongParent.research_panels[0].series[1].key='bsa901';assert.throws(()=>validateFinancialPanels(wrongParent),/series|keys/);
 const wrongValue=structuredClone(data);wrongValue.research_panels[0].rows[0].values.bsa902=41;assert.throws(()=>validateFinancialPanels(wrongValue),/source line/);
});

test('valuation, negative compositions and annual-labelled quarterly values fail closed',()=>{
 const negative=example();negative.rows[0].equity=-30;negative.research_panels[0].rows[0].values.equity=-30;
 assert.throws(()=>financialEngineData(negative,'ABC','annual',true),/composition/);
 const valuation=example();valuation.research_panels[0]={...valuation.research_panels[0],key:'pe',chart:'unavailable',series:[{key:'pe',label:'P/E',unit:'multiple'}],rows:[{period:'2025',values:{pe:10},statuses:{pe:'QUALIFIED'},bases:{pe:'consolidated'}}]};
 assert.throws(()=>financialEngineData(valuation,'ABC','annual',true));
 const annual=example();annual.research_panels[0]={...annual.research_panels[0],key:'quarterly',chart:'performance',series:[{key:'net_profit',label:'Profit after tax',unit:'VND'}],rows:[{period:'2025',values:{net_profit:0},statuses:{net_profit:'QUALIFIED'},bases:{net_profit:'consolidated'}}]};
 assert.throws(()=>financialEngineData(annual,'ABC','annual',true),/Unsupported/);
});

test('period filtering recalculates coverage status without promoting previous qualified data',()=>{
 const data=example(),panel=data.research_panels[0];panel.rows.push({period:'2026',values:{total_liabilities:null,equity:null,liabilities_assets:null},statuses:{total_liabilities:'UNQUALIFIED',equity:'UNQUALIFIED',liabilities_assets:'UNQUALIFIED'},bases:{total_liabilities:null,equity:null,liabilities_assets:null}});
 assert.equal(selectFinancialPanel(data,'funding',['2026']).status,'UNQUALIFIED');
 assert.equal(selectFinancialPanel(data,'funding',['2025']).status,'QUALIFIED');
 assert.equal(selectFinancialPanel(data,'pe',['2025']),undefined);
});

test('explicit shells explain unavailable PE/PB and unknown data in EN/VI without fake chart paths',()=>{
 const html=render(Panel,{kind:'pe',unit:'billions'});
 assert.match(html,/P\/E history/);assert.match(html,/Multiple/);assert.match(html,/UNAVAILABLE/);
 assert.doesNotMatch(html,/data-financial-chart=|VND bn/);
 assert.match(render(Panel,{kind:'assets',unit:'millions'},'vi'),/Cơ cấu tài sản/);
});

test('trend chart keeps amount and rate presentations distinct with keyboard-operable series controls',()=>{
 const rows=fixture().rows;
 rows[0].revenue=2_400_000_000;rows[0].net_profit=340_000_000;rows[0].net_margin=.14;
 const amount=render(ResearchChart,{rows,fields:['revenue','net_profit'],title:'Revenue and profit',unit:'billions'});
 const rate=render(ResearchChart,{rows,fields:['net_margin'],title:'Profitability',percentage:true,unit:'billions'});
 assert.match(amount,/data-financial-chart="amount"/);assert.match(amount,/VND bn/);
 assert.match(amount,/role="group" aria-label="Chart series"/);assert.match(amount,/aria-pressed="true"/);
 assert.match(amount,/Revenue/);assert.match(amount,/Profit after tax/);
 assert.match(rate,/data-financial-chart="percent"/);assert.match(rate,/Net Margin/);assert.match(rate,/· %/);
 assert.match(amount,/min-h-7/);assert.match(rate,/financial-research-chart-canvas/);
});

test('defensive renderer withholds malformed unqualified or DEMO points from observations too',()=>{
 const panel=example().research_panels[0];
 for(const point of panel.rows){for(const key of Object.keys(point.values)){point.values[key]=987654321;point.statuses[key]='UNQUALIFIED';}}
 panel.status='UNQUALIFIED';
 const html=render(Panel,{kind:'funding',panel,unit:'vnd'});
 assert.doesNotMatch(html,/987,654,321/);assert.match(html,/Inputs exist/);
 for(const key of Object.keys(panel.rows[0].values))panel.rows[0].statuses[key]='DEMO';
 assert.doesNotMatch(render(Panel,{kind:'funding',panel,unit:'vnd',isFixture:false}),/987,654,321/);
 assert.match(render(Panel,{kind:'funding',panel,unit:'vnd',isFixture:true}),/987,654,321/);
});

test('statement grouping follows actual source parents, supports collapse and tolerates cycles',()=>{
 const line=(code,parent=null)=>({code,parent,name_en:code,name_vi:code,unit:'VND',value:0,raw_value:0,semantic_status:'reported'});
 const periods=[{period:'2025',basis:'annual',consolidation:null,items:[line('bsa1'),line('bsa2','BSA1'),line('bsa3','BSA2'),line('unmapped','Source heading')]}];
 assert.equal(statementHierarchy(periods,new Set())[2].depth,2);
 assert.deepEqual(statementHierarchy(periods,new Set(['bsa1'])).filter(x=>!x.hidden).map(x=>x.line.code),['bsa1','unmapped']);
 const cycle=[{...periods[0],items:[line('a','b'),line('b','a')]}];
 assert.ok(statementHierarchy(cycle,new Set(['a','b'])).every(x=>!x.hidden&&!x.expandable));
 const conflicted=[{...periods[0],items:[{...line('a'),semantic_status:'conflicted'},line('b','a')]}];
 assert.ok(statementHierarchy(conflicted,new Set(['a'])).every(x=>!x.hidden&&!x.expandable));
 const html=render(Table,{periods,unit:'vnd',label:'Balance sheet'});
 assert.match(html,/aria-expanded="true"/);assert.match(html,/financial-statement-group/);assert.match(html,/scope="col"/);assert.match(html,/<td>0<\/td>/);
});

test('source evidence links reject unsafe protocols and embedded credentials',()=>{
 assert.equal(financialSourceLink('https://example.test/statements?section=INCOME_STATEMENT'),'https://example.test/statements?section=INCOME_STATEMENT');
 for(const value of ['javascript:alert(1)','data:text/plain,x','file:///C:/private','https://user:secret@example.test/','not a URL'])assert.equal(financialSourceLink(value),undefined);
});
