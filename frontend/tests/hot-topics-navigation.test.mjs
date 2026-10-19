import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
const require=createRequire(import.meta.url);
function load(file,overrides={}){
 const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 const exports={};new Function('require','exports',code)(name=>overrides[name]??require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);return exports;
}
const render=(Component,props={},language='en')=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools(language)},React.createElement(Component,props)));
const Thumbnail=load('../app/components/news/NewsThumbnail.tsx').default;
const TopStory=load('../app/components/news/TopStory.tsx',{'./NewsThumbnail':Thumbnail,'../stock/LivePrice':{TickerMovement:()=>{throw Error('No additional quote consumer');}}}).default;
const hot=load('../app/components/news/HotTopics.tsx',{'./TopStory':TopStory});
const item=id=>{const article={id:'article-'+id,title:'Original headline '+id+' rất dài '.repeat(12),source_name:'Original Publisher',url:'https://publisher.example/'+id,published_at:'2026-10-19T02:10:00Z',first_seen_at:'2026-10-19T02:15:00Z',tickers:[],topics:[],sectors:[]};return {story:{id,source_count:2},representative_article:article,articles:[article]};};
const stories=['rank-1','rank-2','rank-3','rank-4'].map(item);

test('Hot Topics keeps backend order, representative/source text, original URLs and distinct Story IDs',()=>{
 const html=render(hot.HotTopicsView,{stories:[stories[0],stories[0],...stories.slice(1)],error:false,retry(){},expanded:false,toggle(){}});
 assert.equal((html.match(/data-story-id=/g)||[]).length,4);
 let index=-1;for(const s of stories){const next=html.indexOf('data-story-id="'+s.story.id+'"');assert.ok(next>index);index=next;assert.ok(html.includes(s.representative_article.url));}
 assert.match(html,/Original Publisher/);assert.match(html,/rel="noopener noreferrer"/);
 assert.match(html,/hot-topic-third/);assert.match(html,/hot-topic-extra/);assert.match(html,/aria-expanded="false"/);
 assert.doesNotMatch(html,/<img|SSI-certified|DEMO|line-clamp/);
 assert.match(render(hot.HotTopicsView,{stories,error:false,retry(){},expanded:true,toggle(){}}),/aria-expanded="true"/);
});

test('loading, confirmed empty, failed initial read and retained previous results stay distinct in both languages',()=>{
 for(const language of ['en','vi']){
  const tools=localeTools(language),base={retry(){},toggle(){},expanded:false};
  assert.ok(render(hot.HotTopicsView,{...base,stories:null,error:false},language).includes(tools.t('Loading publisher reporting…')));
  const empty=render(hot.HotTopicsView,{...base,stories:[],error:false},language);assert.ok(empty.includes(tools.t('No stories with independent publisher coverage qualify yet.')));assert.doesNotMatch(empty,/aria-expanded/);
  const failed=render(hot.HotTopicsView,{...base,stories:null,error:true},language);assert.match(failed,/role="alert"/);assert.ok(failed.includes(tools.t('Retry')));assert.ok(!failed.includes(tools.t('No stories with independent publisher coverage qualify yet.')));
  const previous=render(hot.HotTopicsView,{...base,stories,error:true},language);assert.ok(previous.includes(tools.t('Previously loaded headlines are shown below.')));assert.match(previous,/Original headline rank-1/);
 }
});

