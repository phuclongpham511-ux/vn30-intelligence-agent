"use client";
import {useEffect,useState} from 'react';
import {useLocale} from '@/lib/i18n';
import type {FundamentalResearch,FundamentalPeriod} from '@/lib/types';
import {FINANCIAL_LABELS,type FinancialKey} from '@/lib/fundamental-data';
import {financialResearchData,amountFields,growthFields,ratioFields,researchSections,unitDivisor,unitLabels,type AmountUnit,type ResearchSection} from '@/lib/fundamental-research';
import {direction} from '@/lib/presentation';
import {stockRead} from '@/lib/stock-detail';
import FinancialResearchChart from './FinancialResearchCharts';
import {Button} from '../ui/button';
import {Skeleton} from '../ui/skeleton';

const sectionLabels={overview:'Financial overview',performance:'Business performance',statements:'Financial statements',ratios:'Financial ratios'} as const;
const statementLabels={income:'Income statement',balance:'Balance sheet',cash:'Cash flow statement'} as const;

function FinancialTable({rows,fields,unit,label}:{rows:FundamentalPeriod[];fields:readonly FinancialKey[];unit:AmountUnit;label:string}){
  const {ui,t,number,percent}=useLocale();
  return <div className="fundamental-table-scroll" role="region" aria-label={ui(label)} tabIndex={0}><table className="fundamental-table text-xs">
    <caption className="sr-only">{ui(label)} · {ui(unitLabels[unit])} · {t('Dash means unavailable; missing is not zero.')}</caption>
    <thead><tr><th scope="col">{t('Metric')}</th>{rows.map(row=><th scope="col" key={row.period}>{row.period}</th>)}</tr></thead>
    <tbody>{fields.map(key=><tr key={key}><th scope="row">{ui(FINANCIAL_LABELS[key])}</th>{rows.map(row=><td key={row.period}>{amountFields.includes(key as typeof amountFields[number])?row[key]==null?'—':number(row[key]!/unitDivisor[unit],unit==='vnd'?0:2):percent(row[key],key.includes('growth'))}</td>)}</tr>)}</tbody>
  </table></div>;
}

function ChangeSummary({data,unit}:{data:FundamentalResearch;unit:AmountUnit}){
  const {t,ui,number,percent}=useLocale();
  const amount=(value:number|null,signed=false)=>value===null?'—':(signed&&value>0?'+':'')+number(value/unitDivisor[unit],unit==='vnd'?0:2);
  return <section className="border-t pt-4" aria-label={t('What changed?')}><h3 className="text-sm font-semibold">{t('What changed?')}</h3><p className="mt-1 text-xs text-muted-foreground">{t('Exact prior-year comparison. Numerical changes do not explain causes.')}</p>
    {!data.changes.length?<p className="stock-note">{t('Comparable prior-year data is unavailable.')}</p>:<div className="fundamental-table-scroll mt-3" role="region" tabIndex={0} aria-label={t('Annual changes')}><table className="fundamental-table text-xs"><caption className="sr-only">{t('Annual changes')} · {ui(unitLabels[unit])}</caption><thead><tr><th scope="col">{t('Metric')}</th><th scope="col">{data.changes[0].current_period}</th><th scope="col">{data.changes[0].prior_period}</th><th scope="col">{t('Absolute change')}</th><th scope="col">{t('YoY')}</th></tr></thead><tbody>{data.changes.map(change=><tr key={change.metric}><th scope="row">{ui(FINANCIAL_LABELS[change.metric])}</th><td>{amount(change.current)}</td><td>{amount(change.previous)}</td><td className={direction(change.absolute_change)}>{amount(change.absolute_change,true)}</td><td className={direction(change.growth_yoy)}>{percent(change.growth_yoy,true)}</td></tr>)}</tbody></table></div>}
    <p className="mt-2 text-[11px] text-muted-foreground">{t('Growth requires a positive comparable base. Missing, zero or negative bases remain unavailable.')}</p>
  </section>;
}

export default function FundamentalTrends({ticker,visible=true}:{ticker:string;visible?:boolean}){
  const [data,setData]=useState<FundamentalResearch|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState(false),[attempt,setAttempt]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();let disposed=false;const timeout=setTimeout(()=>controller.abort(),20000);
    setLoading(true);setError(false);setData(null);
    stockRead<FundamentalResearch>(`/api/stocks/${encodeURIComponent(ticker)}/fundamentals/research?limit=8`,controller.signal)
      .then(value=>{const result=financialResearchData(value,ticker);if(!disposed)setData(result);})
      .catch(()=>{if(!disposed)setError(true);}).finally(()=>{clearTimeout(timeout);if(!disposed)setLoading(false);});
    return()=>{disposed=true;clearTimeout(timeout);controller.abort();};
  },[ticker,attempt]);
  return <FundamentalTrendsView data={data} loading={loading} error={error} retry={()=>setAttempt(value=>value+1)} visible={visible}/>;
}

