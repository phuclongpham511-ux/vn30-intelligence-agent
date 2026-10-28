import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
const require=createRequire(import.meta.url);
function load(file,mocks={}){
 const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 const exports={};new Function('require','exports',code)(name=>mocks[name]||require(name.startsWith('@/lib/')?'../lib/'+name.slice(6)+'.ts':name),exports);return exports;
}
const now=new Date('2026-10-28T08:00:00Z');
const article={id:'a',title:'Issuer reports results',url:'https://publisher.example/report',source_name:'Publisher',published_at:now.toISOString(),tickers:['XYZ'],topics:[],sectors:[]};
const item={story:{id:'s',source_count:1},representative_article:article,articles:[article],ticker_associations:[{symbol:'XYZ',article_id:'a',article_title:article.title,article_url:article.url,kind:'explicit_stock',matched_text:'XYZ',policy:'issuer-context-v2',evidence_origin:'headline'}]};
test('compact News cards retain ticker and visible localized market movement without provenance',()=>{
 for(const [change,percent,label,vi] of [[100,1,'Up','Tăng'],[-100,-1,'Down','Giảm'],[0,0,'Unchanged','Không đổi']]){
  const snapshot={ticker:'XYZ',last_price:10000+change,reference_price:10000,change,change_percent:percent,trading_date:'2026-10-28',updated_at:now.toISOString(),session:'closed',source:'Synthetic test',price_unit:'VND'};
  const live=load('../app/components/stock/LivePrice.tsx',{'./TradingActivity':{default:()=>null},'@/lib/useLiveMarket':{useLiveMarket:()=>({data:{items:{XYZ:{status:'fresh',snapshot}}},failed:false})}});
  const Card=load('../app/components/news/TopStory.tsx',{'./NewsThumbnail':({children})=>typeof children==='function'?children(null):children,'../stock/LivePrice':{TickerMovement:props=>React.createElement(live.TickerMovement,{...props,now})}}).default;
  for(const [language,expected] of [['en',label],['vi',vi]]){
   const html=renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools(language)},React.createElement(live.LivePrices,{symbols:['XYZ'],interval:30000},React.createElement(Card,{item,compact:true,textOnly:true,showMovement:true}))));
   assert.match(html,/href="\/stocks\/XYZ"/);
   assert.match(html,/>XYZ<\/strong>/);
   const visible=html.replace(/<span class="sr-only">[\s\S]*?<\/span>/g,'');
   assert.ok(visible.includes('>'+expected+'</span>'),visible);
   assert.doesNotMatch(html,/<details|Sources and timestamps|View source archive/);
  }
 }
});

test('News archive shares one deduplicated quote provider and enables movement on its compact cards',()=>{
 const row={...item,research_category:'COMPANY'};
 const live=load('../app/components/stock/LivePrice.tsx',{'./TradingActivity':{default:()=>null},'@/lib/useLiveMarket':{useLiveMarket:symbols=>{
  assert.deepEqual(symbols,['XYZ']);return {data:null,failed:false};
 }}});
 const Card=load('../app/components/news/TopStory.tsx',{'./NewsThumbnail':({children})=>typeof children==='function'?children(null):children,'../stock/LivePrice':live}).default;
 const News=load('../app/news/page.tsx',{'../components/mascot/Mascot':{MascotState:({children})=>children},'../components/ui/button':{Button:({children})=>React.createElement('button',null,children)},'../components/news/TopStory':Card,'../components/stock/LivePrice':live,'@/lib/useNewsArchive':{useNewsArchive:()=>({page:{items:[row],as_of:now.toISOString(),has_more:false},loading:false,error:false})}}).default;
 const html=renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools('en')},React.createElement(News)));
 assert.match(html,/href="\/stocks\/XYZ"/);
 assert.match(html,/>Unavailable<\/span>/);
 assert.doesNotMatch(html,/>Unchanged<\/span>|Sources and timestamps/);
});

