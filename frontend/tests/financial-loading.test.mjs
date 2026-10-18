import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {transformSync} from 'next/dist/build/swc/index.js';
const require=createRequire(import.meta.url);
const code=transformSync(readFileSync(new URL('../app/components/stock/FundamentalTrends.tsx',import.meta.url),'utf8'),{filename:'FundamentalTrends.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
const flush=()=>new Promise(resolve=>setImmediate(resolve));

async function harness(run){
 const previous={setTimeout:globalThis.setTimeout,clearTimeout:globalThis.clearTimeout};
 const originalNow=Date.now;
 const timers=new Map(),changes=[],requests=[],values=[],refs=[];let effect,index=0,resolve,reject,cleanup,view,clock=100000;
 try{
  globalThis.setTimeout=(fn,ms)=>{const id=timers.size+1;timers.set(id,{fn,ms});return id;};
  globalThis.clearTimeout=id=>timers.delete(id);
  Date.now=()=>clock;
  const exports={};
  new Function('require','exports',code)(name=>{
   if(name==='react')return {useState:value=>{const key=index++;if(!(key in values))values[key]=value;return [values[key],next=>{values[key]=typeof next==='function'?next(values[key]):next;changes.push({key,next:values[key]});}];},useRef:value=>{const key=index++;return refs[key]??=( {current:value});},useEffect:fn=>{effect=fn;}};
   if(name==='@/lib/stock-detail')return {stockRead:(url,signal)=>{requests.push({url,signal});return new Promise((yes,no)=>{resolve=yes;reject=no;signal.addEventListener('abort',()=>no(new DOMException('Aborted','AbortError')),{once:true});});}};
   if(name==='@/lib/financial-engine-data')return {financialEngineData:data=>data};
   if(name==='./FinancialResearchCharts'||name==='./FinancialStatementTable')return {};
   if(name==='../ui/button'||name==='../ui/skeleton')return {};
   return require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name);
  },exports);
  const render=(ticker='ABC')=>{cleanup?.();index=0;view=exports.default({ticker});cleanup=effect();};
  render();
  await run({timers,changes,requests,cleanup:()=>cleanup?.(),resolve:value=>resolve(value),reject:error=>reject(error),
    frequency:value=>{view.props.onFrequency(value);render();},retry:()=>{view.props.retry();render();},
    render,view:()=>view,advance:ms=>{clock+=ms;}});
 }finally{Date.now=originalNow;Object.assign(globalThis,previous);}
}

test('one bounded financial request leaves slow work independent and permits the cold-source budget',async()=>{
 await harness(async state=>{
  assert.equal(state.requests.length,1);
  assert.match(state.requests[0].url,/frequency=annual&limit=8&projection=display$/);
  assert.equal([...state.timers.values()][0].ms,60000);
  assert.equal(state.requests[0].signal.aborted,false);
  state.resolve({ticker:'ABC'});await flush();
  assert.deepEqual(state.changes.filter(x=>x.key===0).at(-1)?.next,{ticker:'ABC'});
  assert.equal(state.timers.size,0);
  state.cleanup();
 });
});

test('deadline exposes a real error and performs no automatic acquisition retries',async()=>{
 await harness(async state=>{
  [...state.timers.values()][0].fn();await flush();
  assert.equal(state.requests[0].signal.aborted,true);
  assert.ok(state.changes.some(x=>x.key===2&&x.next===true));
  assert.equal(state.requests.length,1);
  state.cleanup();
 });
});

test('unmount/navigation cleanup rejects obsolete results and removes its timer',async()=>{
 await harness(async state=>{
  const initial=state.changes.length;
  state.cleanup();state.resolve({ticker:'OLD'});await flush();
  assert.equal(state.timers.size,0);
  assert.ok(!state.changes.slice(initial).some(x=>x.key===0||x.key===2&&x.next===true));
  assert.equal(state.requests[0].signal.aborted,true);
 });
});

test('a successful frequency round-trip reuses the same evidence without another request',async()=>{
 await harness(async state=>{
  const annual={ticker:'ABC',read_at:'original-source-read'};
  state.resolve(annual);await flush();
  state.frequency('quarterly');state.resolve({ticker:'ABC',period_type:'quarterly'});await flush();
  state.frequency('annual');
  assert.equal(state.requests.length,2);
  assert.equal(state.timers.size,0);
  assert.equal(state.changes.filter(x=>x.key===0).at(-1)?.next,annual);
  state.retry();assert.equal(state.requests.length,3);state.cleanup();
 });
});

test('expired reads, backwards clock and another ticker cannot reuse cached financial evidence',async()=>{
 await harness(async state=>{
  state.resolve({ticker:'ABC'});await flush();
  state.advance(60000);state.render();assert.equal(state.requests.length,2);
  state.resolve({ticker:'ABC'});await flush();
  state.advance(-1);state.render();assert.equal(state.requests.length,3);
  state.render('OTHER');assert.equal(state.requests.length,4);state.cleanup();
 });
});

test('failed requests and obsolete responses are not cached as successful frequency reads',async()=>{
 await harness(async state=>{
  state.reject(new Error('source unavailable'));await flush();
  state.frequency('quarterly');state.resolve({ticker:'ABC',period_type:'quarterly'});await flush();
  state.frequency('annual');assert.equal(state.requests.length,3);
  const obsolete=state.resolve;
  state.cleanup();obsolete({ticker:'ABC'});await flush();
  state.render();assert.equal(state.requests.length,4);state.cleanup();
 });
});

test('ticker and frequency transitions hide the prior financial period before the effect runs',async()=>{
 await harness(async state=>{
  state.resolve({ticker:'ABC',period_type:'annual'});await flush();state.render();
  assert.equal(state.view().props.data.period_type,'annual');
  state.frequency('quarterly');
  assert.equal(state.view().props.data,null);assert.equal(state.view().props.loading,true);
  state.resolve({ticker:'ABC',period_type:'quarterly'});await flush();
  state.render('OTHER');assert.equal(state.view().props.data,null);state.cleanup();
 });
});
