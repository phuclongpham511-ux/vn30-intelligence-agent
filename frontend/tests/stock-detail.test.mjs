import test from 'node:test';
import assert from 'node:assert/strict';
import {stockSection,stockIdentity,stockRead,actionStatus,trustedAction,actionUrl} from '../lib/stock-detail.ts';
import {readWatchlist,followStock} from '../lib/watchlist.ts';

test('stock sections accept research deep links and reject unknown fragments',()=>{
  assert.equal(stockSection('#stock-actions'),'actions');
  assert.equal(stockSection('#stock-fundamentals'),'fundamentals');
  assert.equal(stockSection('#stock-community'),'community');
  assert.equal(stockSection('#untrusted'),'overview');
});
test('stock identity requires the selected cached equity, never another ticker',()=>{
  assert.equal(stockIdentity([{symbol:'ABC',exchange:'HOSE',company_name:null}],'ABC').company_name,null);
  assert.throws(()=>stockIdentity([{symbol:'XYZ',exchange:'HNX'}],'ABC'));
});
test('pending, withdrawn and fixture observations cannot present trusted event terms',()=>{
  const row={verified:true,withdrawn:false,is_fixture:false,source:'Synthetic source contract test'};
  assert.equal(trustedAction(row),true);
  for(const change of [{verified:false},{withdrawn:true},{is_fixture:true}])assert.equal(trustedAction({...row,...change}),false);
  assert.equal(actionStatus({...row,verified:false}),'Pending verification');
  assert.equal(actionStatus({...row,withdrawn:true}),'Withdrawn');
  assert.equal(actionStatus({...row,is_fixture:true}),'Fixture observation');
});
test('corporate source links reject credentials and executable URLs',()=>{
  assert.equal(actionUrl('https://vsdc.vn/document.pdf'),'https://vsdc.vn/document.pdf');
  for(const value of [null,'javascript:alert(1)','https://name:secret@vsdc.vn/','file:///private'])assert.equal(actionUrl(value),null);
});
test('independent stock reads surface errors and discard obsolete JSON responses',async()=>{
  const abort=new AbortController();
  await assert.rejects(stockRead('/market',abort.signal,async()=>({ok:false})),/unavailable/);
  await assert.rejects(stockRead('/identity',abort.signal,async()=>({ok:true,json:async()=>{abort.abort();return {ticker:'OLD'};}})));
});
test('following from Stock Detail preserves explicit review receipts for existing stocks',()=>{
  const raw={symbols:['ABC'],seen:{ABC:['story-1']},communitySeen:{ABC:['thread-1']},receipts:{ABC:{'news:story-1':{revision:'v2',reviewed_at:'2026-10-12T09:00:00Z'}}}};
  const updated=followStock(readWatchlist(JSON.stringify(raw)),'XYZ');
  assert.deepEqual(updated.receipts,raw.receipts);
  assert.deepEqual(updated.seen,raw.seen);
  assert.deepEqual(updated.communitySeen,raw.communitySeen);
  assert.throws(()=>readWatchlist('{invalid'));
});
