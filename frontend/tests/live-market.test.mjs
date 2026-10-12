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
test('closed market schedules one opening check; activation checks once; failure is not fresh',async()=>{
 const env=environment();let calls=0;const seen=[];
 const stop=liveRefresh(async()=>{if(++calls===2)throw Error();return {session:'closed'};},data=>seen.push(data),15000,env.visibility,env.scheduler,()=>{},()=>new Date('2026-10-12T08:30:00+07:00'));
 await settle();assert.equal(env.timers.size,1);assert.equal([...env.timers.values()][0].delay,30*60*1000);
 env.change('hidden');env.change('visible');await settle();assert.equal(calls,2);assert.equal(seen.at(-1),null);
 assert.equal([...env.timers.values()][0].delay,30*60*1000);stop();
});
test('a visible Friday-close tab resumes Monday without reload or visibility change',async()=>{
 const env=environment();let calls=0,now=new Date('2026-10-09T15:05:00+07:00');const seen=[];
 const stop=liveRefresh(async()=>({session:++calls===1?'closed':'active'}),data=>seen.push(data),15000,env.visibility,env.scheduler,()=>{},()=>now);
 await settle();assert.equal(calls,1);assert.equal(env.timers.size,1);
 const wake=[...env.timers.values()][0];const opening=new Date('2026-10-12T09:00:00+07:00');
 assert.equal(wake.delay,opening-now);
 now=opening;wake.fn();await settle();
 assert.equal(calls,2);assert.equal(seen.at(-1).session,'active');assert.equal([...env.timers.values()][0].delay,15000);
 env.change('hidden');assert.equal(env.timers.size,0);stop();assert.equal(env.listeners.size,0);
});
test('opening checks use Vietnam weekdays independently of the browser timezone',async()=>{
 for(const [at,opening] of [
  ['2026-10-10T10:00:00+07:00','2026-10-12T09:00:00+07:00'],
  ['2026-10-11T23:30:00+07:00','2026-10-12T09:00:00+07:00'],
  ['2026-10-12T08:59:00+07:00','2026-10-12T09:00:00+07:00'],
  ['2026-10-12T15:05:00+07:00','2026-10-13T09:00:00+07:00'],
 ]) {
  const env=environment();const now=new Date(at);
  const stop=liveRefresh(async()=>({session:'closed'}),()=>{},15000,env.visibility,env.scheduler,()=>{},()=>now);
  await settle();assert.equal(env.timers.size,1);assert.equal([...env.timers.values()][0].delay,new Date(opening)-now);
  stop();assert.equal(env.timers.size,0);
 }
});
test('an opening wake does not invent an active session when provider evidence is missing',async()=>{
 const env=environment();let calls=0,now=new Date('2026-10-12T08:59:00+07:00');const seen=[];
 const stop=liveRefresh(async()=>({session:++calls===1?'closed':'unknown'}),data=>seen.push(data),15000,env.visibility,env.scheduler,()=>{},()=>now);
 await settle();now=new Date('2026-10-12T09:00:00+07:00');[...env.timers.values()][0].fn();await settle();
 assert.equal(calls,2);assert.equal(seen.at(-1).session,'unknown');assert.equal([...env.timers.values()][0].delay,15000);
 stop();
});
test('opening timer delayed beyond closing does not start a recovery burst',async()=>{
 const env=environment();let now=new Date('2026-10-09T15:05:00+07:00'),calls=0;
 const stop=liveRefresh(async()=>{calls++;return {session:'closed'};},()=>{},15000,env.visibility,env.scheduler,()=>{},()=>now);
 await settle();now=new Date('2026-10-12T16:00:00+07:00');[...env.timers.values()][0].fn();await settle();
 assert.equal(calls,2);assert.equal([...env.timers.values()][0].delay,new Date('2026-10-13T09:00:00+07:00')-now);stop();
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
test('unconfirmed sessions get bounded initial retries and then back off without claiming active',async()=>{
 const env=environment();const seen=[];
 const stop=liveRefresh(async()=>({session:'unknown'}),data=>seen.push(data),10000,env.visibility,env.scheduler,()=>{},()=>new Date('2026-10-12T10:00:00+07:00'));
 await settle();
 for(let i=0;i<3;i++) {assert.equal([...env.timers.values()][0].delay,10000);[...env.timers.values()][0].fn();await settle();}
 for(const delay of [60000,120000,240000,480000,900000,900000]) {
  assert.equal([...env.timers.values()][0].delay,delay);[...env.timers.values()][0].fn();await settle();
 }
 assert.ok(seen.every(x=>x.session==='unknown'));stop();
});

test('temporary opening failure retries slowly, then restores 15-second active cadence',async()=>{
 const env=environment();let calls=0,now=new Date('2026-10-12T08:59:00+07:00');const seen=[];
 const stop=liveRefresh(async()=>{calls++;if(calls===2)throw Error('temporary');return {session:calls===1?'closed':'active'};},data=>seen.push(data),15000,env.visibility,env.scheduler,()=>{},()=>now);
 await settle();now=new Date('2026-10-12T09:00:00+07:00');[...env.timers.values()][0].fn();await settle();
 assert.equal(calls,2);assert.equal(seen.at(-1),null);assert.equal([...env.timers.values()][0].delay,60000);
 now=new Date('2026-10-12T09:01:00+07:00');[...env.timers.values()][0].fn();await settle();
 assert.equal(seen.at(-1).session,'active');assert.equal([...env.timers.values()][0].delay,15000);stop();
});
test('throttled opening timer handles a late closed reply before eventual active data',async()=>{
 const env=environment();let calls=0,now=new Date('2026-10-09T15:05:00+07:00');
 const stop=liveRefresh(async()=>({session:++calls<3?'closed':'active'}),()=>{},15000,env.visibility,env.scheduler,()=>{},()=>now);
 await settle();now=new Date('2026-10-12T09:03:00+07:00');[...env.timers.values()][0].fn();await settle();
 assert.equal([...env.timers.values()][0].delay,60000);now=new Date('2026-10-12T09:04:00+07:00');
 [...env.timers.values()][0].fn();await settle();assert.equal(calls,3);assert.equal([...env.timers.values()][0].delay,15000);stop();
});
test('holiday closed replies get only three slow rechecks before next-opening sleep',async()=>{
 const env=environment();let now=new Date('2026-10-12T09:00:00+07:00');const seen=[];
 const stop=liveRefresh(async()=>({session:'closed'}),data=>seen.push(data),15000,env.visibility,env.scheduler,()=>{},()=>now,env.visibility);
 await settle();
 for(const delay of [60000,120000,240000]) {
  const wake=[...env.timers.values()][0];assert.equal(wake.delay,delay);now=new Date(now.getTime()+delay);wake.fn();await settle();
 }
 assert.equal([...env.timers.values()][0].delay,new Date('2026-10-13T09:00:00+07:00')-now);
 now=new Date(now.getTime()+2000);env.listeners.get('focus')();await settle();
 assert.equal([...env.timers.values()][0].delay,new Date('2026-10-13T09:00:00+07:00')-now);
 assert.ok(seen.every(x=>x.session==='closed'));stop();
});
test('sleep and foreground event bursts coalesce into one request, with full cleanup',async()=>{
 const env=environment();let now=new Date('2026-10-12T08:00:00+07:00'),calls=0,resolve;const seen=[];
 const stop=liveRefresh(async()=>{calls++;if(calls===1)return {session:'closed'};return new Promise(r=>resolve=r);},data=>seen.push(data),15000,env.visibility,env.scheduler,()=>{},()=>now,env.visibility);
 await settle();now=new Date('2026-10-12T09:05:00+07:00');
 for(const event of ['focus','pageshow','visibilitychange','focus'])env.listeners.get(event)();
 assert.equal(calls,2);assert.equal(env.timers.size,1);resolve({session:'active'});await settle();
 env.listeners.get('focus')();assert.equal(calls,2);assert.equal(env.timers.size,1);
 assert.equal([...env.timers.values()][0].delay,15000);stop();assert.equal(env.listeners.size,0);assert.equal(env.timers.size,0);
});
test('hung opening request times out and late results cannot override recovery',async()=>{
 const env=environment();let now=new Date('2026-10-12T09:00:00+07:00'),calls=0,resolve,signal;const seen=[];
 const stop=liveRefresh(s=>{calls++;signal=s;return calls===1?new Promise(r=>resolve=r):Promise.resolve({session:'active'});},data=>seen.push(data),15000,env.visibility,env.scheduler,()=>{},()=>now,env.visibility);
 assert.equal([...env.timers.values()][0].delay,20000);
 now=new Date(now.getTime()+20000);[...env.timers.values()][0].fn();await settle();
 assert.equal(signal.aborted,true);assert.deepEqual(seen,[null]);assert.equal([...env.timers.values()][0].delay,60000);
 now=new Date(now.getTime()+60000);[...env.timers.values()][0].fn();await settle();
 resolve({session:'closed'});await settle();assert.deepEqual(seen,[null,{session:'active'}]);assert.equal(env.timers.size,1);stop();
});
test('hidden then visible during an abort ignores obsolete results and starts one new request',async()=>{
 const env=environment();let calls=0,resolve;const seen=[];
 const stop=liveRefresh(()=>++calls===1?new Promise(r=>resolve=r):Promise.resolve({session:'active'}),data=>seen.push(data),15000,env.visibility,env.scheduler,()=>{},()=>new Date('2026-10-12T10:00:00+07:00'),env.visibility);
 env.change('hidden');env.change('visible');env.listeners.get('focus')();await settle();
 assert.equal(calls,2);resolve({session:'closed'});await settle();assert.deepEqual(seen,[{session:'active'}]);assert.equal(env.timers.size,1);stop();
});
test('failed/unknown recovery respects lunch, closing and weekend boundaries',async()=>{
 for(const [at,target] of [
  ['2026-10-12T11:29:30+07:00','2026-10-12T13:00:00+07:00'],
  ['2026-10-12T12:00:00+07:00','2026-10-12T13:00:00+07:00'],
  ['2026-10-12T14:59:30+07:00','2026-10-13T09:00:00+07:00'],
  ['2026-10-10T10:00:00+07:00','2026-10-12T09:00:00+07:00'],
 ]) {
  const env=environment(),now=new Date(at);
  const stop=liveRefresh(async()=>{throw Error();},()=>{},15000,env.visibility,env.scheduler,()=>{},()=>now);
  await settle();assert.equal([...env.timers.values()][0].delay,new Date(target)-now);stop();
 }
});
test('midday break wakes at 13:00 and returns to active cadence',async()=>{
 const env=environment();let now=new Date('2026-10-12T11:45:00+07:00'),calls=0;
 const stop=liveRefresh(async()=>({session:++calls===1?'break':'active'}),()=>{},15000,env.visibility,env.scheduler,()=>{},()=>now);
 await settle();assert.equal([...env.timers.values()][0].delay,75*60*1000);
 now=new Date('2026-10-12T13:00:00+07:00');[...env.timers.values()][0].fn();await settle();
 assert.equal(calls,2);assert.equal([...env.timers.values()][0].delay,15000);stop();
});
