export type Session = 'active'|'break'|'closed'|'unknown';
export type LiveStatus = 'fresh'|'stale'|'unavailable';
export type LiveSnapshot = {ticker:string;last_price:number;reference_price:number|null;change:number|null;change_percent:number|null;open:number|null;high:number|null;low:number|null;total_volume:number|null;total_value:number|null;trading_date:string;updated_at:string;source:string;session:Session};
export type LiveItem = {status:LiveStatus;snapshot:LiveSnapshot|null};
export type LiveBatch = {items:Record<string,LiveItem>;session:Session;as_of:string};
export type LiveIndex = {snapshot:(import('./marketIndex').IndexSnapshot & {updated_at:string;session:Session})|null;status:LiveStatus;session:Session;as_of:string};

export const visibleSymbols=(symbols:string[])=>[...new Set(symbols.map(s=>s.trim().toUpperCase()))].sort().join(',');
export function movement(change:number|null|undefined) {
  return change==null || !Number.isFinite(change) ? {label:'Unavailable',color:'text-muted-foreground'} : change>0 ? {label:'Up',color:'positive'} : change<0 ? {label:'Down',color:'negative'} : {label:'Unchanged',color:'unchanged'};
}
export function indexMascot(session:Session,change:number|null|undefined) {
  return session==='active' ? 'marketWatching' : change!=null && change>0 ? 'marketUp' : change!=null && change<0 ? 'marketDown' : 'marketNeutral';
}

type Events = {addEventListener:(name:string,handler:()=>void)=>void;removeEventListener:(name:string,handler:()=>void)=>void};
type Visibility = Events & {visibilityState:string};
type Scheduler = {set:(callback:()=>void,delay:number)=>unknown;clear:(timer:unknown)=>void};
function vietnamClock(now:Date) {
  const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'numeric',day:'numeric',hour:'numeric',minute:'numeric',hourCycle:'h23'}).formatToParts(now);
  const get=(type:string)=>Number(parts.find(p=>p.type===type)?.value);
  const day=Date.UTC(get('year'),get('month')-1,get('day'));
  return {day,minute:get('hour')*60+get('minute'),weekday:![0,6].includes(new Date(day).getUTCDay())};
}
function nextOpeningCheck(now:Date) {
  // 09:00 ICT is 02:00 UTC. This is a provider recheck, not proof of a trading day.
  let next=vietnamClock(now).day+2*3600000;
  while(next<=now.getTime()||[0,6].includes(new Date(next).getUTCDay()))next+=86400000;
  return next-now.getTime();
}
function recoveryDelay(now:Date,delay:number) {
  const local=vietnamClock(now);
  if(!local.weekday||local.minute<540||local.minute>=900)return nextOpeningCheck(now);
  const lunch=local.day+4.5*3600000,afternoon=local.day+6*3600000,close=local.day+8*3600000;
  if(local.minute>=690&&local.minute<780)return afternoon-now.getTime();
  if(local.minute<690&&now.getTime()+delay>=lunch)return afternoon-now.getTime();
  if(now.getTime()+delay>=close)return nextOpeningCheck(now);
  return delay;
}
export function liveRefresh<T extends {session:Session}>(load:(signal:AbortSignal)=>Promise<T>,receive:(data:T|null)=>void,interval:number,visibility:Visibility,scheduler:Scheduler,release:()=>void=()=>{},clock:()=>Date=()=>new Date(),foreground?:Events) {
  let stopped=false, timer:unknown, controller:AbortController|null=null, initialChecks=0, recoveryChecks=0;
  let closedDay=NaN,closedChecks=0,inFlight=false,pendingForeground=false,lastStart=-Infinity;
  const clear=()=>{if(timer!==undefined){scheduler.clear(timer);timer=undefined;}};
  const run=async()=>{
    if(stopped||visibility.visibilityState==='hidden'||inFlight)return;
    clear();inFlight=true;lastStart=clock().getTime();
    const request=new AbortController();controller=request;let timedOut=false;
    let abort:()=>void=()=>{};
    const cancelled=new Promise<never>((_,reject)=>{abort=()=>reject(Error('Live request aborted'));request.signal.addEventListener('abort',abort,{once:true});});
    const deadline=scheduler.set(()=>{timedOut=true;request.abort();},20000);
    let result:T|null=null;
    try {result=await Promise.race([load(request.signal),cancelled]);if(!request.signal.aborted&&!stopped)receive(result);}
    catch {if((!request.signal.aborted||timedOut)&&!stopped&&visibility.visibilityState!=='hidden')receive(null);}
    finally {scheduler.clear(deadline);request.signal.removeEventListener('abort',abort);inFlight=false;if(controller===request)controller=null;}
    if(pendingForeground){pendingForeground=false;if(!stopped&&visibility.visibilityState!=='hidden'){void run();return;}}
    if(timedOut)result=null;
    if(stopped||(request.signal.aborted&&!timedOut)||visibility.visibilityState==='hidden')return;
    const now=clock(),local=vietnamClock(now);
    if(closedDay!==local.day){closedDay=local.day;closedChecks=0;}
    let delay=result?.session==='active'?interval:60000;
    if(result?.session==='active'){initialChecks=0;recoveryChecks=0;}
    else if(result?.session==='closed') {
      // At most three slow checks per ICT date handle a delayed opening/closure.
      delay=local.weekday&&local.minute>=540&&local.minute<900&&closedChecks<3
        ?recoveryDelay(now,60000*2**closedChecks++):nextOpeningCheck(now);
    } else {
      delay=60000*2**Math.min(recoveryChecks++,4);
      delay=Math.min(delay,900000);
      if(result?.session==='unknown'&&initialChecks++<3){delay=Math.min(interval,15000);recoveryChecks=0;}
      delay=recoveryDelay(now,delay);
    }
    timer=scheduler.set(()=>void run(),delay);
  };
  const changed=()=>{
    if(stopped)return;
    if(visibility.visibilityState==='hidden'){clear();controller?.abort();release();return;}
    if(inFlight){pendingForeground=!!controller?.signal.aborted;return;}
    // visibilitychange, focus and pageshow commonly describe the same activation.
    if(clock().getTime()-lastStart<1000&&timer!==undefined)return;
    clear();void run();
  };
  visibility.addEventListener('visibilitychange',changed); void run();
  foreground?.addEventListener('focus',changed);foreground?.addEventListener('pageshow',changed);
  return ()=>{stopped=true;clear();controller?.abort();release();visibility.removeEventListener('visibilitychange',changed);foreground?.removeEventListener('focus',changed);foreground?.removeEventListener('pageshow',changed);};
}
