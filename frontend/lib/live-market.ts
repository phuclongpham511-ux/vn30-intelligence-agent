export type Session = 'active'|'break'|'closed'|'unknown';
export type LiveStatus = 'fresh'|'stale'|'unavailable';
export type LiveSnapshot = {ticker:string;last_price:number;reference_price:number|null;change:number|null;change_percent:number|null;open:number|null;high:number|null;low:number|null;total_volume:number|null;total_value:number|null;trading_date:string;updated_at:string;source:string;session:Session};
export type LiveItem = {status:LiveStatus;snapshot:LiveSnapshot|null};
export type LiveBatch = {items:Record<string,LiveItem>;session:Session;as_of:string};
export type LiveIndex = {snapshot:(import('./marketIndex').IndexSnapshot & {updated_at:string;session:Session})|null;status:LiveStatus;session:Session;as_of:string};

export const visibleSymbols=(symbols:string[])=>[...new Set(symbols.map(s=>s.trim().toUpperCase()))].sort().join(',');
export function movement(change:number|null|undefined) {
  return change==null ? {label:'Unavailable',color:'text-muted-foreground'} : change>0 ? {label:'Up',color:'text-emerald-600 dark:text-emerald-400'} : change<0 ? {label:'Down',color:'text-red-600 dark:text-red-400'} : {label:'Unchanged',color:'text-muted-foreground'};
}
export function indexMascot(session:Session,change:number|null|undefined) {
  return session==='active' ? 'marketWatching' : change!=null && change>0 ? 'marketUp' : change!=null && change<0 ? 'marketDown' : 'marketNeutral';
}

type Visibility = {visibilityState:string;addEventListener:(name:string,handler:()=>void)=>void;removeEventListener:(name:string,handler:()=>void)=>void};
type Scheduler = {set:(callback:()=>void,delay:number)=>unknown;clear:(timer:unknown)=>void};
export function liveRefresh<T extends {session:Session}>(load:(signal:AbortSignal)=>Promise<T>,receive:(data:T|null)=>void,interval:number,visibility:Visibility,scheduler:Scheduler,release:()=>void=()=>{}) {
  let stopped=false, timer:unknown, controller:AbortController|null=null, initialChecks=0;
  const clear=()=>{if(timer!==undefined){scheduler.clear(timer);timer=undefined;}};
  const run=async()=>{
    clear(); controller?.abort();
    if(stopped||visibility.visibilityState==='hidden')return;
    const request=new AbortController(); controller=request;
    let result:T|null=null;
    try {result=await load(request.signal); if(!request.signal.aborted&&!stopped)receive(result);}
    catch {if(!request.signal.aborted&&!stopped)receive(null);}
    if(stopped||request.signal.aborted||visibility.visibilityState==='hidden')return;
    if(result?.session==='closed')return;
    let delay=result?.session==='active'?interval:60000;
    if(result?.session==='unknown' && initialChecks++<3)delay=Math.min(interval,15000);
    if(result?.session==='break') {
      const now=new Date(); const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Ho_Chi_Minh',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(now);
      const get=(type:string)=>Number(parts.find(p=>p.type===type)?.value);
      delay=Math.max(1000,((13-get('hour'))*3600-get('minute')*60-get('second'))*1000);
    }
    timer=scheduler.set(()=>void run(),delay);
  };
  const changed=()=>{clear();controller?.abort();if(visibility.visibilityState!=='hidden')void run();else release();};
  visibility.addEventListener('visibilitychange',changed); void run();
  return ()=>{stopped=true;clear();controller?.abort();release();visibility.removeEventListener('visibilitychange',changed);};
}
