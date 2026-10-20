import type {FundamentalResearch} from './types.ts';

export type VerificationStatus='VERIFIED'|'PARTIALLY_VERIFIED'|'UNAVAILABLE';
export type FinancialVerification={
 contract:'financial-verification-v1';ticker:string;frequency:'annual'|'quarterly'|'ttm';
 audience:'public'|'personal_research'|'internal_research';
 statuses:Record<VerificationStatus,number>;displayed_metric_ids:string[];
 point_in_time_qualified:false;
 periods:{period:string;metrics:Record<string,{status:VerificationStatus;display_eligible:boolean;public_display_eligible:boolean;missing_evidence:string[]}>}[];
};

/** Evidence labels cannot authorize values or promote a private response. */
export function validateFinancialVerification(data:FundamentalResearch){
 const v=data.verification;if(v===undefined||v===null)return;
 if(v.contract!=='financial-verification-v1'||v.ticker!==data.ticker||v.frequency!==data.period_type||v.audience!==(data.display_scope||'public')||v.point_in_time_qualified!==false||!Array.isArray(v.periods)||v.periods.length!==data.rows.length||!Array.isArray(v.displayed_metric_ids)||!v.statuses)throw Error('Invalid financial verification ownership');
 const counts={VERIFIED:0,PARTIALLY_VERIFIED:0,UNAVAILABLE:0},visible:string[]=[];
 for(const [index,period] of v.periods.entries()){
  if(period.period!==data.rows[index].period||!period.metrics||typeof period.metrics!=='object'||Object.keys(period.metrics).length>100)throw Error('Invalid verification period');
  for(const [key,metric] of Object.entries(period.metrics)){
   if(!/^[a-z][a-z0-9_]{0,79}$/.test(key)||!metric||!Object.hasOwn(counts,metric.status)||typeof metric.display_eligible!=='boolean'||typeof metric.public_display_eligible!=='boolean'||!Array.isArray(metric.missing_evidence)||metric.missing_evidence.some(m=>typeof m!=='string')||metric.missing_evidence.length>30)throw Error('Invalid financial evidence grade');
   const value=(data.rows[index] as unknown as Record<string,unknown>)[key];
   const present=typeof value==='number'&&Number.isFinite(value)&&!data.is_fixture;
   if(metric.display_eligible!==present||metric.public_display_eligible&&(!present||v.audience!=='public')||metric.status==='VERIFIED'&&metric.missing_evidence.some(m=>m!=='public_display_permission')||metric.status==='UNAVAILABLE'&&present)throw Error('Verification cannot authorize financial values');
   if(index===v.periods.length-1){counts[metric.status]++;if(present)visible.push(key);}
  }
 }
 if(Object.keys(v.statuses).length!==3||Object.entries(counts).some(([key,n])=>v.statuses[key as VerificationStatus]!==n)||JSON.stringify([...v.displayed_metric_ids].sort())!==JSON.stringify(visible.sort()))throw Error('Invalid verification coverage');
}

export const verificationEvidence:Record<string,string>={
 reporting_scope:'Consolidated or separate reporting scope',
 compatible_reporting_scope:'Compatible reporting scope',
 original_unit:'Original reported unit',original_currency:'Original reported currency',
 fiscal_boundaries:'Original fiscal boundaries',
 qualified_publication_timestamp:'Qualified publication timestamp',
 original_document_verification:'Original document and page verification',
 public_display_permission:'Applicable public display permission',
 source_identity_and_hash:'Source identifiers and receipt hashes',
 required_source_fields:'Required source fields',
};
