import test from 'node:test';
import assert from 'node:assert/strict';
import {newsSymbols,relatedTickers,quoteStatus} from '../lib/newsPresentation.ts';
import {movement} from '../lib/live-market.ts';
import {cacheRefresh} from '../lib/cacheRefresh.ts';
test('news requests one bounded union of evidenced, visible tickers, never invents association',()=>{
 const story=symbols=>({representative_article:{id:'a',title:'Original issuer headline',tickers:symbols},ticker_associations:symbols.map(symbol=>({symbol,article_id:'a',article_title:'Original issuer headline',kind:'explicit_stock',matched_text:symbol,policy:'issuer-context-v2'}))});
 const stories=[story(['AAA','AAA','BBB','CCC','DDD']),story(['BBB','EEE'])];
 assert.deepEqual(relatedTickers(stories[0]),['AAA','BBB','CCC']);assert.deepEqual(newsSymbols(stories),['AAA','BBB','CCC','EEE']);
 assert.deepEqual(newsSymbols([story([])]),[]);
 assert.equal(newsSymbols(Array.from({length:60},(_,n)=>story(['X'+n]))).length,50);
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
