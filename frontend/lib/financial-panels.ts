import type {FinancialPanel,FundamentalPeriod,FundamentalResearch} from './types.ts';

const specifications={bank_quality:{chart:'performance',VND:[],fraction:['demand_deposit_share','npl_classified_ratio','classified_loan_coverage'],multiple:[]},cashflow:{chart:'performance',VND:['cash_operating','cash_investing','cash_financing','free_cash_flow'],fraction:[],multiple:[]},profitability:{chart:'performance',VND:[],fraction:['roe','roa','gross_margin','net_margin'],multiple:[]},liquidity:{chart:'performance',VND:[],fraction:[],multiple:['current_ratio','quick_ratio','debt_equity']},bank_funding:{chart:'performance',VND:['customer_loans','customer_deposits'],fraction:['loan_deposit_ratio'],multiple:[]},bank_growth:{chart:'performance',VND:[],fraction:['customer_loans_growth_yoy','customer_deposits_growth_yoy','customer_loans_growth_qoq','customer_deposits_growth_qoq'],multiple:[]},balance_history:{chart:'performance',VND:['total_assets','total_liabilities','equity'],fraction:[],multiple:[]},assets:{chart:'stacked',VND:['cash_equivalents','inventory','customer_loans'],fraction:[],multiple:[]},funding:{chart:'stacked',VND:['total_liabilities','equity'],fraction:['liabilities_assets'],multiple:[]},growth:{chart:'performance',VND:['revenue','operating_income','net_profit'],fraction:['revenue_growth_yoy','operating_income_growth_yoy','net_profit_growth_yoy'],multiple:[]},quarterly:{chart:'performance',VND:['revenue','operating_income','net_profit'],fraction:['revenue_growth_yoy','operating_income_growth_yoy','net_profit_growth_yoy'],multiple:[]},pe:{chart:'unavailable',VND:[],fraction:[],multiple:['pe']},pb:{chart:'unavailable',VND:[],fraction:[],multiple:['pb']}} as const;
const publicStatuses=['QUALIFIED','UNQUALIFIED','UNAVAILABLE','DEMO'];

function privateBankGrowthInputs(data:FundamentalResearch,period:string,key:string,value:unknown){
 if(data.display_scope!=='personal_research'||data.access_classification!=='PERSONAL_RESEARCH'||data.is_fixture||data.profile!=='bank'||data.source!=='vnstock:VCI'||!['annual','quarterly'].includes(data.period_type)||!['customer_loans_growth_yoy','customer_deposits_growth_yoy','customer_loans_growth_qoq','customer_deposits_growth_qoq'].includes(key)||typeof value!=='number'||!Number.isFinite(value))return false;
 const field=key.startsWith('customer_loans')?'customer_loans':'customer_deposits';
 const code=field==='customer_loans'?'bsb104':'bsb113';
 const quarterly=period.includes('-Q');
 if((key.endsWith('_qoq')&&(!quarterly||data.period_type!=='quarterly'))||(key.endsWith('_yoy')&&((data.period_type==='annual')!==!quarterly)))return false;
 let prior='';
 if(!quarterly)prior=String(Number(period)-1);
 else{
  const match=/^(\d{4})-Q([1-4])$/.exec(period);if(!match)return false;
  const year=Number(match[1]),quarter=Number(match[2]);
  prior=key.endsWith('_yoy')?`${year-1}-Q${quarter}`:quarter===1?`${year-1}-Q4`:`${year}-Q${quarter-1}`;
 }
 const chartRow=data.chart_rows?.find(row=>row.period===period) as (FundamentalPeriod&{calculations?:Record<string,{formula:string;inputs:Record<string,unknown>[]}>})|undefined;
 const calculation=chartRow?.calculations?.[key],refs=calculation?.inputs;
 if(calculation?.reason||!Array.isArray(refs)||refs.length!==2)return false;
 const current=refs.find(ref=>ref.period===period),previous=refs.find(ref=>ref.period===prior);
 if(!current||!previous)return false;
 const valid=(ref:Record<string,unknown>)=>{
  const context=ref.source_context as Record<string,unknown>|undefined;
  const sourcePeriod=data.statements?.balance?.periods.find(item=>item.period===ref.period);
  const line=sourcePeriod?.items.find(item=>item.code===code);
  return ref.statement==='balance'&&ref.field===field&&ref.code===code&&ref.source==='vnstock:VCI'&&ref.currency==='VND'&&ref.basis==='point_in_time'&&typeof ref.value==='number'&&Number.isFinite(ref.value)&&ref.content_sha256===current.content_sha256&&context?.unit_evidence==='audited_vci_adapter_contract'&&context.amount_multiplier===1&&context.display_rights!=='prohibited'&&typeof context.record_sha256==='string'&&/^[a-f0-9]{64}$/.test(context.record_sha256)&&sourcePeriod?.basis==='point_in_time'&&line?.unit==='VND'&&line.semantic_status==='reported'&&line.value===ref.value&&line.raw_value===ref.value&&sourcePeriod.source==='vnstock:VCI'&&(sourcePeriod.source_context as Record<string,unknown>|undefined)?.record_sha256===context.record_sha256;
 };
 const evidence=data.verification?.periods.find(item=>item.period===period)?.metrics[key];
 return valid(current)&&valid(previous)&&current.consolidation===previous.consolidation&&(previous.value as number)>0&&Math.abs(value-((current.value as number)-(previous.value as number))/(previous.value as number))<1e-10&&evidence?.status==='PARTIALLY_VERIFIED'&&evidence.display_eligible&&evidence.public_display_eligible===false&&evidence.missing_evidence.length>0&&evidence.dimensions?.ACCOUNTING_VERIFIED===false;
}

