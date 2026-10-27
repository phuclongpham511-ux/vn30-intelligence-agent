// Component interaction contracts only. No browser, server or provider is started.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {transformSync} from 'next/dist/build/swc/index.js';
import {localeTools} from '../lib/i18n.ts';
import {readWatchlist,watchlistStorageKey} from '../lib/watchlist.ts';
import {readCommunityWindow} from '../lib/community.ts';
const require=createRequire(import.meta.url);
const nodes=value=>Array.isArray(value)?value.flatMap(nodes):!value||typeof value!=='object'?[]:[value,...nodes(value.props?.children)];
function component(file,mocks={},language='en'){
 const values=[],effects=[],pending=[];let cursor=0,effect=0;
 const react={...React,useId:()=> 'journey-search',useState(initial){const key=cursor++;if(!(key in values))values[key]=typeof initial==='function'?initial():initial;return [values[key],next=>{values[key]=typeof next==='function'?next(values[key]):next;}];},useEffect(fn,deps){const key=effect++,old=effects[key];if(!old||deps.some((v,i)=>v!==old[i])){effects[key]=deps;pending.push(fn);}}};
 const exports={},code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 new Function('require','exports',code)(id=>id==='react'?react:id==='@/lib/i18n'?{useLocale:()=>localeTools(language)}:mocks[id]||require(id.startsWith('@/lib/')?'../lib/'+id.slice(6)+'.ts':id),exports);
 return {render(props={}){cursor=effect=0;return exports.default(props);},flush(){while(pending.length)pending.shift()();},values};
}

test('an already followed stock can be removed when metadata is missing, preserving other reviews',()=>{
 const oldStorage=globalThis.localStorage,oldWindow=globalThis.window;
 const initial={symbols:['ABC','XYZ'],seen:{ABC:['a'],XYZ:['b']},communitySeen:{},receipts:{XYZ:{'news:b':{revision:'v1',reviewed_at:null}}}};
 let stored=JSON.stringify(initial),writes=0;
 globalThis.localStorage={getItem:key=>{assert.equal(key,watchlistStorageKey);return stored;},setItem(key,value){assert.equal(key,watchlistStorageKey);stored=value;writes++;}};
 globalThis.window={addEventListener(){},removeEventListener(){},dispatchEvent(){}};
 try{
  const view=component('../app/components/stock/FollowStock.tsx',{'../ui/button':{Button:'button'}});
  view.render({ticker:'ABC',available:false});view.flush();
  const button=nodes(view.render({ticker:'ABC',available:false})).find(n=>n.props?.['aria-pressed']===true);
  assert.equal(button.props.disabled,false);
  button.props.onClick();
  const saved=readWatchlist(stored);
  assert.deepEqual(saved.symbols,['XYZ']);assert.deepEqual(saved.receipts.XYZ,initial.receipts.XYZ);
  assert.equal(writes,1);
  const follow=nodes(view.render({ticker:'ABC',available:false})).find(n=>n.props?.['aria-pressed']===false);
  assert.equal(follow.props.disabled,true);
 }finally{globalThis.localStorage=oldStorage;globalThis.window=oldWindow;}
});

for(const language of ['en','vi'])test('independent Community ticker and window survive reload in '+language,()=>{
 const oldWindow=globalThis.window;
 globalThis.window={location:{search:'?ticker=ABC&window=last24h'},history:{replaceState(_s,_t,url){globalThis.window.location.search=new URL(url,'http://localhost').search;}},addEventListener(){},removeEventListener(){}};
 const mocks={'../components/ui/button':{Button:'button'},'../components/news/CommunityPulse':{__esModule:true,default:'pulse'}};
 try{
  const page=component('../app/community/page.tsx',mocks,language);
  page.render();page.flush();let tree=page.render();page.flush();
  const props=nodes(tree).find(n=>n.type==='pulse').props;
  const pulse=component('../app/components/news/CommunityPulse.tsx',{'next/link':{__esModule:true,default:'a'},'../stock/StockCommunity':{CommunityDiscussions:'discussions'},'@/lib/community':{loadCommunity(){throw Error('No acquisition in interaction test');}}},language);
  let controls=pulse.render(props);
  nodes(controls).find(n=>n.type==='input').props.onChange({target:{value:' xyz '}});
  controls=pulse.render(props);
  nodes(controls).find(n=>n.type==='form').props.onSubmit({preventDefault(){}});
  tree=page.render();page.flush();
  assert.equal(new URLSearchParams(window.location.search).get('ticker'),'XYZ');
  assert.equal(readCommunityWindow(window.location.search),'last24h');
  const restored=component('../app/community/page.tsx',mocks,language);restored.render();restored.flush();
  assert.equal(nodes(restored.render()).find(n=>n.type==='pulse').props.ticker,'XYZ');
  const selected=pulse.render({...props,ticker:'XYZ'});
  nodes(selected).find(n=>n.type==='button'&&n.props.children===localeTools(language).t('Clear discussion filter')).props.onClick();
  page.render();page.flush();
  assert.equal(new URLSearchParams(window.location.search).has('ticker'),false);
  assert.equal(readCommunityWindow(window.location.search),'last24h');
 }finally{globalThis.window=oldWindow;}
});

