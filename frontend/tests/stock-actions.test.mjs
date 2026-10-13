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
function render(items=[],options={},language='en') {
  state={data:{ticker:'ABC',coverage:'INCOMPLETE',as_of:'2026-10-12T11:00:00Z',items,has_more:false},error:false,retry(){},...options};
  return renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(exports.default,{ticker:'ABC'})));
}
test('actual action renderer preserves original dates, units and source evidence; no inferred ex-rights',()=>{
  const html=render([row]);
  assert.match(html,/20 Oct 2026/);assert.match(html,/1 Nov 2026/);
  assert.match(html,/1,500 VND/);assert.match(html,/Ex-rights date/);assert.match(html,/<td>Unavailable<\/td>/);
  assert.doesNotMatch(html,/19 Oct 2026/);
  assert.match(html,/Preserved source wording/);assert.match(html,/href="https:\/\/vsdc.vn\/original.pdf"/);
  assert.match(html,/Incomplete coverage/);assert.match(html,/Verified source observation/);
});
test('pending corrections, withdrawals and fixtures withhold trusted dates and terms but keep evidence',()=>{
  for(const change of [{verified:false},{withdrawn:true},{is_fixture:true}]) {
    const html=render([{...row,...change}]);
    assert.doesNotMatch(html,/1,500 VND|20 Oct 2026|1 Nov 2026/);
    assert.match(html,/Preserved source wording/);
  }
  const pendingFixture=render([{...row,verified:false,is_fixture:true}]);
  assert.match(pendingFixture,/Pending verification/);assert.match(pendingFixture,/Fixture observation/);
});
test('empty, failed and wrong-ticker responses are distinct; Vietnamese chrome preserves source text',()=>{
  assert.match(render(),/No recorded corporate actions for ABC/);
  assert.match(render(),/does not establish that no corporate action occurred/);
  const failed=render([],{error:true});assert.match(failed,/temporarily unavailable/);assert.doesNotMatch(failed,/No recorded corporate actions/);
  assert.doesNotMatch(render([],{data:{ticker:'OTHER',items:[row]}}),/Original issuer evidence/);
  const vi=render([row],{},'vi');assert.match(vi,/Ngày đăng ký cuối cùng/);assert.match(vi,/Original issuer evidence/);assert.match(vi,/1.500 VND/);
});
