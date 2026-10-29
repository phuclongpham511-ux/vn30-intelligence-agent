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
let state;
const compiled=transformSync(readFileSync(new URL('../app/components/stock/StockActions.tsx',import.meta.url),'utf8'),{filename:'StockActions.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
new Function('require','exports',compiled)(name=>name==='./useStockRead'?{useStockRead:()=>state}:name==='../ui/button'?{Button:({variant,...props})=>React.createElement('button',props)}:require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
const row={symbol:'ABC',action_id:'action',observation_id:'revision-2',observed_at:'2026-10-12T10:00:00Z',action_type:'cash_dividend',effective_date:null,record_date:'2026-10-20',payment_date:'2026-11-01',announced_at:null,announced_on:'2026-10-10',source:'VSDC',source_url:'https://vsdc.vn/notice',supporting_urls:['https://vsdc.vn/original.pdf'],source_title:'Original issuer evidence',evidence_text:'Preserved source wording',source_revision:'2',verified:true,withdrawn:false,is_fixture:false,terms:{cash_vnd_per_share:1500,new_shares_per_old:null,subscription_price_vnd:null}};
function render(items=[],options={},language='en',ticker='ABC',personalResearch=false) {
  state={data:{ticker,coverage:'INCOMPLETE',as_of:'2026-10-12T11:00:00Z',items,has_more:false},error:false,retry(){},...options};
  return renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(exports.default,{ticker,personalResearch})));
}

test('investor view keeps benefits and dates while hiding internal evidence in EN/VI',()=>{
 for(const language of ['en','vi']){
  const before=JSON.stringify(row),html=render([row],{},language),t=localeTools(language).t;
  for(const key of ['Cash per share','Ex-rights date','Record date','Announced payment date'])assert.ok(html.includes(t(key)));
  assert.match(html,language==='vi'?/1.500 VND/:/1,500 VND/);
  for(const value of ['VSDC','revision-2','2026-10-12','2026-10-10','Original issuer evidence','Preserved source wording','https://vsdc.vn',t('Latest stored version'),t('Read at'),t('Stored source records'),t('Source-marked verified')])assert.ok(!html.includes(value),value);
  assert.match(html,/<dd>Unavailable<\/dd>|<dd>Chưa có dữ liệu<\/dd>/);
  assert.equal(JSON.stringify(row),before);
 }
});
test('past payment dates never create a paid outcome',()=>{
 const html=render([{...row,payment_date:'2020-01-01'}]);
 assert.match(html,/1 Jan 2020/);assert.match(html,/not confirmation of payment/);assert.doesNotMatch(html,/>Paid<|data-payment-status/);
});
test('cancelled revised unverified and DEMO events retain the existing date and term gates',()=>{
 for(const [patch,status] of [[{withdrawn:true},'Cancelled'],[{verification_note:'Unresolved correction: private diagnostic'},'Under revision'],[{verified:false},'Incomplete event details'],[{is_fixture:true},'DEMO']]){
  const html=render([{...row,...patch}]);assert.ok(html.includes(status));assert.doesNotMatch(html,/1,500 VND|20 Oct 2026|1 Nov 2026|private diagnostic/);
 }
 const complete=render([{...row,effective_date:'2026-10-19'}]);assert.doesNotMatch(complete,/Incomplete event details|Under revision|Cancelled/);
});
test('empty loading error and wrong identity remain distinct in the simplified view',()=>{
 assert.match(render(),/No event information for ABC/);assert.match(render(),/No information does not mean no entitlement/);
 assert.match(render([],{data:null}),/Loading events/);
 assert.match(render([],{error:true}),/temporarily unavailable/);
 assert.doesNotMatch(render([],{data:{ticker:'OTHER',items:[row]}}),/1,500 VND/);
 assert.doesNotMatch(render([row,{...row,symbol:'OTHER'}]),/1,500 VND/);
});
test('private payload gate and real zero or tiny ratios are unchanged',()=>{
 const data={ticker:'ABC',items:[row],coverage:'INCOMPLETE',has_more:false,display_scope:'personal_research',public_display_eligible:false};
 assert.doesNotMatch(render([],{data}),/1,500 VND/);
 const privateView=renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools('en')},React.createElement(exports.StockActionsView,{ticker:'ABC',data,retry(){},allowPersonal:true})));
 assert.match(privateView,/1,500 VND/);
 assert.match(render([{...row,terms:{cash_vnd_per_share:0}}]),/>0 VND</);
 assert.match(render([{...row,action_type:'stock_dividend',terms:{new_shares_per_old:1e-25}}]),/>1e-25 \/ 1</);
});
test('event filter keeps instrument-specific terms and a clean empty category',()=>{
 const items=['cash_dividend','rights_offering'].map((action_type,i)=>({...row,action_type,observation_id:String(i),terms:{cash_vnd_per_share:1500,new_shares_per_old:.1,subscription_price_vnd:12000}}));
 const view=(items,category)=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools('en')},React.createElement(exports.StockActionsView,{ticker:'ABC',data:{ticker:'ABC',items,has_more:false},retry(){},category})));
 const html=view(items,'other');assert.match(html,/12,000 VND/);assert.doesNotMatch(html,/1,500 VND/);
 assert.match(view([row],'other'),/No events in this category/);
});

// These are saved real notice facts with simulated API receipts, not live ingestion.
const curated=JSON.parse(readFileSync(new URL('../../data/corporate_actions/verified_v1.json',import.meta.url),'utf8')).notices;
function renderSaved(component) {
 const saved=curated.find(item=>item.component_id===component);
 return render([{...row,effective_date:null,record_date:null,payment_date:null,terms:null,source_title:null,evidence_text:null,supporting_urls:[],...saved}],{},'en',saved.symbol);
}
test('reviewed VNM cash payment never leaks into the separate bonus-share component',()=>{
 const cash=renderSaved('VNM-2020-cash'),bonus=renderSaved('VNM-2020-bonus');
 assert.match(cash,/2,000 VND/);assert.match(cash,/15 Oct 2020/);
 assert.match(bonus,/0.2 \/ 1/);assert.doesNotMatch(bonus,/2,000 VND|15 Oct 2020/);
 assert.match(bonus,/Incomplete event details/);
});
test('reviewed SSI rights preserve 0.5 new shares per old and VND price without a sibling cash payment',()=>{
 const html=renderSaved('SSI-2022-rights');
 assert.match(html,/0.5 \/ 1/);assert.match(html,/15,000 VND/);assert.match(html,/23 Jun 2022/);
 assert.doesNotMatch(html,/1,000 VND|20 Jul 2022/);assert.match(html,/Incomplete event details/);
});
test('reviewed HFC registration cannot promote custody dates, aggregate shares or par value into entitlement facts',()=>{
 const html=renderSaved('HFC-2023-additional-registration');
 assert.match(html,/Incomplete event details/);
 assert.doesNotMatch(html,/26 Sept 2023|2,000,000 \/ 1|10,000 VND/);
 assert.equal((html.match(/<dd>Unavailable<\/dd>/g)||[]).length,3);
});
