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
// Reuse the repository's explicit unresolved-correction marker, not guesses from prose.
export function actionConflict(row:ActionObservation) {return row.verification_note?.startsWith('Unresolved correction')===true;}
export function actionStatus(row:ActionObservation) {
  return row.withdrawn===true?'Withdrawn':actionConflict(row)?'Unresolved correction':row.verified!==true?'Pending verification':row.is_fixture===true?'Fixture observation':trustedAction(row)?'Source-marked verified':'Pending verification';
}
// Pending corrections and test observations cannot become trusted event terms.
export function trustedAction(row:ActionObservation) {return row.verified===true&&row.withdrawn===false&&row.is_fixture===false&&!!row.source?.trim()&&!actionConflict(row);}
export type ActionCategory='all'|'distributions'|'other';
export function actionHistory(items:ActionObservation[],category:ActionCategory='all') {
  return items.filter(row=>category==='all'||['cash_dividend','stock_dividend','bonus_shares'].includes(row.action_type)===(category==='distributions'));
}
export function actionDate(row:ActionObservation,key:'effective_date'|'record_date'|'payment_date') {
  const value=row[key];
  if(!trustedAction(row)||typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))return null;
  const stamp=Date.parse(value+'T00:00:00Z');
  return Number.isFinite(stamp)&&new Date(stamp).toISOString().slice(0,10)===value?value:null;
}
/** Read the declared source units only; never infer a yield, ratio or adjustment. */
export function actionTerm(row:ActionObservation,key:'cash_vnd_per_share'|'new_shares_per_old'|'subscription_price_vnd') {
  const value=row.terms?.[key];
  const applicable=key==='cash_vnd_per_share'?row.action_type==='cash_dividend':key==='subscription_price_vnd'?
    ['rights_offering','additional_issuance'].includes(row.action_type):
    ['stock_dividend','bonus_shares','rights_offering','additional_issuance'].includes(row.action_type);
  return trustedAction(row)&&applicable&&typeof value==='number'&&Number.isFinite(value)&&value>=0&&value<=Number.MAX_SAFE_INTEGER?value:null;
}
/** Completeness of displayed fields only, never independent verification or payment. */
export function actionDetailsIncomplete(row:ActionObservation) {
  if(!trustedAction(row))return true;
  if((['effective_date','record_date','payment_date'] as const).some(key=>actionDate(row,key)===null))return true;
  switch(row.action_type) {
    case 'cash_dividend':return actionTerm(row,'cash_vnd_per_share')===null;
    case 'stock_dividend':case 'bonus_shares':return actionTerm(row,'new_shares_per_old')===null;
    case 'rights_offering':case 'additional_issuance':return actionTerm(row,'new_shares_per_old')===null||actionTerm(row,'subscription_price_vnd')===null;
    default:return true;
  }
}
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