test('missing publication time is First seen, missing images do not suppress stories and ticker links stay separate',()=>{
 const data=item('ticker');data.representative_article.published_at=null;data.representative_article.tickers=['XYZ'];
 data.ticker_associations=[{symbol:'XYZ',article_id:data.representative_article.id,article_title:data.representative_article.title,kind:'explicit_stock',matched_text:'xyz',policy:'issuer-context-v2'}];
 const html=render(hot.HotTopicsView,{stories:[data],error:false,retry(){},expanded:false,toggle(){}});
 assert.match(html,/First seen/);assert.match(html,/href="\/stocks\/XYZ"/);assert.doesNotMatch(html,/<a[^>]*>[^<]*<a/);
 const unsafe=structuredClone(data);unsafe.representative_article.url='javascript:alert(1)';
 assert.doesNotMatch(render(hot.HotTopicsView,{stories:[unsafe],error:false,retry(){},expanded:false,toggle(){}}),/href="javascript:/);
});

const passthrough=({children})=>children;
const shell=load('../app/components/app-shell/AppShell.tsx',{'../ui/button':{Button:passthrough},'../stock/TickerSearch':()=>null,'../market/MarketSearch':{MarketSearchProvider:passthrough,useMarketSearch:()=>({setQuery(){}})},'../stock/StockUniverse':{StockUniverse:passthrough},'next-themes':{ThemeProvider:passthrough,useTheme:()=>({resolvedTheme:'dark',setTheme(){}})}});
for(const [path,href] of [['/','/'],['/stocks/FPT','/'],['/indices/VNINDEX','/'],['/news','/news'],['/news/stories/one','/news'],['/watchlist','/watchlist']])test('primary navigation has exactly three visible destinations and correct active state: '+path,()=>{
 for(const language of ['en','vi']){
  const html=render(shell.PrimaryNavigation,{path},language);
  assert.equal((html.match(/<a /g)||[]).length,3);assert.equal((html.match(/aria-current="page"/g)||[]).length,1);
  const active=html.match(/<a\b[^>]*aria-current="page"[^>]*>/)?.[0];assert.ok(active);assert.ok(active.includes('href="'+href+'"'));
  for(const label of language==='vi'?['Thị trường','Tin tức','Theo dõi']:['Market','News','Watchlist']){assert.ok(html.includes('aria-label="'+label+'"'));assert.ok(html.includes('>'+label+'</span>'));}
  assert.doesNotMatch(html,/class="[^"]*\bhidden\b|<aside|role="menu"/);
 }
});

test('one context area defaults to Hot Topics; actual option callbacks retain separate datasets and keyboard controls',()=>{
 let selection='hot';const react={...React,useState(){return [selection,next=>selection=next];}};
 const Hot=()=>null,Focus=()=>null;
 const Context=load('../app/components/news/MarketNewsContext.tsx',{'./HotTopics':Hot,'./MarketFocus':Focus,react,'@/lib/i18n':{useLocale:()=>localeTools('en')}}).default;
 const find=(tree,predicate)=>{if(!tree||typeof tree!=='object')return; if(predicate(tree))return tree;for(const c of React.Children.toArray(tree.props?.children)){const match=find(c,predicate);if(match)return match;}};
 let tree=Context(),html=renderToStaticMarkup(tree);
 assert.match(html,/id="market-news-hot-option"[^>]*aria-pressed="true"/);
 assert.match(html,/id="market-news-focus-option"[^>]*aria-pressed="false"/);
 assert.match(html,/id="market-news-focus-panel"[^>]*hidden=""/);
 assert.match(html,/aria-controls="market-news-hot-panel"/);assert.match(html,/href="\/news"/);
 assert.doesNotMatch(html,/role="tab"|localStorage|DEMO/);
 assert.equal(find(tree,n=>n.type===Hot).props.active,true);assert.equal(find(tree,n=>n.type===Focus).props.active,false);
 find(tree,n=>n.props?.id==='market-news-focus-option').props.onClick();tree=Context();html=renderToStaticMarkup(tree);
 assert.equal(find(tree,n=>n.type===Hot).props.active,false);assert.equal(find(tree,n=>n.type===Focus).props.active,true);
 assert.match(html,/id="market-news-hot-panel"[^>]*hidden=""/);assert.match(html,/href="\/news\?view=briefing"/);
 find(tree,n=>n.props?.id==='market-news-hot-option').props.onClick();tree=Context();
 assert.equal(find(tree,n=>n.type===Hot).props.active,true);assert.equal(find(tree,n=>n.type===Focus).props.active,false);
});

