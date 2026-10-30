import test from 'node:test';
import assert from 'node:assert/strict';
import {actionTerm,actionDate,actionHistory,trustedAction,actionStatus,actionDetailsIncomplete} from '../lib/stock-detail.ts';
// Synthetic contract unit tests only, not provider or live dividend evidence.
const row={symbol:'DEMO01',source:'Synthetic test source',action_type:'cash_dividend',verified:true,withdrawn:false,is_fixture:false,
 effective_date:null,record_date:'2026-10-20',payment_date:null,terms:{cash_vnd_per_share:0,new_shares_per_old:.1,subscription_price_vnd:12000}};
test('declared monetary and share units remain type-specific without inferred yields or ratios',()=>{
 assert.equal(actionTerm(row,'cash_vnd_per_share'),0);assert.equal(actionTerm(row,'new_shares_per_old'),null);
 for(const type of ['stock_dividend','bonus_shares','rights_offering','additional_issuance']) {
  const r={...row,action_type:type};assert.equal(actionTerm(r,'new_shares_per_old'),.1);
  assert.equal(actionTerm(r,'cash_vnd_per_share'),null);
  assert.equal(actionTerm(r,'subscription_price_vnd'),['rights_offering','additional_issuance'].includes(type)?12000:null);
 }
 assert.equal(actionTerm({...row,action_type:'other'},'cash_vnd_per_share'),null);
});
test('unqualified, fixture, withdrawn, invalid and absent values never become presentable facts',()=>{
 for(const patch of [{verified:false},{withdrawn:true},{is_fixture:true},{is_fixture:undefined},{withdrawn:undefined},{source:''}]) {
  const r={...row,...patch};assert.equal(trustedAction(r),false);assert.equal(actionTerm(r,'cash_vnd_per_share'),null);assert.equal(actionDate(r,'record_date'),null);
  assert.notEqual(actionStatus(r),'Source-marked verified');
 }
 for(const value of [null,undefined,-1,NaN,Infinity,Number.MAX_SAFE_INTEGER+1,'1500'])assert.equal(actionTerm({...row,terms:{cash_vnd_per_share:value}},'cash_vnd_per_share'),null);
});
test('dates preserve original precision and do not back-calculate an ex-date or normalize invalid calendar dates',()=>{
 assert.equal(actionDate(row,'effective_date'),null);assert.equal(actionDate(row,'record_date'),'2026-10-20');assert.equal(actionDate(row,'payment_date'),null);
 for(const date of ['2026-02-30','2026-2-01','not-a-date',null,'2026-10-20T00:00:00Z'])assert.equal(actionDate({...row,effective_date:date},'effective_date'),null);
 assert.equal(actionDate({...row,effective_date:'2024-02-29'},'effective_date'),'2024-02-29');
});
test('category filters preserve source observation order and never merge distinct source observations',()=>{
 const items=['cash_dividend','stock_dividend','bonus_shares','rights_offering','additional_issuance','other'].map((action_type,i)=>({...row,action_type,observation_id:String(i)}));
 const before=JSON.stringify(items);
 assert.deepEqual(actionHistory(items,'distributions').map(r=>r.observation_id),['0','1','2']);
 assert.deepEqual(actionHistory(items,'other').map(r=>r.observation_id),['3','4','5']);
 assert.equal(actionHistory(items).length,6);assert.equal(JSON.stringify(items),before);
});

test('display completeness rejects invalid or missing fields without treating zero as missing',()=>{
 const cash={...row,effective_date:'2026-10-19',payment_date:'2026-11-01'};
 assert.equal(actionDetailsIncomplete(cash),false);
 for(const change of [{record_date:null},{payment_date:'2026-02-30'},{terms:null},{terms:{cash_vnd_per_share:NaN}}])assert.equal(actionDetailsIncomplete({...cash,...change}),true);
 const rights={...cash,action_type:'rights_offering'};
 assert.equal(actionDetailsIncomplete(rights),false);
 assert.equal(actionDetailsIncomplete({...rights,terms:{new_shares_per_old:.5}}),true);
 assert.equal(actionDetailsIncomplete({...cash,action_type:'other'}),true);
});

test('explicit unresolved-correction marker vetoes both date and term gates while preserving the input',()=>{
 const conflict={...row,verification_note:'Unresolved correction: two incompatible dates'};
 const before=JSON.stringify(conflict);
 assert.equal(trustedAction(conflict),false);assert.equal(actionStatus(conflict),'Unresolved correction');
 assert.equal(actionDate(conflict,'record_date'),null);assert.equal(actionTerm(conflict,'cash_vnd_per_share'),null);
 assert.equal(actionDetailsIncomplete(conflict),true);assert.equal(JSON.stringify(conflict),before);
 assert.equal(trustedAction({...row,verification_note:'Verified source has missing payment date'}),true,'missing facts are not invented conflicts');
});
