import test from 'node:test';
import assert from 'node:assert/strict';
import {acceptanceDataset,replayHandler,clock} from './fixtures/acceptance-replay.mjs';
import {financialEngineData} from '../lib/financial-engine-data.ts';
import {stockResearch} from '../lib/stock-intelligence.ts';
import {loadIntelligence,emptyWatchlist,followStock,unfollowStock,isUnread,reviewUpdates,readWatchlist} from '../lib/watchlist.ts';
import {actionDate,actionTerm,trustedAction} from '../lib/stock-detail.ts';

const dataset=acceptanceDataset(),handle=replayHandler(dataset);
const request=(url,options={})=>handle(new Request('http://127.0.0.1:3410'+url,options));

test('offline API fails closed on unlisted routes, acquisition and unknown instruments',async()=>{
 for(const [url,method] of [['/api/ingestion/refresh','POST'],['/api/stocks/XYZ/financials','GET'],['/api/stocks/AAA/onboard','POST'],['/api/news/refresh','POST']]) {
  const response=await request(url,{method});assert.equal(response.status,404);assert.equal(response.headers.get('X-Woofi-Acceptance'),'OFFLINE_REPLAY_ONLY');
 }
 const unknown=await loadIntelligence(['XYZ'],0,undefined,request);assert.equal(unknown.stocks[0].status,'unavailable');
});
test('metadata pagination/search owns the requested ticker and never invents business data',async()=>{
 const data=await (await request('/api/stocks/universe?q=ABC&limit=1')).json();
 assert.equal(data.total,1);assert.equal(data.items[0].symbol,'ABC');assert.equal(data.items[0].exchange,'DEMO');assert.match(data.items[0].source,/DEMO/);
 assert.equal(data.items[0].industry,undefined);assert.equal(data.items[0].business_description,undefined);
});
test('shared financial fixture remains DEMO; unsupported valuation and periods stay unavailable',async()=>{
 const reply=await request('/api/stocks/ABC/financials?frequency=annual');
 const data=financialEngineData(await reply.json(),'ABC','annual',true);
 assert.equal(data.is_fixture,true);assert.ok(data.fundamental_summary.metrics.some(m=>m.status==='DEMO'));
 assert.ok(!data.fundamental_summary.metrics.some(m=>m.status==='QUALIFIED'));
 assert.equal(data.fundamental_summary.metrics.find(m=>m.key==='pe').value,null);
 assert.equal((await request('/api/stocks/ABC/financials?frequency=ttm')).status,404);
});
test('corporate-action DEMO/conflict/withdrawn states cannot expose confirmed terms or dates',async()=>{
 const data=await (await request('/api/stocks/ABC/corporate-actions')).json();assert.equal(data.items.length,4);
 for(const row of data.items){assert.equal(row.is_fixture,true);assert.equal(trustedAction(row),false);assert.equal(actionDate(row,'record_date'),null);assert.equal(actionTerm(row,'cash_vnd_per_share'),null);assert.equal(row.source_url,null);}
 assert.equal(data.coverage,'INCOMPLETE');
});
test('real parser accepts one stable story/two articles and one original DEMO discussion',async()=>{
 const data=await loadIntelligence(['AAA'],0,undefined,request,{community_groups:true});
 const projected=stockResearch(data,'AAA',followStock(emptyWatchlist(),'AAA'));
 assert.equal(projected.omitted,false);assert.equal(projected.news.length,1);assert.equal(projected.news[0].articles.length,2);
 assert.equal(projected.community.length,1);assert.equal(projected.communityGroups.length,1);
 assert.equal(projected.community[0].source,'DEMO Forum — unverified');assert.equal(projected.community[0].discussion.is_fixture,true);
 assert.notEqual(projected.news[0].published,projected.news[0].observed);
 assert.equal(Date.parse(data.as_of)-Date.parse(data.stocks[0].news.window_start),72*3600000);
 assert.equal(Date.parse(data.as_of)-Date.parse(data.stocks[0].community.window_start),24*3600000);
 assert.ok(!data.stocks[0].news.items.some(s=>s.entity_id==='outside-window'));
});
test('canonical review receipts persist, cross-ticker review is separate, corrections reopen and unfollow preserves another ticker',async()=>{
 const data=await loadIntelligence(['AAA','BBB'],0,undefined,request),item=data.stocks[0].news.items[0];
 let state=followStock(followStock(emptyWatchlist(),'AAA'),'BBB');assert.equal(isUnread(state,'AAA',item),true);
 state=readWatchlist(JSON.stringify(reviewUpdates(state,'AAA',[item],clock)));
 assert.equal(isUnread(state,'AAA',item),false);assert.equal(isUnread(state,'BBB',item),true);
 const correction={...item,revision:'v2',revision_members:{...item.revision_members,article:'v2'}};
 assert.equal(isUnread(state,'AAA',correction),true);assert.equal(isUnread(state,'AAA',item),false);
 const removed=unfollowStock(state,'BBB');assert.deepEqual(removed.receipts.AAA,state.receipts.AAA);
 assert.equal(removed.symbols.includes('AAA'),true);assert.equal(removed.symbols.includes('BBB'),false);
});
test('malformed mutation/oversized request cannot escape fixture-only request boundaries',async()=>{
 for(const body of ['bad',JSON.stringify({symbols:['AAA','AAA']}),JSON.stringify({symbols:['AAA'],offset:-1}),JSON.stringify({symbols:['AAA'],page_size:100})])assert.equal((await request('/api/watchlists/intelligence',{method:'POST',body})).status,422);
 assert.equal((await request('/api/watchlists/intelligence',{method:'POST',body:'x'.repeat(8001)})).status,413);
});
