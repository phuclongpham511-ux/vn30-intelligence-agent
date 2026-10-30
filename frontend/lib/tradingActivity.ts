import type {LiveSnapshot,LiveStatus} from './live-market.ts';
import {resolvePriceState} from './priceState.ts';

/** Never interpret legacy totals, interval volume or price*volume as session activity. */
export function activityValue(row:LiveSnapshot|null|undefined,key:'volume'|'value',status:string,now=new Date()):number|null {
  const a=row?.trading_activity,m=a?.[key];
  if(!row||status!=='fresh'||!a||!m||m.qualification!=='qualified'||!a.source||!m.field||
    a.symbol!==row.ticker||a.trading_date!==row.trading_date||a.session!=='trading_day'||
    a.scope!=='regular_matched'||a.cumulative!==true||a.includes_negotiated_trades!==false||
    m.unit!==(key==='volume'?'shares':'VND')||typeof m.value!=='number'||!Number.isFinite(m.value)||m.value<0||
    Math.abs(m.value)>Number.MAX_SAFE_INTEGER||(key==='volume'&&!Number.isSafeInteger(m.value))||
    !((typeof m.raw_value==='number'&&Number.isFinite(m.raw_value))||(typeof m.raw_value==='string'&&/^\d+(?:\.\d+)?$/.test(m.raw_value)))||Number(m.raw_value)!==m.value)return null;
  const timestamp=Date.parse(a.observed_at),priceTime=Date.parse(row.updated_at);
  const day=(v:Date)=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).format(v);
  if(!Number.isFinite(timestamp)||timestamp>now.getTime()+5000||timestamp!==priceTime||
    day(new Date(timestamp))!==a.trading_date||day(now)!==a.trading_date)return null;
  return m.value;
}
export function activityNumber(value:number|null,key:'volume'|'value',language:'en'|'vi') {
  if(value===null)return '—';
  const locale=language==='vi'?'vi-VN':'en-GB';
  const divisor=key==='value'?(value>=1e9?1e9:value>=1e6?1e6:1):(value>=1e6?1e6:value>=1e3?1e3:1);
  const suffix=divisor===1?'':language==='vi'?(divisor===1e9?' tỷ':divisor===1e6?' triệu':' K'):(divisor===1e9?' B':divisor===1e6?' M':' K');
  return new Intl.NumberFormat(locale,{maximumFractionDigits:divisor===1?8:2}).format(value/divisor)+suffix;
}
/** Exact qualified limits only; no assumed percentage or exchange limit. */
export function priceLimitTone(row:LiveSnapshot|null|undefined,status:string,now=new Date()):'ceiling'|'floor'|null {
  const state=resolvePriceState(row?.ticker??'',row,status,now);
  return state==='CEILING'?'ceiling':state==='FLOOR'?'floor':null;
}
