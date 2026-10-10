export type IndexSnapshot = {index:string;level:number;change:number|null;change_percent:number|null;total_volume:number|null;total_value:number|null;trading_date:string;source:string;fetched_at:string};
export function indexMovement(data:IndexSnapshot|null) {
  const change=data?.change;
  return change==null || !Number.isFinite(change) ? {label:'Direction unavailable',mascot:'marketUncertain',color:'text-muted-foreground'} as const : change>0 ? {label:'Up',mascot:'marketUp',color:'text-emerald-600 dark:text-emerald-400'} as const : change<0 ? {label:'Down',mascot:'marketDown',color:'text-red-600 dark:text-red-400'} as const : {label:'Unchanged',mascot:'marketNeutral',color:'text-muted-foreground'} as const;
}

export const signedIndex=(value:number|null,suffix='',locale='en-GB')=>value==null?'Unavailable':`${value>0?'+':''}${value.toLocaleString(locale,{minimumFractionDigits:2,maximumFractionDigits:2})}${suffix}`;
export const indexAggregate=(value:number|null|undefined,unit:string,locale='en-GB')=>value==null?'Unavailable':`${value.toLocaleString(locale,{notation:'compact',maximumFractionDigits:2})} ${unit}`;
export const indexDate=(date:string)=>new Date(date+'T00:00:00').toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});

export function indexDisplayStatus(data:import('./live-market').LiveIndex|null,failed=false,now=new Date()) {
  if(!data?.snapshot||data.status==='unavailable')return 'unavailable';
  const day=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
  const updated=Date.parse(data.snapshot.updated_at);
  if(failed||data.status==='stale'||day!==data.snapshot.trading_date||!Number.isFinite(updated)||updated>now.getTime()+5000)return 'stale';
  // A browser left open cannot keep labelling an old active-session snapshot fresh.
  if((data.session==='active'||data.session==='unknown')&&now.getTime()-updated>120000)return 'stale';
  return 'fresh';
}
