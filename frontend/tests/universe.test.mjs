import test from 'node:test';
import assert from 'node:assert/strict';
import { browseSecurities, loadUniverse,stockSuggestions,readRecentSearches,rememberSearch,removeRecentSearch,recentSearchLimit,equityPageUrl,loadEquityPage } from '../lib/universe.ts';

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

test('server discovery requests a single bounded page, with composed filters and escaped company search',async()=>{
 const url=equityPageUrl({query:'Công ty & Alpha',exchange:'HOSE',group:'VN30',page:2,size:10});
 const params=new URL(url,'https://local.example').searchParams;
 assert.equal(params.get('q'),'Công ty & Alpha');assert.equal(params.get('exchange'),'HOSE');
 assert.equal(params.get('index_group'),'VN30');assert.equal(params.get('offset'),'20');assert.equal(params.get('limit'),'10');
 let count=0;
 const signal=new AbortController().signal;
 const data=await loadEquityPage(url,signal,async (path,options)=>{
  count++;assert.equal(path,url);assert.equal(options.signal,signal);assert.equal(options.cache,'no-store');
  return {ok:true,json:async()=>({items:[{symbol:'AAA'}],total:21,total_universe:1000,offset:20,limit:10,status:'healthy'})};
 });
 assert.equal(count,1);assert.equal(data.items.length,1);
 assert.equal(new URL(equityPageUrl({symbols:['AAA','BBB'],size:8}),'https://local.example').searchParams.get('symbols'),'AAA,BBB');
});

test('discovery transport failures and malformed pages never become zero results',async()=>{
 await assert.rejects(loadEquityPage(equityPageUrl(),undefined,async()=>({ok:false})),/could not be loaded/);
 for(const page of [{items:[],total:null},{items:[],total:0,total_universe:-1,offset:0,limit:10},
  {items:[{symbol:'AAA'},{symbol:'BBB'}],total:2,total_universe:2,offset:0,limit:1}])
  await assert.rejects(loadEquityPage(equityPageUrl(),undefined,async()=>({ok:true,json:async()=>page})),/Incomplete/);
});
