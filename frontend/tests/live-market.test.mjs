import test from 'node:test';
import assert from 'node:assert/strict';
import {liveRefresh,indexMascot,visibleSymbols,movement} from '../lib/live-market.ts';
import {localeTools} from '../lib/i18n.ts';

test('requested symbols are bounded to caller-visible deduplicated set',()=>{
 assert.equal(visibleSymbols(['TCB','fpt','FPT']),'FPT,TCB');
});
test('direction includes real zero and missing values without fabricating neutral numbers',()=>{
 assert.equal(movement(12).label,'Up');assert.equal(movement(-1).label,'Down');
 assert.equal(movement(0).label,'Unchanged');assert.equal(movement(null).label,'Unavailable');
});
test('active sessions watch; breaks/closed/unconfirmed use direction or neutral',()=>{
 assert.equal(indexMascot('active',-12),'marketWatching');
 assert.equal(indexMascot('active',5),'marketWatching');
 for(const session of ['break','closed','unknown']) {
  assert.equal(indexMascot(session,5),'marketUp');assert.equal(indexMascot(session,-3),'marketDown');
  assert.equal(indexMascot(session,0),'marketNeutral');assert.equal(indexMascot(session,null),'marketNeutral');
 }
});
test('today source date formats as 07/10 under the Vietnam timezone',()=>{
 assert.equal(localeTools('vi').date('2026-10-07'),'07/10/2026');
});

function environment() {
 const listeners=new Map(),timers=new Map(); let id=0;
 const visibility={visibilityState:'visible',addEventListener:(name,fn)=>listeners.set(name,fn),removeEventListener:name=>listeners.delete(name)};
 const scheduler={set:(fn,delay)=>{timers.set(++id,{fn,delay});return id;},clear:key=>timers.delete(key)};
 return {visibility,scheduler,timers,listeners,change(state){visibility.visibilityState=state;listeners.get('visibilitychange')?.();}};
}
const settle=()=>new Promise(resolve=>setImmediate(resolve));
test('polling receives changed prices without reload, respects cadence and pauses hidden tabs',async()=>{
 const env=environment();let calls=0;const seen=[];
 const stop=liveRefresh(async()=>({session:'active',price:++calls}),data=>seen.push(data),10000,env.visibility,env.scheduler);
 await settle();assert.equal(calls,1);assert.equal([...env.timers.values()][0].delay,10000);
 [...env.timers.values()][0].fn();await settle();assert.equal(seen.at(-1).price,2);
 env.change('hidden');assert.equal(env.timers.size,0);assert.equal(calls,2);
 env.change('visible');await settle();assert.equal(calls,3);
 stop();assert.equal(env.timers.size,0);assert.equal(env.listeners.size,0);
});
test('closed market stops rapid polling; activation checks once; failed fetch not labelled fresh',async()=>{
 const env=environment();let calls=0;const seen=[];
 const stop=liveRefresh(async()=>{if(++calls===2)throw Error();return {session:'closed'};},data=>seen.push(data),15000,env.visibility,env.scheduler);
 await settle();assert.equal(env.timers.size,0);
 env.change('hidden');env.change('visible');await settle();assert.equal(calls,2);assert.equal(seen.at(-1),null);
 assert.equal([...env.timers.values()][0].delay,60000);stop();
});
test('unmount aborts in-flight fetch and suppresses obsolete symbol responses',async()=>{
 const env=environment();let signal,resolve;const seen=[];
 const stop=liveRefresh(s=>{signal=s;return new Promise(r=>resolve=r);},data=>seen.push(data),30000,env.visibility,env.scheduler);
 stop();assert.equal(signal.aborted,true);resolve({session:'active'});await settle();
 assert.equal(seen.length,0);assert.equal(env.timers.size,0);
});
test('hidden and unmount release demand while activation reacquires it',async()=>{
 const env=environment();let releases=0,calls=0;
 const stop=liveRefresh(async()=>{calls++;return {session:'active'};},()=>{},20000,env.visibility,env.scheduler,()=>releases++);
 await settle();env.change('hidden');assert.equal(releases,1);assert.equal(env.timers.size,0);
 env.change('visible');await settle();assert.equal(calls,2);stop();assert.equal(releases,2);
});
test('unconfirmed sessions get bounded initial retries and then slow down without claiming active',async()=>{
 const env=environment();const seen=[];
 const stop=liveRefresh(async()=>({session:'unknown'}),data=>seen.push(data),10000,env.visibility,env.scheduler);
 await settle();
 for(let i=0;i<3;i++) {assert.equal([...env.timers.values()][0].delay,10000);[...env.timers.values()][0].fn();await settle();}
 assert.equal([...env.timers.values()][0].delay,60000);assert.ok(seen.every(x=>x.session==='unknown'));stop();
});
