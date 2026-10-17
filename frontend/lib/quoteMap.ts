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

export type BoardRow=ReturnType<typeof boardRows>[number];
/** Compare only a known, single trading-date/session cohort from this loaded page. */
export function sampleObservations(stocks:BoardIdentity[],data:LiveBatch|null,failed=false,now=new Date()) {
  const rows=boardRows(stocks,data,failed,now);
  const candidates=rows.filter(r=>r.status==='fresh'&&typeof r.row?.change_percent==='number'&&Number.isFinite(r.row.change_percent));
  const cohorts=new Set(candidates.map(r=>r.row!.trading_date+'|'+r.row!.session));
  const comparable=!!data&&!failed&&data.session!=='unknown'&&candidates.length>=2&&cohorts.size===1&&candidates.every(r=>r.row!.session===data.session);
  const groups=movementGroups(comparable?candidates:[]);
  return {rows,comparable,groups,compared:comparable?candidates.length:0,
    gainers:groups.advancing.slice(0,4),
    decliners:[...groups.declining].sort((a,b)=>a.row!.change_percent!-b.row!.change_percent!||a.stock.symbol.localeCompare(b.stock.symbol)).slice(0,4),
    available:data&&!failed?rows.filter(r=>r.row).length:null,
    stale:rows.filter(r=>r.status==='stale').length,missing:rows.filter(r=>!r.row).length};
}
export type MovementGroup='advancing'|'declining'|'unchanged'|'unqualified';
/** Organization of this loaded sample only; never a sector or market-wide metric. */
export function movementGroups(rows:BoardRow[]) {
  const result:Record<MovementGroup,BoardRow[]>={advancing:[],declining:[],unchanged:[],unqualified:[]};
  for(const row of rows){
    const value=row.row?.change_percent;
    const key=row.status!=='fresh'||typeof value!=='number'||!Number.isFinite(value)?'unqualified':value>0?'advancing':value<0?'declining':'unchanged';
    result[key].push(row);
  }
  return result;
}
export type HeatBin='negative-strong'|'negative'|'zero'|'positive'|'positive-strong'|'neutral';
export function heatmapBin(row:BoardRow):HeatBin {
  const value=row.row?.change_percent;
  if(row.status!=='fresh'||typeof value!=='number'||!Number.isFinite(value))return 'neutral';
  return value<=-1?'negative-strong':value<0?'negative':value===0?'zero':value<1?'positive':'positive-strong';
}