const flush=()=>new Promise(resolve=>setImmediate(resolve));
async function hotHarness(run,{focus=false}={}){
 const before=globalThis.fetch,values=[],effects=[],requests=[];let cursor=0,props={active:true,compact:true},view,refresh,stops=0;
 const react={useState(initial){const key=cursor++;if(!(key in values))values[key]=initial;return [values[key],next=>values[key]=typeof next==='function'?next(values[key]):next];},useEffect(fn,deps){const key=cursor++,old=effects[key];if(!old||deps.some((v,i)=>v!==old.deps[i]))effects[key]={fn,deps,pending:true,cleanup:old?.cleanup};}};
 const Hot=load(focus?'../app/components/news/MarketFocus.tsx':'../app/components/news/HotTopics.tsx',{react,'@/lib/i18n':{useLocale:()=>localeTools('en')},'../stock/LivePrice':{LivePrices:passthrough},'./TopStory':()=>null,'@/lib/cacheRefresh':{cacheRefresh(fn){refresh=fn;return()=>{stops++;};}}}).default;
 globalThis.fetch=(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));
 const render=(next={})=>{props={...props,...next};cursor=0;view=Hot(props);for(const e of effects.filter(Boolean))if(e.pending){e.cleanup?.();e.pending=false;e.cleanup=e.fn();}return view;};
 const cleanup=()=>effects.filter(Boolean).forEach(e=>e.cleanup?.());
 try{await run({requests,render,view:()=>view,refresh:()=>refresh(),stops:()=>stops});}finally{cleanup();globalThis.fetch=before;}
}

test('one exact persisted endpoint, coalesced cache refresh, original rank and no snapshots summed',async()=>hotHarness(async h=>{
 h.render();assert.equal(h.requests.length,1);assert.equal(h.requests[0].url,'/api/news/hot?limit=4');assert.equal(h.requests[0].options.cache,'no-store');
 h.refresh();assert.equal(h.requests.length,1);
 h.requests[0].resolve({ok:true,json:async()=>[stories[1],stories[0],stories[1]]});await flush();h.render();
 assert.deepEqual(h.view().props.stories.map(s=>s.story.id),['rank-2','rank-1']);
 h.refresh();h.requests[1].resolve({ok:true,json:async()=>[stories[3]]});await flush();h.render();
 assert.deepEqual(h.view().props.stories.map(s=>s.story.id),['rank-4']);
}));

test('inactive option aborts read, removes refresh subscription and ignores late results; reactivation can retry',async()=>hotHarness(async h=>{
 h.render({active:false});assert.equal(h.requests.length,0);
 h.render({active:true});const old=h.requests[0];h.render({active:false});assert.ok(old.options.signal.aborted);assert.equal(h.stops(),1);
 old.resolve({ok:true,json:async()=>stories});await flush();h.render();assert.equal(h.view().props.stories,null);
 h.render({active:true});h.requests[1].resolve({ok:false});await flush();h.render();assert.equal(h.view().props.error,true);
 h.view().props.retry();h.render();assert.equal(h.requests.length,3);h.requests[2].resolve({ok:true,json:async()=>[]});await flush();h.render();assert.equal(h.view().props.error,false);assert.deepEqual(h.view().props.stories,[]);
}));

test('failed refresh preserves earlier source evidence without labeling it fresh',async()=>hotHarness(async h=>{
 h.render();h.requests[0].resolve({ok:true,json:async()=>stories});await flush();h.render();
 h.refresh();h.requests[1].reject(Error('read failed'));await flush();h.render();assert.equal(h.view().props.error,true);assert.deepEqual(h.view().props.stories,stories);
}));

test('Market Focus retains its two existing feed contracts and 24-hour qualified subset, independently of Hot Topics',async()=>hotHarness(async h=>{
 h.render({active:false});assert.equal(h.requests.length,0);
 h.render({active:true});assert.deepEqual(h.requests.map(r=>r.url),['/api/news/feed?research_category=MARKET_BRIEF&limit=6','/api/news/feed?research_category=COMPANY&limit=6']);
 const record=(id,hours,category='MARKET_BRIEF')=>{const row=item(id);row.research_category=category;row.representative_article.published_at=new Date(Date.now()-hours*3600000).toISOString();return row;};
 const recent=record('qualified-market',1),old=record('older-than-24h',25),future=record('future',-1),unqualified=record('unqualified-company',1,'COMPANY');
 h.requests[0].resolve({ok:true,json:async()=>[old,recent,future]});h.requests[1].resolve({ok:true,json:async()=>[unqualified,recent]});await flush();h.render();
 const html=renderToStaticMarkup(h.view());assert.match(html,/Original headline qualified-market/);assert.doesNotMatch(html,/Original headline older-than-24h|Original headline future|Original headline unqualified-company/);
 assert.equal((html.match(/data-story-id=/g)||[]).length,1);assert.match(html,/Last 24 hours/);
 h.render({active:false});assert.ok(h.requests.every(r=>r.options.signal.aborted));assert.equal(h.stops(),1);
},{focus:true}));

