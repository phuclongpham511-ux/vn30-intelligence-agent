export type IndustryMetric={value:number|null;unit:'VND'|'fraction'|'multiple';status:'COMPLETE'|'PARTIAL'|'UNAVAILABLE';included_companies:number;expected_companies:number;coverage:number|null;method:string;excluded:Record<string,string>;peers:{ticker:string;value:number;rank:number;percentile:number;contribution:number|null;sources:string[];revisions:string[]}[]};
export type IndustrySnapshot={contract:'industry-financials-v1';industry:{id:string;name_en:string;name_vi:string;model:string};taxonomy:{name:string;version:string;source_reference:string};period:string;frequency:'annual'|'quarterly'|'ttm';membership_on:string;report_scope:'consolidated'|'standalone';expected_companies:number;represented_companies:number;missing_tickers:string[];metrics:Record<string,IndustryMetric>;point_in_time_qualified:false;limitations:string[];is_fixture?:boolean};
export type IndustryDirectory={contract:'industry-directory-v1';status:'AVAILABLE'|'UNAVAILABLE';taxonomy:IndustrySnapshot['taxonomy']|null;industries:IndustrySnapshot['industry'][]};

/** Accept public qualified aggregates; DEMO requires an explicit isolated caller. */
export function industryData(value:IndustrySnapshot,industry:string,period:string,allowDemo=false):IndustrySnapshot{
 if(!value||value.contract!=='industry-financials-v1'||value.industry?.id!==industry||value.period!==period||!/^\d{4}(?:-Q[1-4])?$/.test(period)||!value.taxonomy?.version||!value.taxonomy.source_reference||!value.metrics||typeof value.metrics!=='object'||Object.keys(value.metrics).length>40||!Array.isArray(value.limitations)||!Array.isArray(value.missing_tickers))throw Error('Invalid industry ownership');
 if(value.is_fixture&&!allowDemo)throw Error('Demo industry data is not public evidence');
 for(const metric of Object.values(value.metrics)){
  if(!metric||!['COMPLETE','PARTIAL','UNAVAILABLE'].includes(metric.status)||!['VND','fraction','multiple'].includes(metric.unit)||!Number.isInteger(metric.included_companies)||!Number.isInteger(metric.expected_companies)||metric.included_companies<0||metric.included_companies>metric.expected_companies||metric.expected_companies!==value.expected_companies||!Array.isArray(metric.peers)||typeof metric.method!=='string'||!metric.excluded)throw Error('Invalid industry coverage');
  if(metric.value!==null&&(typeof metric.value!=='number'||!Number.isFinite(metric.value))||metric.status==='UNAVAILABLE'&&metric.value!==null||metric.status!=='UNAVAILABLE'&&(metric.value===null||!metric.included_companies)||metric.status==='COMPLETE'&&metric.included_companies!==metric.expected_companies)throw Error('Invalid industry value');
  if(metric.coverage!==(metric.expected_companies?metric.included_companies/metric.expected_companies:null)||metric.peers.length!==metric.included_companies)throw Error('Industry coverage does not match cohort');
  const seen=new Set<string>();
  for(const peer of metric.peers){
   if(!/^[A-Z0-9]{1,20}$/.test(peer.ticker)||seen.has(peer.ticker)||!Number.isFinite(peer.value)||!Number.isInteger(peer.rank)||peer.rank<1||peer.rank>metric.peers.length||!Number.isFinite(peer.percentile)||peer.percentile<0||peer.percentile>1||peer.contribution!==null&&!Number.isFinite(peer.contribution)||!Array.isArray(peer.sources)||!peer.sources.length||!Array.isArray(peer.revisions)||!peer.revisions.length)throw Error('Invalid financial peer');
   seen.add(peer.ticker);
  }
 }
 return value;
}

export const industryLabels:Record<string,string>={revenue:'Revenue',gross_profit:'Gross profit',net_profit:'Profit after tax',profit_parent:'Parent-shareholder profit',total_assets:'Total assets',total_liabilities:'Total liabilities',equity:'Total equity',cash_operating:'Operating cash flow',cash_investing:'Investing cash flow',cash_financing:'Financing cash flow',free_cash_flow:'Free cash flow',operating_income:'Operating income',net_interest_income:'Net interest income',customer_loans:'Customer loans',customer_deposits:'Customer deposits',inventory:'Inventory',roe:'ROE',roa:'ROA',gross_margin:'Gross Margin',net_margin:'Net Margin',loan_deposit_ratio:'Accounting loans / deposits',pe:'P/E',pb:'P/B'};
