import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
const require=createRequire(import.meta.url);
function component(file, overrides={}) {
  const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{
    filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
  const exports={};
  new Function('require','exports',code)(name=>overrides[name] || require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
  return exports.default;
}
const TopStory=component('../app/components/news/TopStory.tsx');
const article={id:'a',title:'Issuer update',url:'https://example.org/a',source_name:'Publisher',published_at:null,first_seen_at:'2026-10-06T05:00:00Z',tickers:[],topics:[],sectors:[]};
test('news thumbnail preserves full aspect and missing/unsafe images leave no frame',()=>{
  const render=image=>renderToStaticMarkup(React.createElement(TopStory,{item:{story:{id:'s',representative_title:article.title,source_count:2},representative_article:{...article,thumbnail_url:image},articles:[article],research_category:'COMPANY'}}));
  assert.match(render('https://example.org/image.jpg'),/object-contain/);
  assert.doesNotMatch(render(null),/<img|object-contain/);
  assert.doesNotMatch(render('javascript:alert(1)'),/<img/);
  assert.match(render(null),/Company/);
});
test('Explore renders a bounded universe with direct research links and no add prerequisite',()=>{
  const rows=Array.from({length:60},(_,n)=>({symbol:`X${n}`,exchange:n%2?'HNX':'HOSE',display_name_en:'Issuer'}));
  const Picker=component('../app/components/TickerPicker.tsx',{
    './stock/useRecentSearches':{useRecentSearches:()=>({recent:[],remember:()=>{}})},
    './stock/StockSearch':()=>React.createElement('input',{role:'combobox'}),
    'next/navigation':{useRouter:()=>({push:()=>{}})},
    './stock/StockUniverse':{useStocks:()=>({stocks:rows,loading:false,error:'',status:'healthy'})},
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
    './stock/StockUniverse':{useStocks:()=>({stocks:[],loading:true,error:'',status:'not_attempted'})},
    './ui/button':{Button:({variant,...props})=>React.createElement('button',props)},
    './mascot/Mascot':{MascotState:({children})=>children}});
  const html=renderToStaticMarkup(React.createElement(Picker));
  assert.match(html,/Universe count unavailable/);
  assert.doesNotMatch(html,/0 Vietnam equities/);
});

test('shared stock search initially stays empty instead of rendering the market directory',()=>{
  const Search=component('../app/components/stock/StockSearch.tsx',{'./useRecentSearches':{useRecentSearches:()=>({recent:[],remember:()=>{}})}});
  const html=renderToStaticMarkup(React.createElement(Search,{stocks:Array.from({length:1522},(_,n)=>({symbol:`X${n}`,exchange:'HOSE'})),label:'Stock to follow',onSelect:()=>{}}));
  assert.match(html,/role="combobox"/);
  assert.match(html,/aria-expanded="false"/);
  assert.doesNotMatch(html,/role="option"|<select/);
});

test('Hot Topics selects only same-cluster images and excludes no-image stories',()=>{
 const render=item=>renderToStaticMarkup(React.createElement(TopStory,{item,requireImage:true}));
 const base={story:{id:'s',source_count:2},representative_article:article,articles:[article]};
 assert.equal(render(base),'');
 const sibling={...article,id:'b',thumbnail_url:'https://example.org/sibling.jpg'};
 assert.match(render({...base,articles:[article,sibling]}),/sibling.jpg/);
 assert.doesNotMatch(render({...base,thumbnail_url:'https://other.example/unrelated.jpg'}),/<img/);
 const preferred={...article,thumbnail_url:'https://example.org/preferred.jpg'};
 assert.match(render({...base,representative_article:preferred,articles:[preferred,sibling]}),/src="https:\/\/example.org\/preferred.jpg"/);
});

test('Explore hero links to index research, enlarges mascot, and keeps provider details out',()=>{
 const Market=component('../app/components/ExploreMarket.tsx',{
  './mascot/Mascot':{MascotIllustration:({size})=>React.createElement('span',{'data-mascot-size':size}),MascotState:({children})=>children},
  './news/TopStory':()=>null});
 const html=renderToStaticMarkup(React.createElement(Market));
 assert.match(html,/<header/);assert.match(html,/href="\/indices\/VNINDEX"/);assert.match(html,/data-mascot-size="128"/);
 assert.doesNotMatch(html,/SSI:FastConnect|Latest provider summary|panel flex/);
});

test('stock news archive link opens the semantic Company view',()=>{
 const News=component('../app/components/stock/StockNews.tsx',{
  '../news/ArticleRow':()=>null,'../news/SourceCoverage':()=>null});
 const html=renderToStaticMarkup(React.createElement(News,{ticker:'XYZ'}));
 assert.match(html,/href="\/news\?ticker=XYZ&amp;view=company"/);
});
