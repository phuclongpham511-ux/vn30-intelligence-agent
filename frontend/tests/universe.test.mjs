import test from 'node:test';
import assert from 'node:assert/strict';
import { browseSecurities, loadUniverse } from '../lib/universe.ts';

test('full universe search/filter/pagination finds equities without a Stock id', () => {
  const rows = [{symbol:'AAA',exchange:'HOSE',display_name_en:'Alpha'},
    {symbol:'BBB',exchange:'HNX',company_name:'Công ty Beta'}, {symbol:'CCC',exchange:'UPCOM'}];
  assert.equal(browseSecurities(rows, 'cong ty', 'HNX').items[0].symbol, 'BBB');
  assert.equal(browseSecurities(rows, 'ccc').items[0].symbol, 'CCC');
  assert.deepEqual(browseSecurities(rows, '', '', 1, 1).items.map(r=>r.symbol), ['BBB']);
  assert.equal(browseSecurities(rows, '', '', 0, 1).total, 3);
});

test('cached metadata pages cover the full master and never request market history', async () => {
  const calls=[];
  const result=await loadUniverse(async url => { calls.push(url); return {ok:true,json:async()=>({
    total:2,total_universe:2,status:'healthy',items:[{symbol:calls.length===1?'AAA':'BBB',exchange:'HOSE'}]})}; });
  assert.deepEqual(result.stocks.map(r=>r.symbol), ['AAA','BBB']);
  assert.equal(calls.length,2);
  assert.ok(calls.every(url=>url.startsWith('/api/stocks/universe?')));
});
