import test from 'node:test';
import assert from 'node:assert/strict';
import {stockResearch} from '../lib/stock-intelligence.ts';
import {loadIntelligence,reviewUpdates,isUnread,baselineLegacyReviews,readWatchlist} from '../lib/watchlist.ts';
import {reviewBriefingItem} from '../lib/dailyBriefing.ts';

import {at,article,news,thread,discussion,packet,saved} from './fixtures/stock-intelligence.mjs';

test('one item per canonical story/discussion ID; publication never becomes ingestion time',()=>{
 const data=packet([news,news],[discussion,discussion]),state=saved(),before=JSON.stringify({data,state});
 const result=stockResearch(data,'AAA',state);
 assert.equal(result.news.length,1);assert.equal(result.community.length,1);
 assert.equal(result.news[0].published,article.published_at);assert.equal(result.news[0].observed,article.first_seen_at);
 assert.equal(result.community[0].observed,thread.first_seen_at);assert.equal(result.community[0].discussion.views,0);
 assert.equal(JSON.stringify({data,state}),before);
});
test('strong current ticker evidence and weaker stored associations stay distinct',()=>{
 const proof={symbol:'AAA',article_id:article.id,article_title:article.title,article_url:article.url,kind:'explicit_stock',matched_text:'AAA',policy:'issuer-context-v2',evidence_origin:'headline'};
 assert.equal(stockResearch(packet([{...news,ticker_associations:[proof]}]),'AAA',saved()).news[0].relevance,'Explicit ticker evidence');
 const stale={...proof,article_title:'Prior title'};
 assert.equal(stockResearch(packet([{...news,ticker_associations:[stale]}]),'AAA',saved()).news[0].relevance,'Stored ticker match; detailed proof unavailable');
 const issuer={...proof,kind:'issuer_identity'};
 assert.equal(stockResearch(packet([{...news,ticker_associations:[issuer]}]),'AAA',saved()).news[0].relevance,'Issuer-context evidence');
});
test('foreign ticker, unsafe URLs and future source evidence cannot enter stock research',()=>{
 assert.throws(()=>stockResearch(packet(),'BBB',saved()));
 for(const mutation of [{...news,evidence:[{...article,tickers:['BBB']}]},{...news,url:'javascript:alert(1)'},{...news,evidence:[{...article,published_at:'2026-10-19T00:00:00Z'}]}]){
  const result=stockResearch(packet([mutation]),'AAA',saved());assert.equal(result.news.length,0);assert.equal(result.omitted,true);
 }
 const result=stockResearch(packet([],[{...discussion,evidence:{...thread,tickers:['BBB']}}]),'AAA',saved());
 assert.equal(result.community.length,0);assert.equal(result.omitted,true);
});
test('server-owned story windows retain older anchors, with no client renewal or time-only unread cutoff',()=>{
 const old={...news,occurred_at:'2026-10-01T00:00:00Z',evidence:[{...article,published_at:null,first_seen_at:'2026-10-01T00:00:00Z'}]};
 const result=stockResearch(packet([old]),'AAA',saved());
 assert.equal(result.news.length,1);assert.equal(result.news[0].published,null);assert.equal(result.news[0].unread,true);
});
test('explicit single-item reviews preserve other stocks, hidden items and concurrent newer reviews',()=>{
 const state=saved(),entry={references:[{symbol:'AAA',item:news}]};
 const reviewed=readWatchlist(JSON.stringify(reviewBriefingItem(state,state,entry,at)));
 assert.equal(isUnread(reviewed,'AAA',news),false);assert.equal(isUnread(reviewed,'BBB',news),true);
 assert.equal(isUnread(reviewed,'AAA',discussion),true);
 const current=reviewUpdates(state,'AAA',[{...news,revision:'v2',revision_members:{article:'v2'}}],at);
 assert.equal(reviewBriefingItem(current,state,entry,at),current,'concurrent explicit review wins');
 const removed={...state,symbols:['BBB']};assert.equal(reviewBriefingItem(removed,state,entry,at),removed);
});
test('publisher copies and engagement changes do not reopen reviewed content; a correction does',()=>{
 const state=reviewUpdates(saved(),'AAA',[news,discussion],at);
 const copy={...news,revision:'another-anchor',revision_members:{article:'v1',copy:'copy-v1'}};
 assert.equal(stockResearch(packet([copy],[{...discussion,evidence:{...thread,replies:999}}]),'AAA',state).news[0].unread,false);
 assert.equal(stockResearch(packet([copy],[{...discussion,evidence:{...thread,replies:999}}]),'AAA',state).community[0].unread,false);
 const correction={...copy,revision_members:{article:'v2',copy:'copy-v1'}};
 const row=stockResearch(packet([correction]),'AAA',state).news[0];assert.equal(row.unread,true);assert.equal(row.corrected,true);
});
test('legacy baselines preserve known story reviews without creating new reviews or dates',()=>{
 const state={...saved(),seen:{AAA:['story']}};
 const next=baselineLegacyReviews(state,packet());
 assert.equal(next.receipts.AAA['news:story'].reviewed_at,null);
 assert.equal(isUnread(next,'AAA',discussion),true);assert.equal(next.reviewedAt,undefined);
 assert.equal(stockResearch(packet(),'AAA',null).news[0].unread,null);
 assert.equal(stockResearch(packet(),'AAA',{...saved(),symbols:['BBB']}).news[0].unread,null);
});
test('Pulse-supplied copy groups suppress repeated primary cards without merging native review identities',()=>{
 const copy={...discussion,id:'community:copy',entity_id:'copy',evidence:{...thread,id:'copy'}};
 const data=packet([],[discussion,copy]);data.stocks[0].community.display_groups=[['thread','copy']];
 const state=reviewUpdates(saved(),'AAA',[discussion],at);
 const result=stockResearch(data,'AAA',state);
 assert.equal(result.community.length,2);assert.equal(result.communityGroups.length,1);
 assert.equal(result.communityGroups[0][0].item.entity_id,'copy','unreviewed member represents the group');
 assert.equal(result.communityGroups[0][0].unread,true);assert.equal(result.communityGroups[0][1].unread,false);
});
test('missing community observation time never inherits its publication instant',()=>{
 const evidence={...thread};delete evidence.first_seen_at;
 const result=stockResearch(packet([],[{...discussion,evidence}]),'AAA',saved());
 assert.equal(result.community[0].published,thread.published_at);assert.equal(result.community[0].observed,null);
});
test('copy grouping is optional display metadata; existing Watchlist request bodies stay unchanged',async()=>{
 const response={...packet(),stocks:[{symbol:'AAA',status:'unavailable',news:null,community:null,technical:null}]};
 const bodies=[];
 const request=async(_url,options)=>{bodies.push(JSON.parse(options.body));return {ok:true,json:async()=>response};};
 await loadIntelligence(['AAA'],0,undefined,request);
 await loadIntelligence(['AAA'],0,undefined,request,{community_groups:true});
 assert.deepEqual(bodies[0],{symbols:['AAA'],offset:0,page_size:12});
 assert.deepEqual(bodies[1],{...bodies[0],community_groups:true});
});
