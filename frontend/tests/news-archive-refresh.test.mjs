import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {transformSync} from 'next/dist/build/swc/index.js';
const require=createRequire(import.meta.url);
test('archive incorporates changed persisted pages without restart, preserving revealed depth and snapshot pagination',async()=>{
 const prior={fetch:globalThis.fetch,document:globalThis.document,window:globalThis.window,setInterval:globalThis.setInterval,clearInterval:globalThis.clearInterval};
 let effect,tick,version=0;const states=[],requests=[];
 try{
 globalThis.document={visibilityState:'visible',addEventListener(){},removeEventListener(){}};globalThis.window={addEventListener(){},removeEventListener(){}};
 globalThis.setInterval=fn=>{tick=fn;return 1;};globalThis.clearInterval=()=>{};
 globalThis.fetch=async(url,options)=>{requests.push({url,options});const q=new URL(url,'http://test').searchParams;const offset=Number(q.get('offset'));return {ok:true,json:async()=>({items:Array.from({length:12},(_,n)=>({story:{id:`v${version}-${n+offset}`}})),as_of:'2026-10-11T05:00:00Z',has_more:offset===0,next_offset:offset===0?12:null})};};
 const code=transformSync(readFileSync(new URL('../lib/useNewsArchive.ts',import.meta.url),'utf8'),{filename:'useNewsArchive.ts',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript'}}}).code;
 const exports={};new Function('require','exports',code)(name=>name==='react'?{useEffect:fn=>{effect=fn;},useRef:current=>({current}),useState:initial=>[initial,value=>states.push(value)]}:require(name==='./cacheRefresh.ts'?'../lib/cacheRefresh.ts':name),exports);
 const archive=exports.useNewsArchive('research_category=MARKET_BRIEF',0);const cleanup=effect();await new Promise(r=>setImmediate(r));
 archive.loadMore();await new Promise(r=>setImmediate(r));
 assert.equal(states.filter(v=>v?.items).at(-1).items.length,24);assert.match(requests[1].url,/as_of=2026-10-11/);
 version=1;tick();await new Promise(r=>setImmediate(r));const page=states.filter(v=>v?.items).at(-1);
 assert.equal(page.items.length,24);assert.equal(page.items[0].story.id,'v1-0');assert.equal(page.items.at(-1).story.id,'v1-23');
 assert.ok(requests.every(r=>r.url.startsWith('/api/news/feed/page?')&&r.options.cache==='no-store'));
 cleanup();assert.ok(requests.every(r=>r.options.signal.aborted));
 }finally{Object.assign(globalThis,prior);}
});
