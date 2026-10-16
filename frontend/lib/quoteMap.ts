import type {LiveItem} from './live-market.ts';
import {quoteStatus} from './newsPresentation.ts';

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
