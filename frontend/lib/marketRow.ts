import type {PriceState} from './priceState.ts';

/** Presentation buckets only: percentage points, never price-band qualification. */
export function marketRowStrength(state:PriceState,changePercent:unknown):'low'|'medium'|'high'|undefined {
  if((state!=='ADVANCING'&&state!=='DECLINING')||typeof changePercent!=='number'||!Number.isFinite(changePercent)||
    changePercent===0||(state==='ADVANCING')!==(changePercent>0))return undefined;
  const magnitude=Math.abs(changePercent);
  return magnitude<1?'low':magnitude<3?'medium':'high';
}
