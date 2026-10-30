import test from 'node:test';
import assert from 'node:assert/strict';
import {newsSymbols,relatedTickers,allRelatedTickers,quoteStatus} from '../lib/newsPresentation.ts';
import {movement} from '../lib/live-market.ts';
import {cacheRefresh} from '../lib/cacheRefresh.ts';
import {editorialStories,latestReporting,newsArticleTime} from '../lib/newsPresentation.ts';

test('editorial feed keeps backend chronology and one row per Story, excluding discussions and unknown classifications',()=>{
 const rows=[{story:{id:'recent'},research_category:'MARKET_BRIEF'},{story:{id:'old'},research_category:'COMPANY'},{story:{id:'recent'},research_category:'INDUSTRY'},{story:{id:'discussion'},research_category:'COMMUNITY'},{story:{id:'unknown'}}];
 assert.deepEqual(editorialStories(rows).map(row=>row.story.id),['recent','old']);
 assert.equal(rows.length,5);
});

test('latest reporting follows documented publication or first observation, never a fetch recheck',()=>{
 const original={id:'original',published_at:'2026-10-06T05:00:00Z',first_seen_at:'2026-10-06T06:00:00Z',last_seen_at:'2026-10-09T05:00:00Z'};
 const later={id:'later',published_at:null,first_seen_at:'2026-10-07T05:00:00Z'};
 assert.deepEqual(latestReporting({representative_article:original,articles:[original,later]}),{kind:'First seen',value:'2026-10-07T05:00:00Z'});
 assert.deepEqual(newsArticleTime({...original,published_at:'bad'}),{kind:'First seen',value:original.first_seen_at});
 assert.deepEqual(newsArticleTime({...original,published_at:null,first_seen_at:'bad'}),{kind:'First seen',value:null});
});
test('news requests one bounded union of evidenced, visible tickers, never invents association',()=>{
 const story=symbols=>({representative_article:{id:'a',title:'Original issuer headline',tickers:symbols},ticker_associations:symbols.map(symbol=>({symbol,article_id:'a',article_title:'Original issuer headline',kind:'explicit_stock',matched_text:symbol,policy:'issuer-context-v2'}))});
 const stories=[story(['AAA','AAA','BBB','CCC','DDD']),story(['BBB','EEE'])];
 assert.deepEqual(relatedTickers(stories[0]),['AAA','BBB','CCC']);assert.deepEqual(newsSymbols(stories),['AAA','BBB','CCC','EEE']);
 assert.deepEqual(newsSymbols([story([])]),[]);
 assert.equal(newsSymbols(Array.from({length:60},(_,n)=>story(['X'+n]))).length,50);
});

test('all editorial categories expose companies proved in any current Story member, not just the representative',()=>{
 const a={id:'a',title:'VN-Index và cổ phiếu ABC',url:'https://publisher.example/a',tickers:['ABC']};
 const b={id:'b',title:'Ngành thép: cổ phiếu XYZ và DEF',url:'https://publisher.example/b',tickers:['XYZ','DEF']};
 const proof=(article,symbol)=>({symbol,article_id:article.id,article_title:article.title,article_url:article.url,kind:'explicit_stock',matched_text:symbol,policy:'issuer-context-v2'});
 for(const category of ['MARKET_BRIEF','INDUSTRY','COMPANY']){
  const item={research_category:category,representative_article:a,articles:[a,b],ticker_associations:[proof(a,'ABC'),proof(b,'XYZ'),proof(b,'DEF'),{...proof(b,'BAD'),article_title:'Wrong title'}]};
  assert.deepEqual(allRelatedTickers(item),['ABC','XYZ','DEF']);
  assert.deepEqual(allRelatedTickers({...item,representative_article:{...a,title:'Corrected title',tickers:[]}}),['XYZ','DEF']);
 }
});

test('unverified legacy tags, stale-title proofs and other articles never create stock chips or SSI demand',()=>{
 const article={id:'currency',title:'Lãi suất tiền đồng và giá USD liên ngân hàng liên tục giảm',tickers:['USD']};
 assert.deepEqual(relatedTickers({representative_article:article}),[]);
 assert.deepEqual(newsSymbols([{representative_article:article}]),[]);
 const proof={symbol:'USD',article_id:'currency',article_title:'Cổ phiếu USD tăng giá',kind:'explicit_stock',matched_text:'usd',policy:'issuer-context-v2'};
 for(const patch of [{},{article_title:article.title,policy:'old'},{article_title:article.title,article_id:'other'},{article_title:article.title,matched_text:''}]){
  assert.deepEqual(relatedTickers({representative_article:article,ticker_associations:[{...proof,...patch}]}),[]);
 }
});
test('zero is yellow, unknown neutral; stale date never becomes a current zero',()=>{
 assert.equal(movement(0).color,'unchanged');assert.equal(movement(null).color,'text-muted-foreground');assert.equal(movement(NaN).label,'Unavailable');
 const now=new Date('2026-10-11T05:00:00Z');const item={status:'fresh',snapshot:{trading_date:'2026-10-09',updated_at:'2026-10-09T07:45:00Z',session:'closed',change_percent:0}};
 assert.equal(quoteStatus(item,false,now),'stale');assert.equal(quoteStatus(undefined,false,now),'unavailable');
 item.snapshot.trading_date='2026-10-11';item.snapshot.updated_at=now.toISOString();item.snapshot.session='active';assert.equal(quoteStatus(item,false,now),'fresh');
 assert.equal(quoteStatus(item,false,new Date('2026-10-11T05:03:00Z')),'stale');assert.equal(quoteStatus(item,true,now),'stale');
});
test('cached News refreshes on interval, focus and tab return without acquisition; hidden pauses and cleanup removes all listeners',()=>{
 let calls=0,tick,cleared=false;const listeners={};const visibility={visibilityState:'visible',addEventListener:(k,v)=>listeners[k]=v,removeEventListener:k=>delete listeners[k]};const focus={addEventListener:(k,v)=>listeners[k]=v,removeEventListener:k=>delete listeners[k]};
 const stop=cacheRefresh(()=>calls++,visibility,focus,{set:fn=>{tick=fn;return 1;},clear:id=>{assert.equal(id,1);cleared=true;}});
 tick();assert.equal(calls,1);visibility.visibilityState='hidden';tick();listeners.focus();assert.equal(calls,1);
 visibility.visibilityState='visible';listeners.visibilitychange();listeners.focus();assert.equal(calls,3);stop();assert.ok(cleared);assert.deepEqual(listeners,{});
});
