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
function render(items=[],options={},language='en',ticker='ABC') {
  state={data:{ticker,coverage:'INCOMPLETE',as_of:'2026-10-12T11:00:00Z',items,has_more:false},error:false,retry(){},...options};
  return renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(exports.default,{ticker})));
}
test('actual action renderer preserves original dates, units and source evidence; no inferred ex-rights',()=>{
  const html=render([row]);
  assert.match(html,/20 Oct 2026/);assert.match(html,/1 Nov 2026/);
  assert.match(html,/1,500 VND/);assert.match(html,/Ex-rights date/);assert.match(html,/<dd>Unavailable<\/dd>/);
  assert.doesNotMatch(html,/19 Oct 2026/);
  assert.match(html,/Preserved source wording/);assert.match(html,/href="https:\/\/vsdc.vn\/original.pdf"/);
  assert.match(html,/Incomplete coverage/);assert.match(html,/Source-marked verified/);
  assert.equal((html.match(/data-action-observation=/g)||[]).length,1);
  assert.equal((html.match(/Preserved source wording/g)||[]).length,1,'one record keeps its source evidence, without a duplicate timeline');
  assert.match(html,/payment date does not confirm payment/);
});
test('pending corrections, withdrawals and fixtures withhold trusted dates and terms but keep evidence',()=>{
  for(const change of [{verified:false},{withdrawn:true},{is_fixture:true}]) {
    const html=render([{...row,...change}]);
    assert.doesNotMatch(html,/1,500 VND|20 Oct 2026|1 Nov 2026/);
    assert.match(html,/Preserved source wording/);
  }
  const pendingFixture=render([{...row,verified:false,is_fixture:true}]);
  assert.match(pendingFixture,/Pending verification/);assert.match(pendingFixture,/Fixture observation/);
  assert.match(pendingFixture,/DEMO/);assert.match(pendingFixture,/Synthetic source fixture/);
});
test('empty, failed and wrong-ticker responses are distinct; Vietnamese chrome preserves source text',()=>{
  assert.match(render(),/No recorded corporate actions for ABC/);
  assert.match(render(),/does not establish that no corporate action occurred/);
  const failed=render([],{error:true});assert.match(failed,/temporarily unavailable/);assert.doesNotMatch(failed,/No recorded corporate actions/);
  assert.doesNotMatch(render([],{data:{ticker:'OTHER',items:[row]}}),/Original issuer evidence/);
  const vi=render([row],{},'vi');assert.match(vi,/Ngày đăng ký cuối cùng/);assert.match(vi,/Original issuer evidence/);assert.match(vi,/1.500 VND/);
});
test('mixed instrument observations fail closed even if the page ticker is correct',()=>{
 const html=render([row,{...row,observation_id:'foreign',symbol:'OTHER'}]);
 assert.match(html,/temporarily unavailable/);assert.doesNotMatch(html,/1,500 VND|Original issuer evidence/);
});
test('real zero and small source share ratios never become missing or a fabricated zero',()=>{
 assert.match(render([{...row,terms:{cash_vnd_per_share:0}}]),/>0 VND</);
 const html=render([{...row,action_type:'stock_dividend',terms:{new_shares_per_old:1e-25}}]);
 assert.match(html,/>1e-25 \/ 1</);assert.doesNotMatch(html,/>0 \/ 1</);
});
test('filtered history reuses compact records and renders only supported terms for each type',()=>{
 const items=['cash_dividend','stock_dividend','bonus_shares','rights_offering','additional_issuance'].map((action_type,i)=>({...row,action_type,observation_id:String(i),terms:{cash_vnd_per_share:1500,new_shares_per_old:.1,subscription_price_vnd:12000}}));
 const renderView=category=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools('en')},React.createElement(exports.StockActionsView,{ticker:'ABC',data:{ticker:'ABC',items,as_of:'2026-10-12T11:00:00Z',coverage:'INCOMPLETE',has_more:false},retry(){},category})));
 const distributions=renderView('distributions'),other=renderView('other');
 assert.equal((distributions.match(/data-action-observation=/g)||[]).length,3);assert.match(distributions,/3 of 5 recorded observations/);
 assert.match(distributions,/0.1 \/ 1/);assert.doesNotMatch(distributions,/12,000 VND|Rights offering/);
 assert.equal((other.match(/data-action-observation=/g)||[]).length,2);assert.match(other,/12,000 VND/);assert.doesNotMatch(other,/1,500 VND/);
});
test('an empty filtered category is not misreported as an empty corporate-action history',()=>{
 const html=renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools('en')},React.createElement(exports.StockActionsView,{ticker:'ABC',data:{ticker:'ABC',items:[row],as_of:'2026-10-12T11:00:00Z',coverage:'INCOMPLETE',has_more:false},retry(){},category:'other'})));
 assert.match(html,/0 of 1 recorded observations/);assert.match(html,/No recorded observations in this category/);
 assert.doesNotMatch(html,/No recorded corporate actions for|data-action-observation=/);
});

test('secondary source and publication receipts are never relabeled as original issuer evidence',()=>{
 const html=render([{...row,source:'Broker event calendar',announced_on:'2026-10-10'}]);
 assert.match(html,/Recorded source link/);assert.doesNotMatch(html,/>Original source document/);
 assert.match(html,/Recorded announcement \/ publication date/);
 assert.match(html,/Source-marked verified/);
 assert.match(html,/Record-level verification does not establish original-publication verification of every fact/);
});

test('incomplete source-marked records are visibly incomplete in EN and VI',()=>{
 assert.match(render([row]),/Incomplete event details/);
 assert.match(render([row],{},'vi'),/Thông tin sự kiện chưa đầy đủ/);
 const complete={...row,effective_date:'2026-10-19'};
 assert.doesNotMatch(render([complete]),/Incomplete event details/);
 assert.match(render([{...complete,terms:null}]),/Incomplete event details/);
});

test('an unresolved correction overrides a retained verified flag and withholds event facts',()=>{
 const html=render([{...row,verification_note:'Unresolved correction: conflicting payment date',verified:true}]);
 assert.match(html,/Unresolved correction/);assert.match(html,/conflicting payment date/);
 assert.doesNotMatch(html,/1,500 VND|20 Oct 2026|1 Nov 2026|Source-marked verified/);
 assert.match(html,/data-action-status="unqualified"/);
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

test('date guide and source version distinguish entitlements from confirmed outcomes in EN/VI',()=>{
 for(const language of ['en','vi']){
  const html=render([{...row,payment_date:'2020-01-01'}],{},language);
  for(const label of ['Understanding your entitlements','Announced payment date','Latest stored version','Earlier revisions are not included in this view.','Payment completion is not verified.'])assert.ok(html.includes(localeTools(language).t(label)),label);
  assert.match(html,/data-action-version/);assert.match(html,/revision-2/);
  assert.doesNotMatch(html,/data-payment-status="paid"/);
 }
});

test('withdrawal and unresolved revision explain why terms are withheld without inventing a revision history',()=>{
 for(const [patch,message] of [[{withdrawn:true},'This notice was withdrawn; do not use it to establish an entitlement.'],[{verification_note:'Unresolved correction: conflicting terms'},'A correction remains unresolved; dates and terms are withheld.']]){
  const html=render([{...row,...patch}]);assert.ok(html.includes(message));assert.doesNotMatch(html,/1,500 VND/);assert.match(html,/Preserved source wording/);
 }
 const html=render([{...row,source_revision:null,announced_on:null,announced_at:null}]);
 assert.match(html,/Latest stored version/);assert.doesNotMatch(html,/Revision 1|First version/);
});
