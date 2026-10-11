import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {emptyNewsFilters,newsViewQuery,readCommunityWindow,readNewsFilters} from '../lib/news.ts';
import {loadCommunity} from '../lib/community.ts';
const require=createRequire(import.meta.url);
function component(file,overrides){
 const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 const exports={};new Function('require','exports',code)(name=>overrides[name]||require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);return exports.default;
}

test('Attention keeps the displayed last24h sample through its link, destination and persisted API request',async()=>{
 const data={unique_items:1,as_of:'2026-10-11T05:00:00Z',coverage_partial:true,sources:[],active_tickers:[{ticker:'XYZ',item_count:1}],themes:[],items:[{id:'one',title:'Original discussion',url:'https://example.org/one',is_fixture:true}]};
 const Pulse=component('../app/components/news/CommunityPulse.tsx',{'../stock/StockCommunity':{CommunityDiscussions:()=>null},react:{...React,useEffect(){},useState:initial=>[initial===null?data:initial,()=>{}]}});
 const html=renderToStaticMarkup(React.createElement(Pulse,{ticker:'',topic:'',attempt:0,compact:true,initialWindow:'last24h'}));
 assert.match(html,/value="last24h" selected=""/);
 assert.match(html,/Sample includes fixture data/);assert.match(html,/Original discussion · Fixture/);
 const href=html.match(/href="(\/news\?[^\"]+)"[^>]*>1 discussion/)[1].replaceAll('&amp;','&');
 assert.equal(readCommunityWindow(href.split('?')[1]),'last24h');
 assert.equal(readNewsFilters(href.split('?')[1]).ticker,'XYZ');
 const prior=globalThis.fetch;
 try{globalThis.fetch=async url=>{const query=new URL(url,'http://test').searchParams;assert.equal(query.get('window'),'last24h');assert.equal(query.get('ticker'),'XYZ');return {ok:true,json:async()=>data};};
 assert.equal((await loadCommunity('XYZ','',undefined,readCommunityWindow(href.split('?')[1]))).unique_items,1);
 }finally{globalThis.fetch=prior;}
 const real=component('../app/components/news/CommunityPulse.tsx',{'../stock/StockCommunity':{CommunityDiscussions:()=>null},react:{...React,useEffect(){},useState:initial=>[initial===null?{...data,items:[{...data.items[0],is_fixture:false}]}:initial,()=>{}]}});
 assert.doesNotMatch(renderToStaticMarkup(React.createElement(real,{ticker:'',topic:'',attempt:0,compact:true})),/Sample includes fixture data|Original discussion · Fixture/);
});

test('Community URL canonicalization preserves only valid windows and excludes them from publisher views',()=>{
 assert.equal(readCommunityWindow('window=unknown'),'today');
 assert.equal(readCommunityWindow(newsViewQuery(emptyNewsFilters,'community','last24h')),'last24h');
 assert.equal(new URLSearchParams(newsViewQuery(emptyNewsFilters,'industry','last24h')).has('window'),false);
 assert.equal(new URLSearchParams(newsViewQuery(emptyNewsFilters,'community')).has('window'),false);
});

test('Index mascot cannot imply an active market for a stale active snapshot or unavailable initial load',()=>{
 const now=new Date();const snapshot={level:1735.09,change:0,change_percent:0,trading_date:new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).format(now),updated_at:new Date(now.getTime()-180000).toISOString(),source:'Fixture:test',total_volume:null,total_value:null};
 const render=live=>{const Market=component('../app/components/ExploreMarket.tsx',{'@/lib/useLiveMarket':{useLiveIndex:()=>live},'./stock/LivePrice':{LivePrices:({children})=>children},'./news/TopStory':()=>null,'./news/CommunityPulse':()=>null,'./mascot/Mascot':{MascotIllustration:({state})=>React.createElement('span',{'data-mascot':state}),MascotState:({children})=>children}});return renderToStaticMarkup(React.createElement(Market));};
 const stale=render({data:{snapshot,status:'fresh',session:'active'},failed:false});assert.match(stale,/data-mascot="marketUncertain"/);assert.match(stale,/Stale market data/);assert.match(stale,/unchanged/);
 assert.match(render({data:null,failed:true}),/data-mascot="marketUncertain"/);
 assert.match(render({data:{snapshot:{...snapshot,updated_at:now.toISOString()},status:'fresh',session:'active'},failed:false}),/data-mascot="marketWatching"/);
});
