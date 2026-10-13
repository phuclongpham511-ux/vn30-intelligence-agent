import type {Security} from './types.ts';

export const stockSections = ['overview','fundamentals','technical','actions','news'] as const;
export type StockSection = typeof stockSections[number];
export function stockSection(hash:string):StockSection {
  const value=hash.replace(/^#stock-/, '');
  return stockSections.includes(value as StockSection)?value as StockSection:'overview';
}
export function stockIdentity(items:Security[],ticker:string):Security {
  const row=items.find(item=>item.symbol===ticker);
  if(!row)throw new Error('Stock identity unavailable');
  return row;
}
export type ActionObservation = {
  action_id:string; observation_id:string; symbol:string; observed_at:string;
  action_type:'cash_dividend'|'stock_dividend'|'bonus_shares'|'rights_offering'|'additional_issuance'|'other';
  effective_date:string|null;record_date:string|null;payment_date:string|null;
  announced_at:string|null;announced_on:string|null;
  source:string;source_url:string|null;supporting_urls:string[];
  source_title?:string|null;evidence_text?:string|null;source_revision:string|null;
  source_updated_at?:string|null;verification_note:string|null;
  verified:boolean;withdrawn:boolean;is_fixture:boolean;
  terms:{cash_vnd_per_share:number|null;new_shares_per_old:number|null;subscription_price_vnd:number|null}|null;
};
export type ActionPage={ticker:string;as_of:string;coverage:'INCOMPLETE';items:ActionObservation[];has_more:boolean};
export function actionStatus(row:ActionObservation) {
  return row.withdrawn?'Withdrawn':!row.verified?'Pending verification':row.is_fixture?'Fixture observation':'Verified source observation';
}
// Pending corrections and test observations cannot become trusted event terms.
export function trustedAction(row:ActionObservation) {return row.verified&&!row.withdrawn&&!row.is_fixture;}
export function actionUrl(value:string|null|undefined) {
  try {const url=new URL(value||'');return ['https:','http:'].includes(url.protocol)&&!url.username&&!url.password?url.href:null;}catch{return null;}
}
export async function stockRead<T>(url:string,signal:AbortSignal,request:typeof fetch=fetch):Promise<T> {
  const response=await request(url,{signal,cache:'no-store'});
  if(!response.ok)throw new Error('Stock data unavailable');
  const data:T=await response.json();
  signal.throwIfAborted();
  return data;
}
