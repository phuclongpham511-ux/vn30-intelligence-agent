import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {transformSync} from 'next/dist/build/swc/index.js';
import * as watchlist from '../lib/watchlist.ts';
import {packet,saved,news,at} from './fixtures/stock-intelligence.mjs';
const require=createRequire(import.meta.url);
const code=transformSync(readFileSync(new URL('../app/components/stock/StockIntelligence.tsx',import.meta.url),'utf8'),{filename:'StockIntelligence.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
const flush=()=>new Promise(resolve=>setImmediate(resolve));
async function harness(run,{raw=JSON.stringify(saved()),broken=false}={}){
 const originals=Object.fromEntries(['window','localStorage','setTimeout','clearTimeout','setInterval'].map(key=>[key,globalThis[key]]));
 const values=[],effects=[],requests=[],timers=new Map(),events=new Map();let cursor=0,view,writes=0,props={ticker:'AAA',preview:true};
 try{
  globalThis.localStorage={getItem(){if(broken)throw Error('Storage denied');return raw;},setItem(key,value){if(broken)throw Error('Storage denied');writes++;raw=value;}};
  globalThis.window={addEventListener(name,fn){const list=events.get(name)||new Set();list.add(fn);events.set(name,list);},removeEventListener(name,fn){events.get(name)?.delete(fn);},dispatchEvent(event){for(const fn of events.get(event.type)||[])fn(event);}};
  globalThis.setTimeout=(fn,ms)=>{const key=Symbol();timers.set(key,{fn,ms});return key;};globalThis.clearTimeout=key=>timers.delete(key);
  globalThis.setInterval=()=>{throw Error('No new polling permitted');};
  const exports={};
  const react={useState(initial){const key=cursor++;if(!(key in values))values[key]=initial;return [values[key],next=>{values[key]=typeof next==='function'?next(values[key]):next;}];},useEffect(fn,deps){const key=cursor++,old=effects[key];if(!old||deps.some((value,index)=>value!==old.deps[index]))effects[key]={fn,deps,pending:true,cleanup:old?.cleanup};}};
  new Function('require','exports',code)(name=>name==='react'?react:name==='./StockActions'?{__esModule:true,default:()=>null}:name==='@/lib/watchlist'?{...watchlist,loadIntelligence(symbols,offset,signal,request,options){return new Promise((resolve,reject)=>requests.push({symbols,offset,signal,options,resolve,reject}));}}:require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
  const render=(next={})=>{props={...props,...next};cursor=0;view=exports.default(props);for(const effect of effects.filter(Boolean))if(effect.pending){effect.cleanup?.();effect.pending=false;effect.cleanup=effect.fn();}return view;};
  const cleanup=()=>{for(const effect of effects.filter(Boolean))effect.cleanup?.();};
  render();
  await run({requests,timers,render,view:()=>view,writes:()=>writes,raw:()=>raw,setRaw:value=>{raw=value;},cleanup});
  cleanup();
 }finally{for(const [key,value] of Object.entries(originals))if(value===undefined)delete globalThis[key];else globalThis[key]=value;}
}
test('one bounded persisted read survives Overview/News switching without quotes, polling or auto-review',async()=>{
 await harness(async state=>{
  assert.deepEqual(state.requests[0].symbols,['AAA']);assert.equal(state.requests[0].options.community_groups,true);assert.equal([...state.timers.values()][0].ms,20000);
  state.requests[0].resolve(packet());await flush();state.render({preview:false});state.render({preview:true});
  assert.equal(state.requests.length,1);assert.equal(state.writes(),0);assert.equal(state.timers.size,0);
  assert.equal(state.view().props.data.stocks[0].symbol,'AAA');
  state.view().props.review(news);state.render();assert.equal(state.writes(),1);
  const savedState=watchlist.readWatchlist(state.raw());assert.equal(watchlist.isUnread(savedState,'AAA',news),false);
  assert.equal(watchlist.isUnread(savedState,'BBB',news),true);
 });
});
test('cross-ticker cleanup and late timed-out responses cannot publish old evidence or reviews',async()=>{
 await harness(async state=>{
  const old=state.requests[0];state.render({ticker:'BBB'});assert.equal(old.signal.aborted,true);
  old.resolve(packet());await flush();state.render();assert.equal(state.view().props.data,null);assert.equal(state.writes(),0);
  const current=state.requests[1];[...state.timers.values()][0].fn();
  current.resolve({...packet(),stocks:[{...packet().stocks[0],symbol:'BBB'}]});await flush();state.render();
  assert.equal(state.view().props.error,true);assert.equal(state.view().props.data,null);assert.equal(state.writes(),0);
 });
});
test('unreadable storage is preserved; source evidence remains independently readable',async()=>{
 await harness(async state=>{
  state.requests[0].resolve(packet());await flush();state.render();
  assert.equal(state.view().props.storageError,true);assert.ok(state.view().props.data);assert.equal(state.writes(),0);
 },{raw:'preserve-unreadable',broken:true});
});
test('review merges latest storage and cannot overwrite a concurrent explicit review',async()=>{
 await harness(async state=>{
  state.requests[0].resolve(packet());await flush();state.render();
  const current=watchlist.reviewUpdates(saved(),'AAA',[{...news,revision:'v2',revision_members:{article:'v2'}}],at);
  state.setRaw(JSON.stringify(current));state.view().props.review(news);
  assert.equal(state.writes(),0);assert.equal(watchlist.readWatchlist(state.raw()).receipts.AAA['news:story'].revision,'v2');
  window.dispatchEvent(new Event(watchlist.watchlistChangedEvent));state.render();assert.equal(state.requests.length,1);
 });
});