/** Validate server-qualified chart projections. Never calculate financial inputs. */
export function validateFinancialPanels(data:FundamentalResearch){
 const personal=data.display_scope==='personal_research'&&data.access_classification==='PERSONAL_RESEARCH';
 const statuses=[...publicStatuses,...(personal?['SOURCE_REPORTED','PARTIALLY_VERIFIED']:[])];
 if(data.research_panels===undefined)return; // Older payloads get shells, never invented chart data.
 if(!Array.isArray(data.research_panels)||data.research_panels.length>(personal?96:12))throw Error('Invalid financial panels');
 const seen=new Set<string>(),periods=data.chart_rows?.map(r=>r.period)||[];
 for(const panel of data.research_panels){
  const hierarchyPanel=typeof panel?.key==='string'&&/^components:(income|balance|cash):[a-z0-9_]+$/i.test(panel.key);
  const rootLines=hierarchyPanel&&panel.component_scope==='unparented_lines';
  const componentStatement=hierarchyPanel?panel.statement as 'income'|'balance'|'cash':undefined;
  const componentData=componentStatement?data.statements?.[componentStatement]:undefined;
  const componentPrefixes=componentStatement?{income:['isa','isb','iss'],balance:['bsa','bsb','bss','bsi'],cash:['cfa','cfb','cfs']}[componentStatement]:undefined;
  if(!panel||(!Object.hasOwn(specifications,panel.key)&&!hierarchyPanel)||seen.has(panel.key))throw Error('Invalid financial panel ownership');
  if(hierarchyPanel){
   if(!personal||data.source!=='vnstock:VCI'||!['income','balance','cash'].includes(panel.statement||''))throw Error('Invalid personal hierarchy panel');
   if(rootLines?(panel.key!==`components:${panel.statement}:root`||panel.component_scope!=='unparented_lines'||panel.parent_code!==undefined):
      (panel.component_scope!=='reported_parent'||panel.key!==`components:${panel.statement}:${panel.parent_code?.toLowerCase()}`||!panel.parent_code||!panel.parent_code.trim()))throw Error('Invalid component scope');
   if(!componentData||!['stacked','performance'].includes(panel.chart)||panel.chart==='stacked'&&panel.statement!=='balance')throw Error('Invalid component statement');
   if(!rootLines&&!componentPrefixes!.some(prefix=>panel.parent_code!.toLowerCase().startsWith(prefix)))throw Error('Invalid component parent');
  }
  if(panel.key==='balance_history'&&!personal)throw Error('Research panel is not public data');
  seen.add(panel.key);const spec=hierarchyPanel?undefined:specifications[panel.key as keyof typeof specifications];
  if(panel.source!==data.source||panel.frequency!==data.period_type||(!hierarchyPanel&&panel.chart!==spec!.chart)||!statuses.includes(panel.status)||typeof panel.partial!=='boolean'||typeof panel.methodology!=='string'||!Array.isArray(panel.series)||panel.series.length>(hierarchyPanel?40:5)||!Array.isArray(panel.rows)||panel.rows.length!==periods.length||!Array.isArray(panel.reasons)||panel.reasons.some(r=>typeof r!=='string'))throw Error('Invalid financial panel contract');
  const keys=new Set<string>();
  for(const s of panel.series){
   if(!s||typeof s.label!=='string'||!['VND','fraction','multiple'].includes(s.unit)||(hierarchyPanel?(s.unit!=='VND'||!s.key||keys.has(s.key)||!componentPrefixes!.some(prefix=>s.key.toLowerCase().startsWith(prefix))):(!(spec![s.unit] as readonly string[]).includes(s.key)||keys.has(s.key))))throw Error('Invalid financial panel series');
   if(data.financial_identity_guard&&['revenue','revenue_growth_yoy','cash_equivalents','inventory'].includes(s.key)||data.profile!=='bank'&&['customer_loans','customer_deposits','loan_deposit_ratio'].includes(s.key)||data.profile!=='bank'&&s.key.startsWith('operating_income'))throw Error('Unsafe financial panel issuer');
   keys.add(s.key);
  }
  let available=false,blocked=false;
  for(const [i,row] of panel.rows.entries()){
   if(row.period!==periods[i]||!row.values||!row.statuses||!row.bases||Object.keys(row.values).length!==keys.size||Object.keys(row.values).some(k=>!keys.has(k)))throw Error('Invalid financial panel periods');
   if(hierarchyPanel){
    const sourcePeriod=componentData!.periods.find(item=>item.period===row.period);
    if(!sourcePeriod){
     if(row.statement_basis!=='unavailable'||Object.values(row.values).some(value=>value!==null)||Object.values(row.statuses).some(value=>value!=='UNAVAILABLE'))throw Error('Invalid missing component period');
    }else if(rootLines){
     if(sourcePeriod.basis!==row.statement_basis)throw Error('Invalid root-line reporting basis');
     for(const key of keys){
      const line=sourcePeriod.items.find(item=>item.code===key),value=row.values[key];
      const direct=!!line&&line.parent===null&&line.unit==='VND'&&line.semantic_status==='reported'&&line.value!==null;
      if(direct?(panel.status==='UNQUALIFIED'?(row.statuses[key]!=='UNQUALIFIED'||value!==null):(row.statuses[key]!=='SOURCE_REPORTED'||value!==line!.value)):(row.statuses[key]!=='UNAVAILABLE'||value!==null))throw Error('Root-line value differs from source line');
     }
    }else{
     const parent=sourcePeriod.items.find(item=>item.code.toLowerCase()===panel.parent_code!.toLowerCase());
     if(sourcePeriod.basis!==row.statement_basis||!parent||parent.unit!=='VND'||parent.semantic_status!=='reported')throw Error('Invalid component parent evidence');
     for(const key of keys){
      const line=sourcePeriod.items.find(item=>item.code===key),value=row.values[key];
      const direct=!!line&&line.parent?.toLowerCase()===panel.parent_code!.toLowerCase()&&line.unit==='VND'&&line.semantic_status==='reported'&&line.value!==null;
      if(direct?(panel.status==='UNQUALIFIED'?(row.statuses[key]!=='UNQUALIFIED'||value!==null):(row.statuses[key]!=='SOURCE_REPORTED'||value!==line!.value)):(row.statuses[key]!=='UNAVAILABLE'||value!==null))throw Error('Component value differs from source line');
     }
    }
   }
   for(const key of keys){
    const value=row.values[key],status=row.statuses[key];
    if(!statuses.includes(status)||value!==null&&(typeof value!=='number'||!Number.isFinite(value)))throw Error('Invalid financial panel point');
    if(['UNAVAILABLE','UNQUALIFIED'].includes(status)&&value!==null||status==='DEMO'&&!data.is_fixture||status==='QUALIFIED'&&(data.is_fixture||!['consolidated','standalone'].includes(row.bases[key]||'')))throw Error('Unsafe financial panel qualification');
    if(status==='PARTIALLY_VERIFIED'&&(panel.status!=='PARTIALLY_VERIFIED'||panel.key!=='bank_growth'||panel.series.find(s=>s.key===key)?.unit!=='fraction'||!privateBankGrowthInputs(data,row.period,key,value)))throw Error('Unsafe partially verified bank metric');
    if(status==='SOURCE_REPORTED'&&(!personal||panel.chart==='stacked'&&!hierarchyPanel||panel.series.find(s=>s.key===key)?.unit!=='VND'||value===null))throw Error('Unsafe personal research chart');
    if(value===null&&['QUALIFIED','DEMO'].includes(status))throw Error('Missing qualified financial point');
   if(!hierarchyPanel&&value!==null&&value!==(data.chart_rows?.[i] as unknown as Record<string,unknown>)?.[key])throw Error('Financial panel differs from displayed observation');
    available ||= value!==null;blocked ||= status==='UNQUALIFIED';
   }
   const amounts=panel.series.filter(s=>s.unit==='VND').map(s=>s.key).filter(k=>row.values[k]!==null);
   if(panel.chart==='stacked'&&(amounts.some(k=>row.values[k]!<0)||new Set(amounts.map(k=>row.bases[k])).size>1))throw Error('Unsafe financial composition');
   if(panel.chart==='stacked'&&amounts.length&&panel.series.some(s=>s.unit==='fraction'&&row.values[s.key]!==null&&row.bases[s.key]!==row.bases[amounts[0]]))throw Error('Unsafe financial composition overlay');
   if(panel.key==='quarterly'&&data.period_type!=='quarterly'&&Object.values(row.values).some(v=>v!==null)||panel.chart==='unavailable'&&Object.values(row.values).some(v=>v!==null))throw Error('Unsupported financial panel values');
  }
  const partialPersonalBankGrowth=personal&&!data.is_fixture&&data.profile==='bank'&&data.source==='vnstock:VCI'&&panel.key==='bank_growth'&&panel.rows.some(r=>Object.values(r.statuses).includes('PARTIALLY_VERIFIED'));
  const expected=available?partialPersonalBankGrowth?'PARTIALLY_VERIFIED':panel.rows.some(r=>Object.values(r.statuses).includes('SOURCE_REPORTED'))?'SOURCE_REPORTED':data.is_fixture?'DEMO':'QUALIFIED':blocked?'UNQUALIFIED':'UNAVAILABLE';
  const bases=new Set(panel.rows.flatMap(r=>Object.keys(r.values).filter(k=>r.values[k]!==null).map(k=>r.bases[k])));
  if(bases.size>1)throw Error('Incomparable financial chart bases');
  if(panel.status!==expected)throw Error('Invalid financial panel status');
 }
}

