import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
const require=createRequire(import.meta.url);
let selected,visited,reads,identity;
const react={...React,useState(initial){
  const value=typeof initial==='function'?initial():initial;
  if(value==='overview')return [selected,()=>{}];
  if(value instanceof Set)return [new Set(visited),()=>{}];
  return React.useState(initial);
}};
const marker=name=>({visible=true,focus})=>visible?React.createElement('div',{'data-component':name,'data-focus':focus}):null;
const exports={};
const compiled=transformSync(readFileSync(new URL('../app/components/Explore.tsx',import.meta.url),'utf8'),{filename:'Explore.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
new Function('require','exports',compiled)(name=>{
  if(name==='react')return react;
  if(name==='./stock/useStockRead')return {useStockRead:url=>{reads.push(url);return {data:url.includes('/universe')?identity:null,error:false,retry(){}};}};
  if(name==='./stock/StockStates')return {StockError:marker('Identity error')};
  if(name==='./ui/skeleton')return {Skeleton:marker('Skeleton')};
  if(name==='./ui/button')return {Button:marker('Button')};
  if(name==='./market/WorkspaceNav')return {__esModule:true,default:marker('WorkspaceNav')};
  if(name.startsWith('./stock/'))return {__esModule:true,default:marker(name.slice(8))};
  return require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name);
},exports);
function render(tab,seen=[tab],symbol='ABC') {
  selected=tab;visited=seen;reads=[];
  identity={items:[{symbol,exchange:'HOSE',company_name:'Original company name',source:'SSI:FastConnect'}],last_synced_at:'2026-10-12T10:00:00Z'};
  return renderToStaticMarkup(React.createElement(exports.default,{ticker:'ABC'}));
}
test('direct action deep link reads identity and action evidence without loading market/history or finances',()=>{
  const html=render('actions');
  assert.match(html,/data-component="StockActions"/);
  assert.doesNotMatch(html,/data-component="TechnicalChart|data-component="FundamentalTrends/);
  assert.deepEqual(reads,['/api/stocks/universe?symbols=ABC&limit=1']);
  assert.match(html,/id="stock-tab-actions"[^>]*aria-selected="true"/);
});
test('research tabs share one retained chart and defer unvisited annual financials',()=>{
  const html=render('technical',['overview','technical']);
  assert.equal((html.match(/data-component="TechnicalChart"/g)||[]).length,1);
  assert.doesNotMatch(html,/data-component="FundamentalTrends/);
  assert.match(html,/aria-controls="stock-panel-price"/);
  assert.match(html,/separate assurance; no trading recommendation/);
});
test('a wrong ticker identity cannot render research for the prior company',()=>{
  const html=render('overview',['overview'],'OTHER');
  assert.match(html,/Identity error/);assert.doesNotMatch(html,/Original company name|TechnicalChart/);
});
test('one research integration replaces separate news/community loaders without changing primary tabs',()=>{
 for(const section of ['overview','news']){
  const html=render(section);
  assert.equal((html.match(/data-component="StockIntelligence"/g)||[]).length,1);
  assert.doesNotMatch(html,/data-component="StockNews|data-component="StockCommunity/);
  assert.match(html,/id="stock-tab-fundamentals"/);assert.match(html,/id="stock-tab-actions"/);
 }
});
test('Community is a direct research destination sharing one retained intelligence panel',()=>{
 const html=render('community',['overview','news','community']);
 assert.match(html,/id="stock-tab-community"[^>]*aria-controls="stock-panel-news"[^>]*aria-selected="true"/);
 assert.match(html,/id="stock-panel-news"[^>]*aria-labelledby="stock-tab-community"[^>]*tabindex="0"/);
 assert.equal((html.match(/data-component="StockIntelligence"/g)||[]).length,1);
 assert.match(html,/data-focus="community"/);
 assert.doesNotMatch(html,/data-component="FundamentalTrends"/);
});
