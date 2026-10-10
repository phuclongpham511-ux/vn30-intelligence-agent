import test from 'node:test';
import assert from 'node:assert/strict';
import {emptyWatchlist,followStock,readWatchlist,reviewUpdates,isUnread,uniqueUpdates,baselineLegacyReviews,unfollowStock,loadIntelligence,markReviewed,parseIntelligence,technicalCountKnown} from '../lib/watchlist.ts';

const update=(kind='news',id='same',revision='v1',extra={})=>({id:kind+':'+id,entity_id:id,kind,revision,title:'source evidence',occurred_at:'2026-10-10T01:00:00Z',url:'https://example.org',evidence:[],...extra});
const time='2026-10-10T02:00:00Z';
test('namespaced identities, content revisions, new arrivals and explicit review survive reload',()=>{
  const original=followStock(emptyWatchlist(),'XYZ');
  const news=update(),community=update('community'),technical=update('technical');
  assert.equal(isUnread(original,'XYZ',news),true);
  const reviewed=readWatchlist(JSON.stringify(reviewUpdates(original,'XYZ',[news],time)));
  assert.equal(reviewed.reviewedAt.XYZ,time);
  assert.equal(isUnread(reviewed,'XYZ',news),false);
  assert.equal(isUnread(reviewed,'XYZ',community),true);
  assert.equal(isUnread(reviewed,'XYZ',technical),true);
  assert.equal(isUnread(reviewed,'XYZ',update('news','new')),true);
  assert.equal(isUnread(reviewed,'XYZ',update('news','same','v2')),true);
  const later=reviewUpdates(reviewed,'XYZ',[community],time);
  assert.equal(isUnread(later,'XYZ',news),false);
  assert.equal(isUnread(original,'XYZ',news),true);
  assert.deepEqual(unfollowStock(later,'XYZ'),emptyWatchlist());
});
test('duplicate publishers and rechecks do not create unread stories; a known source correction does',()=>{
  const news=update('news','one','anchor',{revision_members:{article1:'text-v1'}});
  const state=reviewUpdates(followStock(emptyWatchlist(),'XYZ'),'XYZ',[news],time);
  assert.equal(isUnread(state,'XYZ',{...news,revision_members:{article1:'text-v1',article2:'copy'},source_count:2}),false);
  assert.equal(isUnread(state,'XYZ',{...news,revision:'different-publisher-anchor',revision_members:{article1:'text-v1',article2:'copy'}}),false);
  assert.equal(isUnread(state,'XYZ',{...news,revision_members:{article1:'text-v2',article2:'copy'}}),true);
  assert.equal(uniqueUpdates([news,news,update('community','one')]).length,2);
});
test('malformed pages never become zero; incomplete accepted packets have unknown counts',()=>{
  const data={as_of:time,offset:0,page_size:12,stocks:[{symbol:'XYZ',status:'unavailable',news:null,community:null,technical:null}],news_sources:[],community_sources:[]};
  assert.throws(()=>parseIntelligence({...data,stocks:[{...data.stocks[0],symbol:'OTHER'}]},['XYZ'],0),/Invalid/);
  assert.throws(()=>parseIntelligence({...data,stocks:[]},['XYZ'],0),/Invalid/);
  assert.throws(()=>parseIntelligence({...data,offset:12},['XYZ'],0),/Invalid/);
  assert.equal(technicalCountKnown({data:{kind:'diagnostic'}}),false);
  assert.equal(technicalCountKnown({data:{kind:'provisional_packet',packet:{packet_state:'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'}}}),false);
  assert.equal(technicalCountKnown({data:{kind:'provisional_packet',packet:{packet_state:'NO_MEANINGFUL_TECHNICAL_CHANGE'}}}),true);
});
test('review of an empty observed check records time but leaves later arrivals unread',()=>{
  const state=reviewUpdates(followStock(emptyWatchlist(),'XYZ'),'XYZ',[],time);
  assert.equal(state.reviewedAt.XYZ,time);
  assert.equal(isUnread(state,'XYZ',update()),true);
});
test('withdrawn/expired items disappear without erasing history or reviewing corrected evidence',()=>{
  const technical=update('technical');
  const state=reviewUpdates(followStock(emptyWatchlist(),'XYZ'),'XYZ',[technical],time);
  const retracted=[];
  assert.equal(retracted.filter(row=>isUnread(state,'XYZ',row)).length,0);
  assert.equal(isUnread(state,'XYZ',update('technical','same','corrected')),true);
  assert.equal(isUnread(state,'XYZ',technical),false);
});
test('legacy review migration baselines only already reviewed content without inventing a time',()=>{
  const state=readWatchlist(JSON.stringify({symbols:['XYZ'],seen:{XYZ:['same']},communitySeen:{XYZ:['same']}}));
  const news=update(),discussion=update('community'),newItem=update('news','new');
  const data={stocks:[{symbol:'XYZ',news:{items:[news,newItem]},community:{items:[discussion]}}]};
  const next=readWatchlist(JSON.stringify(baselineLegacyReviews(state,data)));
  assert.equal(next.reviewedAt,undefined);
  assert.equal(next.receipts.XYZ[news.id].reviewed_at,null);
  assert.equal(isUnread(next,'XYZ',news),false);
  assert.equal(isUnread(next,'XYZ',newItem),true);
  assert.equal(isUnread(next,'XYZ',update('news','same','changed')),true);
  assert.equal(baselineLegacyReviews(next,data),next);
});
test('partial/page reviews merge rather than forgetting old stories and validate saved receipts',()=>{
  let state=markReviewed(followStock(emptyWatchlist(),'XYZ'),'XYZ',[{story_id:'old'}]);
  state=markReviewed(state,'XYZ',[{story_id:'new'}]);
  assert.deepEqual(state.seen.XYZ,['old','new']);
  assert.throws(()=>readWatchlist(JSON.stringify({...state,receipts:{XYZ:{'news:old':{revision:'x',reviewed_at:'nonsense'}}}})));
  assert.throws(()=>reviewUpdates(state,'XYZ',[],'nonsense'));
});
test('unified load bounds request symbols/page and preserves unavailable failures',async()=>{
  const payload={as_of:time,offset:12,page_size:12,stocks:[{symbol:'XYZ',status:'unavailable',news:null,community:null,technical:null}],news_sources:[],community_sources:[]};
  const data=await loadIntelligence(['XYZ'],12,undefined,async(url,options)=>{
    assert.equal(url,'/api/watchlists/intelligence');
    assert.deepEqual(JSON.parse(options.body),{symbols:['XYZ'],offset:12,page_size:12});
    assert.equal(options.cache,'no-store');return {ok:true,json:async()=>payload};
  });
  assert.deepEqual(data,payload);
  await assert.rejects(loadIntelligence(['XYZ'],0,undefined,async()=>({ok:false})),/unavailable/);
});
