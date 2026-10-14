import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {transformSync} from 'next/dist/build/swc/index.js';
import {marketFocusItems} from '../lib/marketFocus.ts';
import {qualifiedAssociations} from '../lib/newsPresentation.ts';
import {emptyWatchlist,reviewUpdates,isUnread} from '../lib/watchlist.ts';
const require=createRequire(import.meta.url);
function load(file,overrides={}){
 const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 // Route files may only export Next.js page fields. Inspect private helpers in
 // this SSR harness without introducing invalid production page exports.
 const helpers=file.endsWith('/watchlist/page.tsx')?'\nexports.UpdateSection=UpdateSection;exports.ReviewEvidence=ReviewEvidence;':'';
 const exports={};new Function('require','exports',code+helpers)(name=>overrides[name]||require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);return exports;
}
const article={id:'a',title:'Original issuer headline',url:'https://publisher.example/a',source_name:'Publisher',published_at:'2026-10-11T07:00:00Z',first_seen_at:'2026-10-11T07:05:00Z',tickers:['MCH'],topics:[],sectors:[]};
const proof={symbol:'MCH',article_id:'a',article_title:article.title,article_url:article.url,kind:'explicit_stock',matched_text:'mch',policy:'issuer-context-v2',evidence_origin:'publisher_text',evidence_excerpt:'Cổ phiếu MCH bị bán ròng.',text_receipt_id:'receipt',text_hash:'hash',text_observed_at:'2026-10-11T07:05:00Z'};

test('body associations require current attributed receipt evidence; old policy and corrected URLs abstain',()=>{
 assert.equal(qualifiedAssociations(article,[proof]).length,1);
 for(const patch of [{policy:'issuer-context-v1'},{text_hash:null},{evidence_excerpt:null},{text_receipt_id:null},{article_url:'https://publisher.example/correction'}])assert.deepEqual(qualifiedAssociations(article,[{...proof,...patch}]),[]);
});
test('Market Focus selects at most three recent finance stories, with no forum or unverified company inputs',()=>{
 const rows=[{story:{id:'older'},representative_article:{...article,published_at:'2026-10-09T07:00:00Z'},research_category:'MARKET_BRIEF'},
 {story:{id:'company'},representative_article:article,research_category:'COMPANY',ticker_associations:[proof]},
 {story:{id:'recent'},representative_article:{...article,published_at:'2026-10-11T08:00:00Z'},research_category:'MARKET_BRIEF'},
 {story:{id:'unverified'},representative_article:article,research_category:'COMPANY'},
 {story:{id:'forum'},representative_article:article,research_category:'COMMUNITY'}];
 assert.deepEqual(marketFocusItems([...rows,rows[2]]).map(r=>r.story.id),['recent','company','older']);
 assert.deepEqual(marketFocusItems(rows.slice(3)),[]);
});
test('representative headline opens safe publisher directly; ticker anchors are siblings and no Evidence action remains',()=>{
 const Thumbnail=load('../app/components/news/NewsThumbnail.tsx').default;
 const TopStory=load('../app/components/news/TopStory.tsx',{'./NewsThumbnail':Thumbnail,'../stock/LivePrice':{TickerMovement:()=>null}}).default;
 const item={story:{id:'s',source_count:2},representative_article:article,articles:[article],ticker_associations:[proof]};
 const html=renderToStaticMarkup(React.createElement(TopStory,{item}));
 assert.match(html,/href="https:\/\/publisher.example\/a" target="_blank" rel="noopener noreferrer"/);
 assert.match(html,/href="\/stocks\/MCH"/);assert.doesNotMatch(html,/Evidence|news\/stories|publisher groups|View other reporting/);
 assert.doesNotMatch(html,/<a[^>]*>[^<]*<a/);assert.equal((html.match(/<h3/g)||[]).length,1);
 const unsafe=renderToStaticMarkup(React.createElement(TopStory,{item:{...item,representative_article:{...article,url:'javascript:alert(1)'}}}));assert.doesNotMatch(unsafe,/href="javascript:/);
});

const Watchlist=load('../app/watchlist/page.tsx',{'../components/ui/button':{Button:()=>null},'../components/mascot/Mascot':{MascotState:()=>null},'../components/stock/StockSearch':()=>null,'../components/stock/LivePrice':{LivePrices:({children})=>children,LivePrice:()=>null},'../components/stock/TechnicalInsights':{TechnicalInsightsView:()=>null},'../components/news/ArticleRow':()=>null});
const updates=Array.from({length:5},(_,n)=>({id:'news:'+n,entity_id:''+n,kind:'news',title:'Unread headline '+n,occurred_at:article.first_seen_at,revision:'v1',url:article.url,evidence:[article]}));
test('compact Watchlist leaves every loaded unread item visible, with review in secondary controls and no empty sections',()=>{
 const state={...emptyWatchlist(),symbols:['MCH']};
 const props={label:'News',page:{items:updates,has_more:false,truncated:false},symbol:'MCH',state,disabled:false};
 const html=renderToStaticMarkup(React.createElement(Watchlist.UpdateSection,props));
 assert.equal((html.match(/data-unread="true"/g)||[]).length,5);
 assert.doesNotMatch(html,/Mark reviewed|Review displayed|publisher groups|View source evidence/);
 assert.equal(renderToStaticMarkup(React.createElement(Watchlist.UpdateSection,{...props,page:{...props.page,items:[]}})),'');
 const reviewed=reviewUpdates(state,'MCH',[updates[0]]);assert.ok(!isUnread(reviewed,'MCH',updates[0]));assert.ok(isUnread(reviewed,'MCH',updates[1]));
 const reviewHtml=renderToStaticMarkup(React.createElement(Watchlist.ReviewEvidence,{items:updates,symbol:'MCH',state:reviewed,disabled:false,review(){}}));
 assert.equal((reviewHtml.match(/>Mark reviewed<\/button>/g)||[]).length,4);assert.match(reviewHtml,/disabled=""[^>]*>Reviewed<\/button>/);
});
