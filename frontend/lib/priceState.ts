import type {LiveSnapshot} from './live-market.ts';
import {quoteStatus} from './newsPresentation.ts';

export type PriceState='CEILING'|'ADVANCING'|'REFERENCE'|'DECLINING'|'FLOOR'|'STALE'|'UNAVAILABLE'|'UNKNOWN'|'ERROR';
const positive=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v)&&v>0;
const finite=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v);

/** Exact source values only. Day-effective limits are distinct from tick observations. */
export function resolvePriceState(symbol:string,row:LiveSnapshot|null|undefined,status:string,now=new Date(),failed=false):PriceState {
  if(failed||status==='error')return 'ERROR';
  if(!row||status==='unavailable'||row.ticker!==symbol||!positive(row.last_price))return 'UNAVAILABLE';
  if(status==='unknown')return 'UNKNOWN';
  if(quoteStatus({status:status==='fresh'?'fresh':'stale',snapshot:row},false,now)!=='fresh')return 'STALE';
  const sourceDay=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(row.updated_at));
  if(sourceDay!==row.trading_date)return 'STALE';
  if(row.price_unit!=null&&row.price_unit!=='VND')return 'UNKNOWN';
  const change=row.change,reference=row.reference_price;
  if(!finite(change)||reference!=null&&(!positive(reference)||row.last_price-reference!==change)||
    row.change_percent!=null&&(!finite(row.change_percent)||Math.sign(row.change_percent)!==Math.sign(change)))return 'UNKNOWN';
  const limits=row.price_limits;
  if(limits?.qualification==='qualified'&&limits.symbol===symbol&&limits.trading_date===row.trading_date&&
    row.price_unit==='VND'&&limits.unit==='VND'&&limits.source&&limits.ceiling_field&&limits.floor_field&&
    positive(reference)&&positive(limits.floor)&&positive(limits.ceiling)&&limits.floor<reference&&reference<limits.ceiling&&
    (limits.effectiveness==='trading_day'?limits.reference_price===reference:
      Number.isFinite(Date.parse(limits.observed_at??''))&&Date.parse(limits.observed_at!)===Date.parse(row.updated_at))) {
    if(row.last_price===limits.ceiling)return 'CEILING';
    if(row.last_price===limits.floor)return 'FLOOR';
  }
  return change>0?'ADVANCING':change<0?'DECLINING':positive(reference)&&row.last_price===reference?'REFERENCE':'UNKNOWN';
}
export const priceStateLabel:Record<PriceState,string>={CEILING:'Ceiling',ADVANCING:'Up',REFERENCE:'Reference price',DECLINING:'Down',FLOOR:'Floor',STALE:'Stale',UNAVAILABLE:'Unavailable',UNKNOWN:'Unknown',ERROR:'Quote request failed'};
export function priceStateClass(state:PriceState) {
  const legacy:Partial<Record<PriceState,string>>={CEILING:'ceiling',ADVANCING:'positive',REFERENCE:'unchanged',DECLINING:'negative',FLOOR:'floor'};
  return `price-state price-${state.toLowerCase()} ${legacy[state]??'text-muted-foreground'}`;
}
