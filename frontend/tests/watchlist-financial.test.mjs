import test from 'node:test';
import assert from 'node:assert/strict';
import {emptyWatchlist,followStock,reviewUpdates,readWatchlist,isUnread} from '../lib/watchlist.ts';
import {privateFinancialRequest,attachFinancialUpdates} from '../lib/watchlist-financial-server.ts';
import {readFileSync} from 'node:fs';
import {transformSync} from 'next/dist/build/swc/index.js';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);

test('financial review uses existing receipts: reload, duplicate and correction behavior',()=>{
 const item={id:'financial:stable',entity_id:'stable',revision:'one',kind:'financial'};
 const initial=followStock(emptyWatchlist(),'ABC');
 assert.equal(isUnread(initial,'ABC',item),true);
 const state=readWatchlist(JSON.stringify(reviewUpdates(initial,'ABC',[item],'2026-10-26T00:00:00Z')));
 assert.equal(isUnread(state,'ABC',{...item}),false);
 assert.equal(isUnread(state,'ABC',{...item,revision:'two'}),true);
 assert.equal(isUnread(state,'ABC',{...item,id:'news:stable',kind:'news'}),true);
});

test('private feature requires the supported loopback boundary and all flags',async()=>{
 const before={...process.env};
 try {
  const request=new Request('http://127.0.0.1:3431/api/watchlists/intelligence',{headers:{host:'127.0.0.1:3431'}});
  delete process.env.WOOFI_WATCHLIST_FINANCIALS;
  assert.equal(privateFinancialRequest(request),false);
  Object.assign(process.env,{WOOFI_WATCHLIST_FINANCIALS:'1',APP_ENV:'development',WOOFI_PERSONAL_RESEARCH:'1',WOOFI_PERSONAL_BOUNDARY:'loopback-custom-server-v1',WOOFI_DEPLOYMENT_KIND:'personal-development',WOOFI_PERSONAL_BACKEND:'http://127.0.0.1:8432'});
  assert.equal(privateFinancialRequest(request),true);
  for(const headers of [{host:'evil.test'},{host:'127.0.0.1:3431',origin:'https://evil.test'},{host:'127.0.0.1:3431','sec-fetch-site':'cross-site'},{host:'127.0.0.1:3431','x-forwarded-host':'127.0.0.1:3431'}])
   assert.equal(privateFinancialRequest(new Request(request.url,{headers})),false);
  process.env.APP_ENV='production';assert.equal(privateFinancialRequest(request),false);
 } finally {for(const key of Object.keys(process.env))if(!(key in before))delete process.env[key];Object.assign(process.env,before);}
});

test('private merge retains News/Community/Technical and bounds financial reads',async()=>{
 const source={stocks:['A','B','C','D','E','F'].map(symbol=>({symbol,news:{items:[1]},community:{items:[2]},technical:{items:[3]}}))};
 const original=JSON.stringify(source); let calls=0;
 process.env.WOOFI_PERSONAL_BACKEND='http://127.0.0.1:8432';
 process.env.WOOFI_PERSONAL_RESEARCH='1';process.env.WOOFI_PERSONAL_BOUNDARY='loopback-custom-server-v1';process.env.WOOFI_DEPLOYMENT_KIND='personal-development';
 const result=await attachFinancialUpdates(source,source.stocks.map(r=>r.symbol),undefined,async(url,options)=>{
  calls++;assert.equal(url,'http://127.0.0.1:8432/personal-research/watchlist-financials');
  assert.deepEqual(JSON.parse(options.body).symbols,['A','B','C','D','E']);
  return Response.json({contract:'private-watchlist-financial-v1',stocks:['A','B','C','D','E'].map(symbol=>({symbol,financial:{status:'MISSING_DATA',items:[],reasons:['missing'],has_more:false,truncated:false}}))});
 });
 assert.equal(calls,1);assert.equal(JSON.stringify(source),original);
 assert.equal(result.stocks[5].financial.status,'NOT_CHECKED');
 for(let i=0;i<source.stocks.length;i++)for(const key of ['news','community','technical'])assert.deepEqual(result.stocks[i][key],source.stocks[i][key]);
 const failed=await attachFinancialUpdates(source,['A'],undefined,async()=>{throw Error('private read failed');});
 assert.equal(failed.stocks[0].financial.status,'UNAVAILABLE');
 assert.deepEqual(failed.stocks[0].news,source.stocks[0].news);
});

