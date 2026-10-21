import type {FundamentalResearch,FundamentalPeriod} from './types.ts';
import {FINANCIAL_LABELS,type FinancialKey,annualChartData} from './fundamental-data.ts';

export const amountFields=['revenue','net_profit'] as const;
export const growthFields=['revenue_growth_yoy','net_profit_growth_yoy'] as const;
export const ratioFields=['gross_margin','net_margin','roe'] as const;
export const engineAmounts=['revenue','net_profit','operating_income','profit_parent','total_assets','equity','total_liabilities','cash_operating','cash_investing','cash_financing','free_cash_flow','customer_demand_deposits','classified_loans','classified_nonperforming_loans','classified_loan_allowance'] as const;
export const multipleFields=['debt_equity','current_ratio','quick_ratio','cash_conversion'] as const;
export const researchSections=['overview','performance','balance','cashflow','profitability','health','valuation','statements','sources'] as const;
export type ResearchSection=typeof researchSections[number];
export type AmountUnit='billions'|'millions'|'vnd';
export const unitDivisor={billions:1e9,millions:1e6,vnd:1} as const;
export const unitLabels={billions:'VND bn',millions:'VND mn',vnd:'VND'} as const;
// Consolidation is distinct from the source's standalone-quarter flow basis.
export function consolidationLabel(value:string|null|undefined) {
  return value==='consolidated'?'Consolidated statements':value==='standalone'?'Separate statements':'Consolidated / standalone status is not supplied.';
}

export function financialResearchData(data:FundamentalResearch,ticker:string):FundamentalResearch {
  if(!data||data.ticker!==ticker||data.currency!=='VND'||data.period_type!=='annual'||typeof data.source!=='string'||!data.source||typeof data.financial_identity_guard!=='boolean'||!Array.isArray(data.rows)||data.rows.length>20||!Array.isArray(data.changes))throw new Error('Invalid financial ownership or contract');
  const periods=new Set<string>();
  for(const row of data.rows){
    if(row.ticker!==ticker||row.source!==data.source||row.currency!=='VND'||!/^\d{4}$/.test(row.period)||periods.has(row.period))throw new Error('Invalid reporting period or ownership');
    periods.add(row.period);
    for(const key of [...amountFields,...growthFields,...ratioFields])if(row[key]!==null&&(typeof row[key]!=='number'||!Number.isFinite(row[key])))throw new Error('Invalid financial value');
    if(data.financial_identity_guard&&(row.revenue!==null||row.gross_margin!==null||row.net_margin!==null||row.revenue_growth_yoy!==null))throw new Error('Unsafe financial issuer fields');
  }
  const compared=new Set<string>();
  const latest=annualChartData(data.rows).at(-1)?.period;
  for(const change of data.changes){
    if(!(['revenue','net_profit'] as string[]).includes(change.metric)||compared.has(change.metric)||change.current_period!==latest||!/^\d{4}$/.test(change.prior_period)||Number(change.prior_period)!==Number(change.current_period)-1)throw new Error('Invalid comparison period');
    compared.add(change.metric);
    for(const field of ['current','previous','absolute_change','growth_yoy'] as const)if(change[field]!==null&&(typeof change[field]!=='number'||!Number.isFinite(change[field])))throw new Error('Invalid financial comparison');
    if(change.current!==data.rows.find(row=>row.period===change.current_period)?.[change.metric])throw new Error('Comparison does not match reported value');
    const previous=data.rows.find(row=>row.period===change.prior_period);
    if(previous&&change.previous!==previous[change.metric])throw new Error('Comparison does not match prior reported value');
  }
  return {...data,rows:annualChartData(data.rows)};
}

// View projection only: null placeholders prevent a line crossing an absent year.
export function financialChartRows(rows:FundamentalPeriod[]):Partial<FundamentalPeriod>[] {
  if(!rows.length)return [];
  const indexed=new Map(rows.map(row=>[row.period,row]));
  const result:Partial<FundamentalPeriod>[]=[];
  for(let year=Number(rows[0].period);year<=Number(rows.at(-1)!.period);year++){
    result.push(indexed.get(String(year))??{period:String(year),...Object.fromEntries(Object.keys(FINANCIAL_LABELS).map(key=>[key,null]))});
  }
  return result;
}

/** Metric-level navigation: absence in one group does not hide another group. */
export function availableFinancialSections(data:FundamentalResearch|null,rows:FundamentalPeriod[]):ResearchSection[]{
 if(!data||!rows.length)return [...researchSections].filter(k=>k!=='valuation');
 const any=(keys:string[])=>rows.some(r=>keys.some(k=>typeof (r as unknown as Record<string,unknown>)[k]==='number'));
 const groups:Partial<Record<ResearchSection,boolean>>={performance:any(['revenue','operating_income','net_profit']),balance:any(['total_assets','total_liabilities','equity']),cashflow:any(['cash_operating','cash_investing','cash_financing']),profitability:any(['roe','roa','gross_margin','net_margin']),health:any(data.profile==='bank'?['customer_loans','customer_deposits','demand_deposit_share','npl_classified_ratio']:['current_ratio','quick_ratio','debt_equity']),valuation:!!data.fundamental_summary?.metrics.some(m=>m.group==='valuation'&&m.value!==null)};
 return researchSections.filter(k=>groups[k]!==false);
}