export const panelTitles:Record<string,string>={bank_quality:'Bank deposit and credit quality',bank_growth:'Bank credit and deposit growth',cashflow:'Cash flow and reinvestment',profitability:'Profitability history',liquidity:'Liquidity and leverage',bank_funding:'Bank lending and deposits',balance_history:'Reported balance history',assets:'Asset composition',funding:'Funding composition',growth:'Revenue and profit trends',quarterly:'Quarterly operating results',pe:'P/E history',pb:'P/B history'};
export function financialSourceLink(value:string):string|undefined{
 try{const url=new URL(value);return url.protocol==='https:'&&!url.username&&!url.password?url.href:undefined;}catch{return undefined;}
}
export function selectFinancialPanel(data:FundamentalResearch,key:FinancialPanel['key'],periods:string[]):FinancialPanel|undefined{
 const panel=data.research_panels?.find(p=>p.key===key);
 if(!panel)return undefined;
 if(panel.statement)panelTitles[key]=panel.title;
 const rows=panel.rows.filter(r=>r.period>=(periods[0]||'')&&r.period<=(periods.at(-1)||''));
 const available=rows.some(r=>Object.values(r.values).some(v=>v!==null)),blocked=rows.some(r=>Object.values(r.statuses).includes('UNQUALIFIED'));
 const partial=panel.key==='bank_growth'&&data.display_scope==='personal_research'&&rows.some(r=>Object.values(r.statuses).includes('PARTIALLY_VERIFIED'));
 return {...panel,rows,status:available?partial?'PARTIALLY_VERIFIED':rows.some(r=>Object.values(r.statuses).includes('SOURCE_REPORTED'))?'SOURCE_REPORTED':data.is_fixture?'DEMO':'QUALIFIED':blocked?'UNQUALIFIED':'UNAVAILABLE'};
}