test('actual Next proxy leaves public responses unchanged and adds private data only in authorized runtime',async()=>{
 const before={...process.env},originalFetch=globalThis.fetch;
 const exports={},code=transformSync(readFileSync(new URL('../app/api/watchlists/intelligence/route.ts',import.meta.url),'utf8'),{filename:'route.ts',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript'}}}).code;
 new Function('require','exports',code)(id=>id==='@/lib/watchlist-financial-server'?{privateFinancialRequest,attachFinancialUpdates}:require(id),exports);
 const data={as_of:'2026-10-26T00:00:00Z',stocks:[{symbol:'ABC',news:{items:[1]},community:{items:[2]},technical:{items:[3]}}]};
 const makeRequest=()=>new Request('http://127.0.0.1:3431/api/watchlists/intelligence',{method:'POST',headers:{host:'127.0.0.1:3431'},body:JSON.stringify({symbols:['ABC']})});
 let calls=[];
 try{
  globalThis.fetch=async(url)=>{calls.push(url);return Response.json(url.endsWith('/watchlists/intelligence')?data:{contract:'private-watchlist-financial-v1',stocks:[{symbol:'ABC',financial:{status:'MISSING_DATA',items:[],reasons:['missing'],has_more:false,truncated:false}}]});};
  delete process.env.WOOFI_WATCHLIST_FINANCIALS;
  const publicResponse=await exports.POST(makeRequest());
  assert.deepEqual(await publicResponse.json(),data);assert.equal(calls.length,1);
  Object.assign(process.env,{WOOFI_WATCHLIST_FINANCIALS:'1',APP_ENV:'development',WOOFI_PERSONAL_RESEARCH:'1',WOOFI_PERSONAL_BOUNDARY:'loopback-custom-server-v1',WOOFI_DEPLOYMENT_KIND:'personal-development',WOOFI_PERSONAL_BACKEND:'http://127.0.0.1:8432'});
  calls=[];const response=await exports.POST(makeRequest());const privateData=await response.json();
  assert.equal(calls.length,2);assert.equal(response.headers.get('cache-control'),'private, no-store');
  assert.equal(privateData.stocks[0].financial.status,'MISSING_DATA');
  for(const kind of ['news','community','technical'])assert.deepEqual(privateData.stocks[0][kind],data.stocks[0][kind]);
  calls=[];
  const detail=new Request('http://127.0.0.1:3431/api/watchlists/intelligence',{method:'POST',headers:{host:'127.0.0.1:3431'},body:JSON.stringify({symbols:['ABC'],community_groups:true})});
  assert.deepEqual(await (await exports.POST(detail)).json(),data);
  assert.equal(calls.length,1); // Stock Detail's shared read must not gain financial work.
 }finally{globalThis.fetch=originalFetch;for(const key of Object.keys(process.env))if(!(key in before))delete process.env[key];Object.assign(process.env,before);}
});

test('malformed private payload does not contaminate existing source projections',async()=>{
 const core={as_of:'2026-10-26T00:00:00Z',stocks:[{symbol:'ABC',news:{items:[1]},community:{items:[2]},technical:{items:[3]}}]};
 Object.assign(process.env,{WOOFI_PERSONAL_RESEARCH:'1',WOOFI_PERSONAL_BOUNDARY:'loopback-custom-server-v1',WOOFI_DEPLOYMENT_KIND:'personal-development',WOOFI_PERSONAL_BACKEND:'http://127.0.0.1:8432'});
 const result=await attachFinancialUpdates(core,['ABC'],undefined,async()=>Response.json({contract:'private-watchlist-financial-v1',stocks:[{symbol:'ABC',financial:{status:'READY',items:[{kind:'financial',evidence:{insight:{causal_explanation:'invented'}}}],reasons:[],has_more:false,truncated:false}}]}));
 assert.equal(result.stocks[0].financial.status,'UNAVAILABLE');
 assert.deepEqual(result.stocks[0].news,core.stocks[0].news);
});
