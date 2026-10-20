import type {FinancialPanel,FundamentalResearch} from './types.ts';

const specifications={balance_history:{chart:'performance',VND:['total_assets','total_liabilities','equity'],fraction:[],multiple:[]},assets:{chart:'stacked',VND:['cash_equivalents','inventory','customer_loans'],fraction:[],multiple:[]},funding:{chart:'stacked',VND:['total_liabilities','equity'],fraction:['liabilities_assets'],multiple:[]},growth:{chart:'performance',VND:['revenue','operating_income','net_profit'],fraction:['revenue_growth_yoy','operating_income_growth_yoy','net_profit_growth_yoy'],multiple:[]},quarterly:{chart:'performance',VND:['revenue','operating_income','net_profit'],fraction:['revenue_growth_yoy','operating_income_growth_yoy','net_profit_growth_yoy'],multiple:[]},pe:{chart:'unavailable',VND:[],fraction:[],multiple:['pe']},pb:{chart:'unavailable',VND:[],fraction:[],multiple:['pb']}} as const;
const publicStatuses=['QUALIFIED','UNQUALIFIED','UNAVAILABLE','DEMO'];

/** Validate server-qualified chart projections. Never calculate financial inputs. */
export function validateFinancialPanels(data:FundamentalResearch){
 const personal=data.display_scope==='personal_research'&&data.access_classification==='PERSONAL_RESEARCH';
 const statuses=[...publicStatuses,...(personal?['SOURCE_REPORTED']:[])];
 if(data.research_panels===undefined)return; // Older payloads get shells, never invented chart data.
 if(!Array.isArray(data.research_panels)||data.research_panels.length>(personal?7:6))throw Error('Invalid financial panels');
 const seen=new Set<string>(),periods=data.chart_rows?.map(r=>r.period)||[];
 for(const panel of data.research_panels){
  if(!panel||!Object.hasOwn(specifications,panel.key)||seen.has(panel.key))throw Error('Invalid financial panel ownership');
  if(panel.key==='balance_history'&&!personal)throw Error('Research panel is not public data');
  seen.add(panel.key);const spec=specifications[panel.key];
  if(panel.source!==data.source||panel.frequency!==data.period_type||panel.chart!==spec.chart||!statuses.includes(panel.status)||typeof panel.partial!=='boolean'||typeof panel.methodology!=='string'||!Array.isArray(panel.series)||panel.series.length>5||!Array.isArray(panel.rows)||panel.rows.length!==periods.length||!Array.isArray(panel.reasons)||panel.reasons.some(r=>typeof r!=='string'))throw Error('Invalid financial panel contract');
  const keys=new Set<string>();
  for(const s of panel.series){
   if(!s||typeof s.label!=='string'||!['VND','fraction','multiple'].includes(s.unit)||!(spec[s.unit] as readonly string[]).includes(s.key)||keys.has(s.key))throw Error('Invalid financial panel series');
   if(data.financial_identity_guard&&['revenue','revenue_growth_yoy','cash_equivalents','inventory'].includes(s.key)||data.profile!=='bank'&&s.key==='customer_loans'||data.profile!=='bank'&&s.key.startsWith('operating_income'))throw Error('Unsafe financial panel issuer');
   keys.add(s.key);
  }
  let available=false,blocked=false;
  for(const [i,row] of panel.rows.entries()){
   if(row.period!==periods[i]||!row.values||!row.statuses||!row.bases||Object.keys(row.values).length!==keys.size||Object.keys(row.values).some(k=>!keys.has(k)))throw Error('Invalid financial panel periods');
   for(const key of keys){
    const value=row.values[key],status=row.statuses[key];
    if(!statuses.includes(status)||value!==null&&(typeof value!=='number'||!Number.isFinite(value)))throw Error('Invalid financial panel point');
    if(['UNAVAILABLE','UNQUALIFIED'].includes(status)&&value!==null||status==='DEMO'&&!data.is_fixture||status==='QUALIFIED'&&(data.is_fixture||!['consolidated','standalone'].includes(row.bases[key]||'')))throw Error('Unsafe financial panel qualification');
    if(status==='SOURCE_REPORTED'&&(!personal||panel.chart==='stacked'||panel.series.find(s=>s.key===key)?.unit!=='VND'||value===null))throw Error('Unsafe personal research chart');
    if(value===null&&['QUALIFIED','DEMO'].includes(status))throw Error('Missing qualified financial point');
    if(value!==null&&value!==(data.chart_rows?.[i] as unknown as Record<string,unknown>)?.[key])throw Error('Financial panel differs from displayed observation');
    available ||= value!==null;blocked ||= status==='UNQUALIFIED';
   }
   const amounts=panel.series.filter(s=>s.unit==='VND').map(s=>s.key).filter(k=>row.values[k]!==null);
   if(panel.chart==='stacked'&&(amounts.some(k=>row.values[k]!<0)||new Set(amounts.map(k=>row.bases[k])).size>1))throw Error('Unsafe financial composition');
   if(panel.chart==='stacked'&&amounts.length&&panel.series.some(s=>s.unit==='fraction'&&row.values[s.key]!==null&&row.bases[s.key]!==row.bases[amounts[0]]))throw Error('Unsafe financial composition overlay');
   if(panel.key==='quarterly'&&data.period_type!=='quarterly'&&Object.values(row.values).some(v=>v!==null)||panel.chart==='unavailable'&&Object.values(row.values).some(v=>v!==null))throw Error('Unsupported financial panel values');
  }
  const expected=available?panel.rows.some(r=>Object.values(r.statuses).includes('SOURCE_REPORTED'))?'SOURCE_REPORTED':data.is_fixture?'DEMO':'QUALIFIED':blocked?'UNQUALIFIED':'UNAVAILABLE';
  const bases=new Set(panel.rows.flatMap(r=>Object.keys(r.values).filter(k=>r.values[k]!==null).map(k=>r.bases[k])));
  if(bases.size>1)throw Error('Incomparable financial chart bases');
  if(panel.status!==expected)throw Error('Invalid financial panel status');
 }
}

export const panelTitles={balance_history:'Reported balance history',assets:'Asset composition',funding:'Funding composition',growth:'Revenue and profit trends',quarterly:'Quarterly operating results',pe:'P/E history',pb:'P/B history'} as const;
export function financialSourceLink(value:string):string|undefined{
 try{const url=new URL(value);return url.protocol==='https:'&&!url.username&&!url.password?url.href:undefined;}catch{return undefined;}
}
export function selectFinancialPanel(data:FundamentalResearch,key:FinancialPanel['key'],periods:string[]):FinancialPanel|undefined{
 const panel=data.research_panels?.find(p=>p.key===key);
 if(!panel)return undefined;
 const rows=panel.rows.filter(r=>r.period>=(periods[0]||'')&&r.period<=(periods.at(-1)||''));
 const available=rows.some(r=>Object.values(r.values).some(v=>v!==null)),blocked=rows.some(r=>Object.values(r.statuses).includes('UNQUALIFIED'));
 return {...panel,rows,status:available?rows.some(r=>Object.values(r.statuses).includes('SOURCE_REPORTED'))?'SOURCE_REPORTED':data.is_fixture?'DEMO':'QUALIFIED':blocked?'UNQUALIFIED':'UNAVAILABLE'};
}
