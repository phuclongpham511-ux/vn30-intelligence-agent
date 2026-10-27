// Server-only. Never changes the public Watchlist API or its source projections.
import {personalBackend,personalRuntimeEnabled} from './personal-financial-server.ts';
import {parseFinancialPage,type FinancialPage} from './watchlist-financial.ts';
import type {Intelligence} from './watchlist.ts';

export function privateFinancialRequest(request:Request){
 const h=request.headers;
 return process.env.WOOFI_WATCHLIST_FINANCIALS==='1'&&process.env.APP_ENV==='development'&&personalRuntimeEnabled()&&
  new URL(request.url).hostname==='127.0.0.1'&&h.get('host')==='127.0.0.1:3431'&&
  (!h.get('origin')||h.get('origin')==='http://127.0.0.1:3431')&&
  (!h.get('sec-fetch-site')||['same-origin','none'].includes(h.get('sec-fetch-site')!))&&
  !h.has('x-forwarded-host')&&!h.has('forwarded');
}
export async function attachFinancialUpdates(data:Intelligence,symbols:string[],signal?:AbortSignal,request:typeof fetch=fetch):Promise<Intelligence>{
 const selected=symbols.slice(0,5);
 let rows:{symbol:string;financial:FinancialPage}[]=[];
 try{
  const response=await request(`${personalBackend()}/personal-research/watchlist-financials`,{method:'POST',
   headers:{'Content-Type':'application/json'},body:JSON.stringify({symbols:selected}),cache:'no-store',
   signal:AbortSignal.any([...(signal?[signal]:[]),AbortSignal.timeout(15000)])});
  if(!response.ok)throw Error('Private read unavailable');
  const body=await response.json();
  if(body.contract!=='private-watchlist-financial-v1'||!Array.isArray(body.stocks)||body.stocks.length!==selected.length||
    body.stocks.some((r:{symbol:string},index:number)=>r.symbol!==selected[index]))throw Error('Invalid private response');
  rows=body.stocks;
 }catch{/* Preserve News/Community/Technical even when private evidence is unavailable. */}
 const expanded=rows.some(r=>r.financial?.profile==='qualified-v58');
 return {...data,financial_scope:'private_research',stocks:data.stocks.map(row=>{
  let financial:FinancialPage={status:selected.includes(row.symbol)?'UNAVAILABLE':'NOT_CHECKED',items:[],
   reasons:[selected.includes(row.symbol)?'private_financial_read_unavailable':'bounded_to_first_five_symbols'],has_more:false,truncated:false,
   ...(expanded?{profile:'qualified-v58' as const,checks:[]}:{})};
  const candidate=rows.find(r=>r.symbol===row.symbol)?.financial;
  if(candidate)try{financial=parseFinancialPage({...candidate,items:candidate.items.map(item=>({...item,occurred_at:data.as_of}))},row.symbol);}catch{}
  return {...row,financial};
 })};
}