export function FundamentalTrendsView({data,loading,error,retry,visible=true}:{data:FundamentalResearch|null;loading:boolean;error:boolean;retry:()=>void;visible?:boolean}){
  const {t,ui,number,percent,date}=useLocale();
  const [section,setSection]=useState<ResearchSection>('overview'),[unit,setUnit]=useState<AmountUnit>('billions'),[count,setCount]=useState(0),[statement,setStatement]=useState<keyof typeof statementLabels>('income');
  const rows=count?data?.rows.slice(-count)||[]:data?.rows||[];
  const latest=rows.at(-1);
  const supportedAmounts=data?.financial_identity_guard?['net_profit'] as const:amountFields;
  const supportedRatios=data?.financial_identity_guard?['roe'] as const:ratioFields;
  const supportedGrowth=data?.financial_identity_guard?['net_profit_growth_yoy'] as const:growthFields;
  return <section className="min-w-0 space-y-5" aria-labelledby="fundamental-trends-title" hidden={!visible}>
    <header className="flex flex-wrap items-start justify-between gap-3"><div><p className="eyebrow mb-1">{t('Company performance')}</p><h2 id="fundamental-trends-title" className="text-xl">{t('Fundamental analysis')}</h2><p className="mt-1 text-xs text-muted-foreground">{t('Annual reported financials')}{latest?' · '+latest.period+' · '+data!.source:''}</p></div>
      <div className="flex flex-wrap items-center gap-2 text-xs"><div className="inline-flex rounded-md border p-0.5" role="group" aria-label={t('Reporting frequency')}><button type="button" aria-pressed="true" className="rounded bg-primary/10 px-3 py-1.5 text-primary">{t('Annual')}</button><button type="button" disabled title={t('Quarterly data is not supplied by the current adapter.')} className="px-3 py-1.5 text-muted-foreground opacity-50">{t('Quarterly')}</button></div>
        <label className="sr-only" htmlFor="financial-units">{t('Amount units')}</label><select id="financial-units" value={unit} onChange={e=>setUnit(e.target.value as AmountUnit)} className="rounded border bg-background px-2 py-2">{Object.entries(unitLabels).map(([key,label])=><option key={key} value={key}>{ui(label)}</option>)}</select>
        <label className="sr-only" htmlFor="financial-periods">{t('Historical periods')}</label><select id="financial-periods" value={count} onChange={e=>setCount(Number(e.target.value))} className="rounded border bg-background px-2 py-2"><option value={0}>{t('All loaded periods')}</option>{[2,4].map(n=><option key={n} value={n} disabled={!data||data.rows.length<n}>{t('{count} annual periods',{count:n})}</option>)}</select>
      </div>
    </header>
    <nav aria-label={t('Financial research sections')} className="flex gap-1 overflow-x-auto border-b pb-2">{researchSections.map(key=><button key={key} type="button" aria-pressed={section===key} onClick={()=>setSection(key)} className={`shrink-0 rounded-md px-3 py-2 text-xs focus-visible:outline-2 focus-visible:outline-ring ${section===key?'bg-primary/10 font-medium text-primary':'text-muted-foreground hover:bg-muted'}`}>{t(sectionLabels[key])}</button>)}</nav>
    {loading?<div role="status" aria-label={t('Loading annual financial history')} className="space-y-4"><Skeleton className="h-24"/><Skeleton className="h-64"/></div>:error?<div role="alert" className="border-y py-8 text-center"><p className="mb-3 text-sm">{t('Annual financial history is temporarily unavailable.')}</p><Button variant="outline" onClick={retry}>{t('Retry financials')}</Button></div>:!data||!data.rows.length?<p className="py-8 text-sm text-muted-foreground">{t('No annual financial observations are available from the current provider.')}</p>:<>
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 text-[11px] leading-5 text-muted-foreground"><p>{t('Quarterly data is not supplied by the current adapter.')}</p><span>{rows[0]?.period}–{latest?.period} · {ui(unitLabels[unit])}</span></div>
      {data.financial_identity_guard&&<p className="rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs leading-5">{t('Financial issuer coverage is limited. Generic revenue and margins are withheld; banking metrics are not supplied.')}</p>}
      {section==='overview'&&<>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-4 border-y py-4 sm:grid-cols-3 xl:grid-cols-5">{[...supportedAmounts,...supportedRatios].map(key=><div key={key}><dt className="text-xs text-muted-foreground">{ui(FINANCIAL_LABELS[key])}</dt><dd className="financial mt-2 break-words text-lg font-semibold">{amountFields.includes(key as typeof amountFields[number])?latest?.[key]==null?'—':number(latest[key]!/unitDivisor[unit],unit==='vnd'?0:2):percent(latest?.[key])}</dd></div>)}</dl>
        <ChangeSummary data={data} unit={unit}/>
        <div className="grid min-w-0 gap-6 xl:grid-cols-2"><FinancialResearchChart visible={visible} rows={rows} fields={supportedAmounts} title="Revenue and profit trends" unit={unit}/><FinancialResearchChart visible={visible} rows={rows} fields={supportedGrowth} title="Year-over-year growth" percentage unit={unit}/></div>
      </>}
      {section==='performance'&&<><div className="grid min-w-0 gap-6 xl:grid-cols-2"><FinancialResearchChart visible={visible} rows={rows} fields={supportedAmounts} title="Revenue and profit trends" unit={unit}/><FinancialResearchChart visible={visible} rows={rows} fields={supportedGrowth} title="Year-over-year growth" percentage unit={unit}/></div><FinancialTable rows={rows} fields={[...supportedAmounts,...supportedGrowth]} unit={unit} label="Business performance"/></>}
      {section==='statements'&&<section aria-label={t('Financial statements')}><div className="mb-4 flex flex-wrap gap-2" role="group" aria-label={t('Statement type')}>{Object.entries(statementLabels).map(([key,label])=><Button key={key} size="sm" variant={statement===key?'secondary':'outline'} aria-pressed={statement===key} onClick={()=>setStatement(key as keyof typeof statementLabels)}>{t(label)}</Button>)}</div>
        {statement==='income'?<><p className="mb-4 text-xs leading-5 text-muted-foreground">{t('Source-limited income summary. This is not a complete financial statement.')}</p><FinancialTable rows={rows} fields={supportedAmounts} unit={unit} label="Income statement"/></>:<div className="border-y py-10 text-center"><h3 className="text-sm font-semibold">{t(statementLabels[statement])}</h3><p className="mt-2 text-xs text-muted-foreground">{t('This statement is not supplied by the current financial data path.')}</p></div>}
      </section>}
      {section==='ratios'&&<><FinancialResearchChart visible={visible} rows={rows} fields={supportedRatios} title="Profitability" percentage unit={unit}/><FinancialTable rows={rows} fields={[...supportedRatios,...supportedGrowth]} unit={unit} label="Financial ratios"/><div className="grid gap-5 border-t pt-5 sm:grid-cols-3">{['Financial position / leverage','Liquidity','Valuation'].map(label=><div key={label}><h3 className="text-xs font-semibold">{ui(label)}</h3><p className="mt-2 text-xs leading-5 text-muted-foreground">{t('Required verified inputs are unavailable. No ratio is estimated.')}</p></div>)}</div></>}
      <details className="border-t pt-3 text-xs text-muted-foreground"><summary className="cursor-pointer font-medium">{t('Financial source and coverage')}</summary><dl className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-2"><div><dt>{t('Source')}</dt><dd className="mt-1 text-foreground">{data.source}</dd></div><div><dt>{t('Read at')}</dt><dd className="mt-1 text-foreground">{date(data.read_at,true)} · {t('Provider or process cache; not a publication timestamp.')}</dd></div><div><dt>{t('Report basis')}</dt><dd className="mt-1">{t('Consolidated / standalone status is not supplied.')}</dd></div><div><dt>{t('Publication date')}</dt><dd className="mt-1">{t('Unavailable')}</dd></div><div><dt>{t('Sector')}</dt><dd className="mt-1">{data.sector||data.industry||t('Sector classification is unavailable.')}</dd></div><div><dt>{t('Unavailable indicators')}</dt><dd className="mt-1">{t('Parent-shareholder profit, equity, ROA, EPS, P/E and P/B are not supplied. ROE may also be unavailable.')}</dd></div></dl><p className="mt-3 leading-5">{t('Only reported observations are plotted. Missing values are not zero.')}{' '}{t('TTM and quarterly or YTD estimates are not calculated.')}</p></details>
    </>}
  </section>;
}
