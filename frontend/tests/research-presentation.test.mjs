import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
const require=createRequire(import.meta.url);
function component(file, overrides={}) {
  overrides={'./stock/LivePrice':{LivePrices:({children})=>children,LivePrice:()=>null},
    '@/lib/useLiveMarket':{useLiveIndex:()=>({data:null,failed:false})},...overrides};
  const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{
    filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
  const exports={};
  new Function('require','exports',code)(name=>overrides[name] || require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
  return exports.default;
}
const NewsThumbnail=component('../app/components/news/NewsThumbnail.tsx');
const TopStory=component('../app/components/news/TopStory.tsx',{'./NewsThumbnail':NewsThumbnail});
const article={id:'a',title:'Issuer update',url:'https://example.org/a',source_name:'Publisher',published_at:null,first_seen_at:'2026-10-06T05:00:00Z',tickers:[],topics:[],sectors:[]};
test('news rows render source images and hide missing or unsafe image stories',()=>{
  const render=image=>renderToStaticMarkup(React.createElement(TopStory,{item:{story:{id:'s',representative_title:article.title,source_count:2},representative_article:{...article,thumbnail_url:image},articles:[article],research_category:'COMPANY'}}));
  assert.match(render('https://example.org/image.jpg'),/object-cover/);
  assert.equal(render(null),'');
  assert.equal(render('javascript:alert(1)'),'');
  assert.doesNotMatch(render('javascript:alert(1)'),/src="javascript:/);
  assert.match(render('https://example.org/image.jpg'),/Company/);
});
test('Explore renders a bounded universe with direct research links and no add prerequisite',()=>{
  const rows=Array.from({length:60},(_,n)=>({symbol:`X${n}`,exchange:n%2?'HNX':'HOSE',display_name_en:'Issuer'}));
  const Picker=component('../app/components/TickerPicker.tsx',{
    './stock/useRecentSearches':{useRecentSearches:()=>({recent:[],remember:()=>{}})},
    './stock/StockSearch':()=>React.createElement('input',{role:'combobox'}),
    'next/navigation':{useRouter:()=>({push:()=>{}})},
    '@/lib/useEquityPage':{useEquityPage:()=>({data:{items:rows.slice(0,10),total:60,total_universe:60,offset:0,limit:10,status:'healthy'},loading:false,error:false})},
    './ui/button':{Button:({variant,...props})=>React.createElement('button',props)},
    './mascot/Mascot':{MascotState:({children})=>children}});
  const html=renderToStaticMarkup(React.createElement(Picker));
  assert.match(html,/Explore stocks/);
  assert.doesNotMatch(html,/Available stocks|Validate and add/);
  assert.equal((html.match(/href="\/stocks\//g)||[]).length,10);
  assert.match(html,/of 60 results/);
});

test('Explore does not present an unknown universe count as zero',()=>{
  const Picker=component('../app/components/TickerPicker.tsx',{
    './stock/useRecentSearches':{useRecentSearches:()=>({recent:[],remember:()=>{}})},
    './stock/StockSearch':()=>React.createElement('input',{role:'combobox'}),
    'next/navigation':{useRouter:()=>({push:()=>{}})},
    '@/lib/useEquityPage':{useEquityPage:()=>({data:null,loading:true,error:false})},
    './ui/button':{Button:({variant,...props})=>React.createElement('button',props)},
    './mascot/Mascot':{MascotState:({children})=>children}});
  const html=renderToStaticMarkup(React.createElement(Picker));
  assert.match(html,/Universe count unavailable/);
  assert.doesNotMatch(html,/0 Vietnam equities/);
});

test('an unacquired empty metadata cache keeps universe and result counts unknown',()=>{
 const Picker=component('../app/components/TickerPicker.tsx',{
  './stock/useRecentSearches':{useRecentSearches:()=>({recent:[],remember:()=>{}})},
  './stock/StockSearch':()=>React.createElement('input',{role:'combobox'}),
  'next/navigation':{useRouter:()=>({push:()=>{}})},
  '@/lib/useEquityPage':{useEquityPage:()=>({data:{items:[],total:0,total_universe:0,offset:0,limit:10,status:'not_attempted'},loading:false,error:false})},
  './ui/button':{Button:({variant,...props})=>React.createElement('button',props)}});
 const html=renderToStaticMarkup(React.createElement(Picker));
 assert.match(html,/Universe count unavailable/);assert.match(html,/Equity metadata has not been acquired yet/);
 assert.doesNotMatch(html,/0 Vietnam equities|of 0 results/);
});

test('shared stock search initially stays empty instead of rendering the market directory',()=>{
  const Search=component('../app/components/stock/StockSearch.tsx',{'./useRecentSearches':{useRecentSearches:()=>({recent:[],remember:()=>{}})}});
  const html=renderToStaticMarkup(React.createElement(Search,{stocks:Array.from({length:1522},(_,n)=>({symbol:`X${n}`,exchange:'HOSE'})),label:'Stock to follow',onSelect:()=>{}}));
  assert.match(html,/role="combobox"/);
  assert.match(html,/aria-expanded="false"/);
  assert.doesNotMatch(html,/role="option"|<select/);
});

test('Hot Topics selects only same-cluster images and hides no-image stories',()=>{
 const render=item=>renderToStaticMarkup(React.createElement(TopStory,{item,requireImage:true}));
 const base={story:{id:'s',source_count:2},representative_article:article,articles:[article]};
 assert.equal(render(base),'');
 const sibling={...article,id:'b',thumbnail_url:'https://example.org/sibling.jpg'};
 assert.match(render({...base,articles:[article,sibling]}),/sibling.jpg/);
 assert.doesNotMatch(render({...base,thumbnail_url:'https://other.example/unrelated.jpg'}),/src="https:\/\/other.example/);
 const preferred={...article,thumbnail_url:'https://example.org/preferred.jpg'};
 assert.match(render({...base,representative_article:preferred,articles:[preferred,sibling]}),/src="https:\/\/example.org\/preferred.jpg"/);
});

test('Explore preserves its index hero and exposes the requested VN-Index detail link',()=>{
 const Market=component('../app/components/ExploreMarket.tsx',{
  './mascot/Mascot':{MascotIllustration:({size})=>React.createElement('span',{'data-mascot-size':size}),MascotState:({children})=>children},
  './news/TopStory':()=>null,'./news/CommunityPulse':()=>null});
 const html=renderToStaticMarkup(React.createElement(Market));
 assert.match(html,/<header/);assert.match(html,/VN-Index/);assert.match(html,/href="\/indices\/VNINDEX"/);assert.match(html,/data-mascot-size="128"/);
 assert.doesNotMatch(html,/SSI:FastConnect|Latest provider summary|panel flex/);
});

test('stock news archive link opens the semantic Company view',()=>{
 const News=component('../app/components/stock/StockNews.tsx',{
  '../news/SourceCoverage':()=>null,'../news/TopStory':()=>null});
 const html=renderToStaticMarkup(React.createElement(News,{ticker:'XYZ'}));
 assert.match(html,/Quick news · XYZ/);
 assert.match(html,/href="\/news\?ticker=XYZ&amp;view=company"/);
});

test('Quick News keeps one leading story, bounded related headlines and source evidence',()=>{
 const items=Array.from({length:7},(_,n)=>({story:{id:`s${n}`,representative_title:`Story ${n}`,source_count:2},
  representative_article:{...article,id:`a${n}`,title:`Story ${n}`,thumbnail_url:'https://example.org/image.jpg'},articles:[article]}));
 let state=0;
 const News=component('../app/components/stock/StockNews.tsx',{
  react:{...React,useEffect:()=>{},useState:initial=>[state++===0?items:initial,()=>{}]},
  '../news/SourceCoverage':()=>null,'../news/TopStory':TopStory});
 const html=renderToStaticMarkup(React.createElement(News,{ticker:'XYZ'}));
 assert.equal((html.match(/object-cover/g)||[]).length,1);
 for(let n=0;n<5;n++) assert.match(html,new RegExp(`Story ${n}`));
 assert.doesNotMatch(html,/Story 5|Story 6/);
 assert.match(html,/Show more headlines \(2\)/);
 assert.match(html,/Publisher/);
 assert.match(html,/2 independent sources/);
});

test('Quick News polls the cached attention-ranked Company feed and aborts on unmount',async()=>{
 const original={fetch:globalThis.fetch,setInterval:globalThis.setInterval,clearInterval:globalThis.clearInterval};
 let effect, poll, period, cleared;
 const requests=[];
 try {
  globalThis.fetch=async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>[]};};
  globalThis.setInterval=(callback,delay)=>{poll=callback;period=delay;return 42;};
  globalThis.clearInterval=id=>{cleared=id;};
  const News=component('../app/components/stock/StockNews.tsx',{
   react:{...React,useEffect:callback=>{effect=callback;},useState:initial=>[initial,()=>{}]},
   '../news/SourceCoverage':()=>null,'../news/TopStory':()=>null});
  renderToStaticMarkup(React.createElement(News,{ticker:'XYZ'}));
  const cleanup=effect();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(period,60_000);
  const url=new URL(requests[0].url,'https://local.example');
  assert.equal(url.pathname,'/api/news/feed');
  assert.equal(url.searchParams.get('research_category'),'COMPANY');
  assert.equal(url.searchParams.get('ranking'),'attention');
  assert.equal(url.searchParams.get('ticker'),'XYZ');
  assert.equal(url.searchParams.get('limit'),'10');
  poll();await new Promise(resolve=>setImmediate(resolve));
  assert.equal(requests.length,2);
  cleanup();assert.equal(cleared,42);
  assert.ok(requests.every(row=>row.options.signal.aborted));
 } finally {Object.assign(globalThis,original);}
});
