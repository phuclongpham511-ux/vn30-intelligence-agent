import type {AttentionUpdate,UpdatePage} from './watchlist.ts';

export type FinancialEvidence = {source:string;capture_id:string;capture_sha256:string;packet_sha256:string;limitations:string[];
 insight:{ticker:string;metric:string;unit:string;current_period:string;comparison_period:string;
 current_value:number;comparison_value:number;absolute_change:number;percentage_change:number|null;
 qualification_status:'COMPARABLE';causal_explanation:null;missing_information:string[];
 attention_reason:{policy:'financial-attention-v1';noteworthy:true;criteria:string[];thresholds:{relative_movement:number}};evidence_references:Record<string,unknown>[]}};
export type FinancialCheck = {metric:string;status:'READY'|'MISSING_DATA'|'INSUFFICIENT_COMPARISON';
 current_period:string|null;comparison_period:string|null;noteworthy:boolean;reasons:string[]};
export type FinancialPage = UpdatePage & {status:'READY'|'MISSING_DATA'|'INSUFFICIENT_COMPARISON'|'UNAVAILABLE'|'NOT_CHECKED';reasons:string[];
 profile?:'qualified-v58';checks?:FinancialCheck[]};
const strings=(v:unknown):v is string[]=>Array.isArray(v)&&v.every(x=>typeof x==='string');
const digest=(v:unknown)=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
export function parseFinancialPage(value:unknown,symbol:string):FinancialPage {
 const p=value as FinancialPage;
 const expanded=p?.profile==='qualified-v58';
 const metrics=expanded?['revenue','net_profit','customer_loans']:['revenue'];
 if(!p||!['READY','MISSING_DATA','INSUFFICIENT_COMPARISON','UNAVAILABLE','NOT_CHECKED'].includes(p.status)||
  (p.profile!==undefined&&!expanded)||!strings(p.reasons)||p.has_more!==false||p.truncated!==false||!Array.isArray(p.items)||p.items.length>(expanded?2:1)||
  (p.status!=='READY'&&p.items.length))throw Error('Invalid private financial page');
 if(expanded&&(!Array.isArray(p.checks)||p.checks.length>2||new Set(p.checks.map(c=>c.metric)).size!==p.checks.length||
  p.checks.some(c=>!metrics.includes(c.metric)||!['READY','MISSING_DATA','INSUFFICIENT_COMPARISON'].includes(c.status)||
   typeof c.noteworthy!=='boolean'||(c.status!=='READY'&&c.noteworthy)||!strings(c.reasons)||
   ![c.current_period,c.comparison_period].every(v=>v===null||typeof v==='string'&&/^\d{4}$/.test(v)))))throw Error('Invalid financial checks');
 if(new Set(p.items.map(i=>i.id)).size!==p.items.length||new Set(p.items.map(i=>(i.evidence as FinancialEvidence)?.insight?.metric)).size!==p.items.length)throw Error('Duplicate financial updates');
 for(const item of p.items){
  const e=item.evidence as FinancialEvidence,i=e?.insight;
  if(item.kind!=='financial'||!digest(item.entity_id)||item.id!=='financial:'+item.entity_id||!digest(item.revision)||
   typeof item.title!=='string'||item.url!=='/stocks/'+symbol+'#stock-fundamentals'||!e||!strings(e.limitations)||
   !digest(e.capture_id)||!digest(e.capture_sha256)||!digest(e.packet_sha256)||typeof e.source!=='string'||
   !i||i.ticker!==symbol||!metrics.includes(i.metric)||i.unit!=='VND'||i.qualification_status!=='COMPARABLE'||
   i.causal_explanation!==null||i.attention_reason?.policy!=='financial-attention-v1'||!i.attention_reason.noteworthy||!strings(i.attention_reason.criteria)||
   !Number.isFinite(i.attention_reason.thresholds?.relative_movement)||
   !strings(i.missing_information)||!Array.isArray(i.evidence_references)||!i.evidence_references.length||
   !/^\d{4}$/.test(i.current_period)||!/^\d{4}$/.test(i.comparison_period)||
   ![i.current_value,i.comparison_value,i.absolute_change].every(v=>typeof v==='number'&&Number.isFinite(v))||
   (i.percentage_change!==null&&(typeof i.percentage_change!=='number'||!Number.isFinite(i.percentage_change))))
   throw Error('Invalid private financial update');
  if(expanded&&!p.checks!.some(c=>c.metric===i.metric&&c.status==='READY'&&c.noteworthy&&
   c.current_period===i.current_period&&c.comparison_period===i.comparison_period))throw Error('Financial check mismatch');
 }
 return p;
}
