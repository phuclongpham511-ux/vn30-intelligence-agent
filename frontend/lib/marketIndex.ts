export type IndexSnapshot = {index:string;level:number;change:number|null;change_percent:number|null;trading_date:string;source:string;fetched_at:string};
export function indexMovement(data:IndexSnapshot|null) {
  const change=data?.change;
  return change==null || !Number.isFinite(change) ? {label:'Direction unavailable',mascot:'marketUncertain',color:'text-muted-foreground'} as const : change>0 ? {label:'Up',mascot:'marketUp',color:'text-emerald-600 dark:text-emerald-400'} as const : change<0 ? {label:'Down',mascot:'marketDown',color:'text-red-600 dark:text-red-400'} as const : {label:'Unchanged',mascot:'marketNeutral',color:'text-muted-foreground'} as const;
}
