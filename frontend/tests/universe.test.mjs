import test from 'node:test';
import assert from 'node:assert/strict';
import { browseSecurities, loadUniverse,stockSuggestions,readRecentSearches,rememberSearch,removeRecentSearch,recentSearchLimit } from '../lib/universe.ts';

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

test('compact discovery pages compose index membership, company search and exchange',()=>{
 const rows=Array.from({length:32},(_,n)=>({symbol:`X${n}`,exchange:n%2?'HNX':'HOSE',display_name_en:'Alpha'}));
 assert.equal(browseSecurities(rows).items.length,10);
 assert.equal(browseSecurities(rows,'Alpha','HNX',0,10,['X1','X2']).total,1);
 assert.equal(browseSecurities(rows,'','',1).items[0].symbol,'X10');
 assert.deepEqual(browseSecurities(rows,'','',0,10,[]).items,[]);
});
test('empty search exposes only bounded real recent selections, never the full universe',()=>{
 const rows=Array.from({length:100},(_,n)=>({symbol:`X${n}`,exchange:'HOSE'}));
 assert.deepEqual(stockSuggestions(rows,'',[]),[]);
 assert.deepEqual(stockSuggestions(rows,'',['X9','MISSING']).map(s=>s.symbol),['X9']);
 assert.equal(stockSuggestions(rows,'X',[]).length,6);
 assert.deepEqual(readRecentSearches('["X1","X1","bad value","X2"]'),['X1','X2']);
 assert.deepEqual(rememberSearch(['X1','X2','X3','X4','X5'],'X2'),['X2','X1','X3','X4','X5']);
});

test('history caps at eight, deduplicates, removes just one, and survives serialization',()=>{
 let recent=[];
 for(let n=0;n<15;n++) recent=rememberSearch(recent,`X${n}`);
 assert.equal(recent.length,recentSearchLimit);
 assert.equal(recent[0],'X14');
 recent=removeRecentSearch(recent,'X13');
 assert.equal(recent.length,7);assert.ok(!recent.includes('X13'));
 assert.deepEqual(readRecentSearches(JSON.stringify(recent)),recent);
 assert.deepEqual(readRecentSearches('[]'),[]);
 assert.deepEqual(stockSuggestions([{symbol:'AAA',exchange:'HOSE'}],'???',[]),[]);
});

test('ticker exact/prefix matches precede broad company-name substrings',()=>{
 const rows=[{symbol:'AAA',exchange:'HOSE',display_name_en:'Vietnam Example'},...['VIB','VIC','VID','VIE','VIG','VII','VIM'].map(symbol=>({symbol,exchange:'HOSE'}))];
 assert.deepEqual(stockSuggestions(rows,'VI',[]).map(row=>row.symbol),['VIB','VIC','VID','VIE','VIG','VII']);
 assert.equal(stockSuggestions(rows,'vib',[])[0].symbol,'VIB');
});
