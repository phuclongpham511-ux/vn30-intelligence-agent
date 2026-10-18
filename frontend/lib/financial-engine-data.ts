import type {FundamentalResearch,FinancialFrequency} from './types.ts';
import {FINANCIAL_LABELS,type FinancialKey} from './fundamental-data.ts';

/** Validate presentation ownership; all financial calculations remain in Python. */
export function financialEngineData(data:FundamentalResearch,ticker:string,frequency:FinancialFrequency,requireSummary=false):FundamentalResearch{
  const pattern=frequency==='annual'?/^\d{4}$/:/^\d{4}-Q[1-4]$/;
  if(!data||data.data_engine!=='financial-engine-v1'||data.ticker!==ticker||data.currency!=='VND'||data.period_type!==frequency||!data.source||!Array.isArray(data.rows)||data.rows.length>20||!Array.isArray(data.chart_rows)||data.chart_rows.length>1204||!data.statements||!Array.isArray(data.source_receipts)||typeof data.is_fixture!=='boolean')throw new Error('Invalid financial engine contract');
  const seen=new Set<string>();
  if(typeof data.financial_identity_guard!=='boolean'||!['non_financial','bank','financial_other','unknown'].includes(data.profile||'')||data.financial_identity_guard!==(data.profile!=='non_financial'))throw new Error('Invalid issuer profile');
  for(const row of data.rows){
    if(row.ticker!==ticker||row.source!==data.source||row.currency!=='VND'||row.frequency!==frequency||!pattern.test(row.period)||seen.has(row.period))throw new Error('Invalid financial period ownership');
    seen.add(row.period);
    if(row.is_fixture!==data.is_fixture)throw new Error('Invalid fixture ownership');
    for(const field of Object.keys(FINANCIAL_LABELS) as FinancialKey[])if(row[field]!==null&&(typeof row[field]!=='number'||!Number.isFinite(row[field])))throw new Error('Invalid financial engine value');
    if(data.financial_identity_guard&&(row.revenue!==null||row.gross_margin!==null||row.net_margin!==null||row.revenue_growth_yoy!==null))throw new Error('Unsafe financial issuer fields');
  }
  if(data.rows.some((row,index)=>index>0&&row.period<=data.rows[index-1].period))throw new Error('Unordered financial observations');
  const chartSeen=new Set<string>();
  for(const row of data.chart_rows){
    if(!pattern.test(row.period)||chartSeen.has(row.period))throw new Error('Invalid chart periods');chartSeen.add(row.period);
    const original=data.rows.find(item=>item.period===row.period);
    for(const key of Object.keys(FINANCIAL_LABELS) as FinancialKey[])if(row[key]!== (original?.[key]??null))throw new Error('Chart does not match financial observations');
  }
  if(data.rows.some(row=>!chartSeen.has(row.period)))throw new Error('Chart omits financial observations');
  for(const statement of Object.values(data.statements))for(const row of statement.periods){
    if(row.ticker!==ticker||row.source!==data.source||row.currency!=='VND'||!pattern.test(row.period)||!seen.has(row.period))throw new Error('Invalid statement ownership');
    for(const line of row.items){
      if(!line.code||!['VND','VND/share','source_units'].includes(line.unit)||!['reported','conflicted','unqualified'].includes(line.semantic_status))throw new Error('Invalid financial line');
      for(const value of [line.value,line.raw_value])if(value!==null&&(typeof value!=='number'||!Number.isFinite(value)))throw new Error('Invalid source amount');
      if(line.semantic_status!=='reported'&&line.value!==null)throw new Error('Unsafe source conflict');
    }
  }
  if(!Array.isArray(data.changes))throw new Error('Invalid financial comparisons');
  const compared=new Set<string>();
  for(const change of data.changes){
    if(!['revenue','net_profit','operating_income'].includes(change.metric)||change.current_period!==data.rows.at(-1)?.period||!pattern.test(change.prior_period)||Number(change.prior_period.slice(0,4))!==Number(change.current_period.slice(0,4))-1||change.prior_period.slice(4)!==change.current_period.slice(4))throw new Error('Invalid comparable financial periods');
    for(const value of [change.current,change.previous,change.absolute_change,change.growth_yoy])if(value!==null&&(typeof value!=='number'||!Number.isFinite(value)))throw new Error('Invalid financial comparison value');
    if(change.current!==data.rows.at(-1)?.[change.metric])throw new Error('Comparison does not match observation');
    const prior=data.rows.find(row=>row.period===change.prior_period);
    if(prior&&change.previous!==null&&change.previous!==prior[change.metric]||compared.has(change.metric))throw new Error('Invalid comparison ownership');
    if((change.previous===null||change.current===null)&&(change.absolute_change!==null||change.growth_yoy!==null))throw new Error('Missing comparison cannot produce changes');
    compared.add(change.metric);
  }
  const summary=data.fundamental_summary;
  if(requireSummary&&!summary)throw new Error('Financial display qualification unavailable');
  if(summary){
    if(summary.contract!=='fundamental-display-v1'||summary.period!==(data.rows.at(-1)?.period??null)||summary.frequency!==frequency||!Array.isArray(summary.metrics)||summary.metrics.length>32)throw new Error('Invalid financial summary ownership');
    const keys=new Set<string>();
    for(const metric of summary.metrics){
      if(!metric.key||keys.has(metric.key)||!['valuation','performance','profitability','health'].includes(metric.group)||!['VND','VND/share','fraction','multiple'].includes(metric.unit)||!['QUALIFIED','UNAVAILABLE','UNQUALIFIED','DEMO'].includes(metric.status))throw new Error('Invalid financial metric qualification');
      keys.add(metric.key);
      const supported=metric.key in FINANCIAL_LABELS||['market_cap','pe','pb','bvps'].includes(metric.key);
      const expectedUnit=['eps_reported','bvps'].includes(metric.key)?'VND/share':['debt_equity','current_ratio','quick_ratio','cash_conversion','pe','pb'].includes(metric.key)?'multiple':['roe','roa','gross_margin','net_margin','liabilities_assets'].includes(metric.key)||metric.key.includes('growth')?'fraction':'VND';
      if(!supported||metric.unit!==expectedUnit)throw new Error('Invalid financial metric unit');
      if(metric.value!==null&&(typeof metric.value!=='number'||!Number.isFinite(metric.value)))throw new Error('Invalid financial summary value');
      if(['UNQUALIFIED','UNAVAILABLE'].includes(metric.status)&&metric.value!==null||metric.status==='QUALIFIED'&&(data.is_fixture||!['consolidated','standalone'].includes(summary.consolidation||''))||metric.status==='DEMO'&&!data.is_fixture)throw new Error('Unsafe financial qualification');
      if(metric.key in FINANCIAL_LABELS&&metric.value!==(data.rows.at(-1)?.[metric.key as FinancialKey]??null))throw new Error('Financial summary does not match displayed facts');
      if(['market_cap','pe','pb','bvps'].includes(metric.key)&&metric.value!==null)throw new Error('Unsupported valuation inputs');
    }
  }
  return data;
}
