import type {PriceState} from './priceState.ts';

/** Presentation buckets only: percentage points, never price-band qualification. */
export function marketRowStrength(state:PriceState,changePercent:unknown):'low'|'medium'|'high'|undefined {
  if((state!=='ADVANCING'&&state!=='DECLINING')||typeof changePercent!=='number'||!Number.isFinite(changePercent)||
    changePercent===0||(state==='ADVANCING')!==(changePercent>0))return undefined;
  const magnitude=Math.abs(changePercent);
  return magnitude<1?'low':magnitude<3?'medium':'high';
}

/** Continuous visual scale, capped at 7 percentage points; not a trading limit. */
export function marketRowFill(state:PriceState,changePercent:unknown):string|undefined {
  if(!marketRowStrength(state,changePercent))return undefined;
  const from=state==='ADVANCING'?[220,242,222]:[253,231,231];
  const to=state==='ADVANCING'?[112,197,128]:[241,143,151];
  const amount=Math.min(Math.abs(changePercent as number)/7,1);
  return '#'+from.map((value,i)=>Math.round(value+(to[i]-value)*amount).toString(16).padStart(2,'0')).join('');
}
