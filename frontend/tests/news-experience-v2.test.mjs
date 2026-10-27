import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
const require=createRequire(import.meta.url);
function component(file,mocks={}){
 const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 const exports={};new Function('require','exports',code)(name=>mocks[name]||require(name.startsWith('@/lib/')?'../lib/'+name.slice(6)+'.ts':name),exports);return exports.default;
}
const render=(Component,props,language='en')=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(Component,props)));
const article={id:'original',title:'Original publisher headline',url:'https://publisher.example/original',source_name:'Publisher A',published_at:'2026-10-06T05:00:00Z',first_seen_at:'2026-10-06T06:00:00Z',last_seen_at:'2026-10-09T05:00:00Z',tickers:[],topics:[],sectors:[]};
const item={story:{id:'one',source_count:2},research_category:'INDUSTRY',representative_article:article,articles:[article,{...article,id:'later',title:'Other publisher headline',source_name:'Publisher B',url:'https://publisher.example/later',published_at:null,first_seen_at:'2026-10-07T05:00:00Z'}]};

test('news cards retain primary story details but omit expandable provenance in EN/VI',()=>{
 const Thumbnail=component('../app/components/news/NewsThumbnail.tsx');
 const Card=component('../app/components/news/TopStory.tsx',{'./NewsThumbnail':Thumbnail,'../stock/LivePrice':{TickerMovement:()=>null}});
 for(const language of ['en','vi']){
  const before=JSON.stringify(item);
  const html=render(Card,{item,compact:true,reserveThumbnailSpace:true},language);
  assert.equal((html.match(/Original publisher headline/g)||[]).length,1);
  assert.doesNotMatch(html,/Other publisher headline|independent publishers|news\/stories\/one|<details/);
  assert.match(html,/Publisher A/);
  assert.match(html,/dateTime="2026-10-06T05:00:00Z"/);
  assert.doesNotMatch(html,/dateTime="2026-10-07T05:00:00Z"|dateTime="2026-10-09T05:00:00Z"/);
  assert.doesNotMatch(html,/Latest reporting|Sources and timestamps|First seen|View source archive|Nguồn và thời điểm|Ghi nhận lần đầu|Xem kho tin nguồn/i);
  assert.match(html,/data-thumbnail-status="unavailable"/);
  assert.equal(JSON.stringify(item),before);
  assert.doesNotMatch(render(Card,{item:{...item,representative_article:{...article,url:'javascript:alert(1)'}},reserveThumbnailSpace:true},language),/href="javascript:/);
 }
});

test('News renders one chronological list with editorial rows only, and distinct loading/empty/stale failure states',()=>{
 let state={page:{items:[item,{...item,story:{id:'one',source_count:2}},{...item,story:{id:'forum',source_count:1},research_category:'COMMUNITY',representative_article:{...article,title:'Discussion must stay out'}}],as_of:'2026-10-07T06:00:00Z',has_more:true},loading:false,error:false,loadMore(){}};
 const News=component('../app/news/page.tsx',{
  '../components/mascot/Mascot':{MascotState:({children,role})=>React.createElement('div',{role},children)},
  '../components/ui/button':{Button:props=>React.createElement('button',props)},
  '../components/news/SourceCoverage':()=>null,
  '../components/news/TopStory':({item,showSources})=>React.createElement('article',{'data-sources':String(Boolean(showSources))},item.representative_article.title),
  '../components/stock/LivePrice':{LivePrices:({children})=>children},
  '@/lib/useNewsArchive':{useNewsArchive:()=>state}});
 for(const language of ['en','vi']){
  const t=localeTools(language).t;
  let html=render(News,{},language);
  assert.equal((html.match(/<article/g)||[]).length,1);
  assert.match(html,/<ol class="news-results news-feed"/);assert.match(html,/data-sources="false"/);
  assert.ok(html.includes(t('Latest reporting first')));assert.ok(html.includes(t('Feed snapshot')));
  assert.match(html,/role="search"/);assert.doesNotMatch(html,/<select|news-filter-toolbar|Apply filters|Clear all/);
  if(language==='vi')assert.match(html,/Tìm mã cổ phiếu, doanh nghiệp, ngành, tin tức/);
  assert.doesNotMatch(html,/Community Pulse|Discussion must stay out|news-card-featured|news-results-grid/);
  assert.ok(html.includes(t('Show more')));
  const loaded=state.page;state={...state,error:true};html=render(News,{},language);
  assert.ok(html.includes(t('Previously loaded headlines are shown below.')));assert.match(html,/Original publisher headline/);
  state={...state,page:null,loading:true,error:false};assert.ok(render(News,{},language).includes(t('Loading news…')));
  state={...state,page:{...loaded,items:[]},loading:false};assert.ok(render(News,{},language).includes(t('No qualifying recent reporting matches this view. Coverage may be incomplete.')));
  state={...state,error:true};html=render(News,{},language);assert.ok(html.includes(t('News is temporarily unavailable.')));assert.ok(!html.includes(t('No qualifying recent reporting matches this view. Coverage may be incomplete.')));
  state={...state,page:loaded,error:false};
 }
});
