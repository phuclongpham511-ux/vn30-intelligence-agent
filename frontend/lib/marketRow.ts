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
  const magnitude=Math.min(Math.abs(changePercent as number),7);
  // Reach the approved original hue at 3%; keep 1% vs 2% visibly separated.
  const pale=state==='ADVANCING'?[238,250,244]:[255,241,243];
  const original=state==='ADVANCING'?[101,228,178]:[255,145,160];
  const deep=state==='ADVANCING'?[47,189,135]:[239,105,125];
  const [from,to,amount]=magnitude<=3?[pale,original,magnitude/3] as const:[original,deep,(magnitude-3)/4] as const;
  return '#'+from.map((value,i)=>Math.round(value+(to[i]-value)*amount).toString(16).padStart(2,'0')).join('');
}
