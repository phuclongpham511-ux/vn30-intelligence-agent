import type {LiveItem} from './live-market.ts';
import type {LiveBatch} from './live-market.ts';
import {quoteStatus} from './newsPresentation.ts';

export const boardPageSize=30;
export const boardDefaultGroup='VN30';
export type BoardIdentity={symbol:string;company_name?:string|null;display_name_en?:string|null;exchange?:string|null};
export type BoardSort='change'|'fallers'|'ticker'|'price';

/** Presentation only: source values stay unchanged; no breadth, weights or returns. */
export function quoteMapCell(symbol:string,item:LiveItem|undefined,failed=false,now=new Date()) {
  const row=item?.snapshot;
  if(!row||item?.status==='unavailable'||row.ticker!==symbol||!Number.isFinite(row.last_price)||row.last_price<=0)
    return {row:null,status:'unavailable' as const,tone:'neutral' as const};
  const status=quoteStatus(item,failed,now);
  const change=row.change;
  const tone:'up'|'down'|'unchanged'|'neutral'=status!=='fresh'||change==null||!Number.isFinite(change)?'neutral':change>0?'up':change<0?'down':'unchanged';
  return {row,status,tone};
}

/** Compare source values only. Counts/order are UI organization, never index returns. */
export function boardRows(stocks:BoardIdentity[],data:LiveBatch|null,failed=false,now=new Date(),sort:BoardSort='change') {
  return stocks.map(stock=>({stock,...quoteMapCell(stock.symbol,data?.items[stock.symbol],failed,now)})).sort((a,b)=>{
    const identity=()=>a.stock.symbol.localeCompare(b.stock.symbol);
    if(sort==='ticker')return identity();
    const value=(r:typeof a)=>sort==='price'?r.row?.last_price:r.row?.change_percent;
    const av=value(a),bv=value(b),valid=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v);
    const rank=(r:typeof a)=>!r.row?3:!valid(value(r))?2:r.status==='fresh'?0:1;
    if(rank(a)!==rank(b))return rank(a)-rank(b);
    if(!valid(av))return valid(bv)?1:identity();
    if(!valid(bv))return -1;
    return (sort==='fallers'?av-bv:bv-av)||identity();
  });
}
export function boardColumns<T>(rows:T[]):T[][] {
  const count=Math.min(3,Math.ceil(rows.length/10));
  if(!count)return [];
  const columns:T[][]=[];let offset=0;
  for(let index=0;index<count;index++){
    const size=Math.ceil((rows.length-offset)/(count-index));
    columns.push(rows.slice(offset,offset+size));offset+=size;
  }
  return columns;
}
