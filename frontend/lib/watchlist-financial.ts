import type {AttentionUpdate,UpdatePage} from './watchlist.ts';

export type FinancialEvidence = {source:string;capture_id:string;capture_sha256:string;packet_sha256:string;limitations:string[];
 insight:{ticker:string;metric:string;unit:string;current_period:string;comparison_period:string;
 current_value:number;comparison_value:number;absolute_change:number;percentage_change:number|null;
 qualification_status:'COMPARABLE';causal_explanation:null;missing_information:string[];
 attention_reason:{policy:'financial-attention-v1';noteworthy:true;criteria:string[];thresholds:{relative_movement:number}};evidence_references:Record<string,unknown>[]}};
export type FinancialPage = UpdatePage & {status:'READY'|'MISSING_DATA'|'INSUFFICIENT_COMPARISON'|'UNAVAILABLE'|'NOT_CHECKED';reasons:string[]};
const strings=(v:unknown):v is string[]=>Array.isArray(v)&&v.every(x=>typeof x==='string');
const digest=(v:unknown)=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
export function parseFinancialPage(value:unknown,symbol:string):FinancialPage {
 const p=value as FinancialPage;
 if(!p||!['READY','MISSING_DATA','INSUFFICIENT_COMPARISON','UNAVAILABLE','NOT_CHECKED'].includes(p.status)||
  !strings(p.reasons)||p.has_more!==false||p.truncated!==false||!Array.isArray(p.items)||p.items.length>1||
  (p.status!=='READY'&&p.items.length))throw Error('Invalid private financial page');
 for(const item of p.items){
  const e=item.evidence as FinancialEvidence,i=e?.insight;
  if(item.kind!=='financial'||!digest(item.entity_id)||item.id!=='financial:'+item.entity_id||!digest(item.revision)||
   typeof item.title!=='string'||item.url!=='/stocks/'+symbol+'#stock-fundamentals'||!e||!strings(e.limitations)||
   !digest(e.capture_id)||!digest(e.capture_sha256)||!digest(e.packet_sha256)||typeof e.source!=='string'||
   !i||i.ticker!==symbol||i.metric!=='revenue'||i.unit!=='VND'||i.qualification_status!=='COMPARABLE'||
   i.causal_explanation!==null||i.attention_reason?.policy!=='financial-attention-v1'||!i.attention_reason.noteworthy||!strings(i.attention_reason.criteria)||
   !Number.isFinite(i.attention_reason.thresholds?.relative_movement)||
   !strings(i.missing_information)||!Array.isArray(i.evidence_references)||!i.evidence_references.length||
   !/^\d{4}$/.test(i.current_period)||!/^\d{4}$/.test(i.comparison_period)||
   ![i.current_value,i.comparison_value,i.absolute_change].every(v=>typeof v==='number'&&Number.isFinite(v))||
   (i.percentage_change!==null&&(typeof i.percentage_change!=='number'||!Number.isFinite(i.percentage_change))))
   throw Error('Invalid private financial update');
 }
 return p;
}