test('search selection navigates to the exact ticker in EN/VI; unavailable results never navigate',()=>{
 for(const language of ['en','vi']){
  const routes=[],remembered=[];
  const wrapper=component('../app/components/stock/TickerSearch.tsx',{'next/navigation':{useRouter:()=>({push:url=>routes.push(url)})},'./StockSearch':{__esModule:true,default:'search'}},language);
  const props=nodes(wrapper.render()).find(n=>n.type==='search').props;
  let result={data:{items:[{symbol:'ABC',exchange:'HOSE'},{symbol:'XYZ',exchange:'HOSE'}]},loading:false,error:false};
  const search=component('../app/components/stock/StockSearch.tsx',{'./useRecentSearches':{useRecentSearches:()=>({recent:[],remember:s=>remembered.push(s),remove(){},clear(){}})},'@/lib/useEquityPage':{useEquityPage:()=>result}},language);
  let tree=search.render(props);
  nodes(tree).find(n=>n.type==='input').props.onChange({target:{value:'xyz'}});
  tree=search.render(props);
  nodes(tree).find(n=>n.type==='input').props.onKeyDown({key:'Enter',preventDefault(){}});
  assert.deepEqual(routes,['/stocks/XYZ']);assert.deepEqual(remembered,['XYZ']);
  result={data:null,loading:false,error:true};
  tree=search.render(props);nodes(tree).find(n=>n.type==='input').props.onChange({target:{value:'MISSING'}});
  tree=search.render(props);
  assert.ok(nodes(tree).some(n=>n.props?.role==='alert'));
  nodes(tree).find(n=>n.type==='input').props.onKeyDown({key:'Enter',preventDefault(){}});
  assert.deepEqual(routes,['/stocks/XYZ']);
 }
});

test('a stale Following button cannot re-add an unavailable stock after another tab removed it',()=>{
 const oldStorage=globalThis.localStorage,oldWindow=globalThis.window;let stored=JSON.stringify({symbols:['ABC'],seen:{},communitySeen:{}}),writes=0;
 globalThis.localStorage={getItem:()=>stored,setItem(){writes++;}};
 globalThis.window={addEventListener(){},removeEventListener(){},dispatchEvent(){}};
 try{
  const view=component('../app/components/stock/FollowStock.tsx',{'../ui/button':{Button:'button'}});
  view.render({ticker:'ABC',available:false});view.flush();
  const button=nodes(view.render({ticker:'ABC',available:false})).find(n=>n.props?.['aria-pressed']===true);
  stored=JSON.stringify({symbols:[],seen:{},communitySeen:{}});
  button.props.onClick();assert.equal(writes,0);
  stored='{corrupt';button.props.onClick();assert.equal(writes,0);assert.equal(stored,'{corrupt');
  assert.ok(nodes(view.render({ticker:'ABC',available:false})).some(n=>n.props?.role==='alert'));
 }finally{globalThis.localStorage=oldStorage;globalThis.window=oldWindow;}
});


test('legacy Community bookmarks redirect before any editorial request or News source read',()=>{
 const prior={window:globalThis.window,fetch:globalThis.fetch};const redirects=[],queries=[];
 globalThis.window={location:{search:'?view=community&ticker=xyz&window=last24h&source=publisher',replace:url=>redirects.push(url)}};
 globalThis.fetch=()=>{throw Error('A legacy discussion URL must not read editorial sources');};
 try{
  const page=component('../app/news/page.tsx',{'../components/mascot/Mascot':{MascotState:'state'},'../components/ui/button':{Button:'button'},'../components/news/SourceCoverage':{__esModule:true,default:'sources'},'../components/news/TopStory':{__esModule:true,default:'story'},'../components/stock/LivePrice':{LivePrices:'quotes'},'@/lib/useNewsArchive':{useNewsArchive:query=>{queries.push(query);return {page:null,loading:false,error:false,loadMore(){}};}}});
  page.render();page.flush();page.render();page.flush();
  assert.deepEqual(redirects,['/community?ticker=XYZ&window=last24h']);assert.ok(queries.every(query=>query===null));
 }finally{Object.assign(globalThis,prior);}
});

for(const language of ['en','vi'])test('editorial category switches retain ticker and publisher filters in '+language,()=>{
 const prior={window:globalThis.window,fetch:globalThis.fetch};const queries=[];
 globalThis.window={location:{search:'?ticker=XYZ&source=publisher&country=VN'},history:{replaceState(_s,_t,url){window.location.search=new URL(url,'http://localhost').search;}},addEventListener(){},removeEventListener(){}};
 globalThis.fetch=async url=>{assert.equal(url,'/api/news/sources');return {ok:true,json:async()=>[]};};
 try{
  const page=component('../app/news/page.tsx',{'../components/mascot/Mascot':{MascotState:'state'},'../components/ui/button':{Button:'button'},'../components/news/SourceCoverage':{__esModule:true,default:'sources'},'../components/news/TopStory':{__esModule:true,default:'story'},'../components/stock/LivePrice':{LivePrices:'quotes'},'@/lib/useNewsArchive':{useNewsArchive:query=>{queries.push(query);return {page:null,loading:false,error:false,loadMore(){}};}}},language);
  page.render();page.flush();let tree=page.render();page.flush();
  for(const [label,category] of [['Company','COMPANY'],['Market','MARKET_BRIEF'],['Industry','INDUSTRY']]){
   nodes(tree).find(n=>n.type==='button'&&n.props.children===localeTools(language).t(label)).props.onClick();
   tree=page.render();page.flush();
   const q=new URLSearchParams(queries.at(-1));
   assert.equal(q.get('research_category'),category);assert.equal(q.get('ticker'),'XYZ');assert.equal(q.get('source'),'publisher');assert.equal(q.get('country'),'VN');
   const url=new URLSearchParams(window.location.search);assert.equal(url.get('ticker'),'XYZ');assert.equal(url.get('source'),'publisher');assert.equal(url.has('window'),false);
  }
 }finally{Object.assign(globalThis,prior);}
});