test('responsive styles expose all primary links, cap initial headlines at 3/2 and preserve theme tokens and focus',()=>{
 const css=readFileSync(new URL('../app/market-workspace.css',import.meta.url),'utf8');
 const postcss=require('postcss'),ast=postcss.parse(css);
 const rules=selector=>{const out=[];ast.walkRules(selector,r=>out.push(r));return out;};
 const prop=(r,key)=>r.nodes.find(n=>n.prop===key)?.value;
 assert.ok(rules('.woofi-primary-nav').every(r=>prop(r,'display')!=='none'));
 assert.ok(rules('.woofi-primary-nav').some(r=>r.parent.params==='(max-width:900px)'&&prop(r,'grid-template-columns')==='repeat(3,minmax(0,1fr))'));
 assert.equal(prop(rules('.hot-topics-stories:not([data-expanded=true]) .hot-topic-extra')[0],'display'),'none');
 assert.ok(rules('.hot-topics-stories:not([data-expanded=true]) .hot-topic-third').some(r=>r.parent.params==='(max-width:800px)'&&prop(r,'display')==='none'));
 assert.ok(rules('.woofi-primary-nav a[aria-current=page]').some(r=>prop(r,'color')==='var(--primary)'&&prop(r,'border-bottom-color')==='var(--primary)'));
 assert.match(css,/\.market-news-context button:focus-visible/);assert.match(css,/\.market-news-context \[hidden\]\{display:none!important\}/);
});

test('homepage news remains available when equity metadata loads, fails or is empty, without duplicating the healthy overview module',()=>{
 const News=()=>React.createElement('div',{'data-news-context':'present'});
 const Overview=load('../app/components/market/MarketOverview.tsx',{'../news/MarketNewsContext':News,'../stock/LivePrice':{useLivePrices:()=>({data:null,failed:true})},'./FutureData':()=>null}).default;
 let result={loading:false,error:false,data:{items:[{symbol:'XYZ'}],total:1,offset:0,status:'healthy'}},selected='overview';
 const Workspace=load('../app/components/market/MarketWorkspace.tsx',{
  react:{...React,useState(initial){return React.useState(initial==='overview'?selected:initial);}},
  '@/lib/useEquityPage':{useEquityPage:()=>result},'./MarketSearch':{useMarketSearch:()=>({query:''})},
  '../stock/useRecentSearches':{useRecentSearches:()=>({remember(){}})},'../stock/LivePrice':{LivePrices:passthrough},'../stock/QuoteMap':()=>React.createElement('div',{'data-board':'preserved'}),
  './WorkspaceNav':{__esModule:true,default:()=>null,workspaceView:()=>selected},'./MarketContext':()=>null,'./MarketOverview':Overview,'../news/MarketNewsContext':News,'./FutureData':()=>null,
 }).default;
 const healthy=render(Workspace);assert.equal((healthy.match(/data-news-context/g)||[]).length,1);
 assert.ok(healthy.indexOf('market-sample')<healthy.indexOf('data-news-context'));assert.ok(healthy.indexOf('data-news-context')<healthy.indexOf('market-mover-grid'));
 for(const patch of [{loading:true,data:null},{error:true,data:null},{data:{items:[],offset:0,total:0}}]){const previous=result;result={...result,...patch};assert.equal((render(Workspace).match(/data-news-context/g)||[]).length,1);result=previous;}
 for(const view of ['board','heatmap']){selected=view;const html=render(Workspace);assert.doesNotMatch(html,/data-news-context/);assert.match(html,/data-board="preserved"/);}
});
