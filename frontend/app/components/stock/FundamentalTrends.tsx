"use client";
import {useEffect,useState} from 'react';
import {useLocale} from '@/lib/i18n';
import type {FundamentalResearch,FundamentalPeriod,FinancialFrequency} from '@/lib/types';
import {FINANCIAL_LABELS,type FinancialKey} from '@/lib/fundamental-data';
import {amountFields,growthFields,engineAmounts,multipleFields,researchSections,unitDivisor,unitLabels,type AmountUnit,type ResearchSection} from '@/lib/fundamental-research';
import {financialEngineData} from '@/lib/financial-engine-data';
import {direction} from '@/lib/presentation';
import {stockRead} from '@/lib/stock-detail';
import FinancialResearchChart from './FinancialResearchCharts';
import FinancialStatementTable from './FinancialStatementTable';
import {Button} from '../ui/button';
import {Skeleton} from '../ui/skeleton';

const sectionLabels={overview:'Financial overview',performance:'Business performance',statements:'Financial statements',ratios:'Financial ratios'} as const;
const statementLabels={income:'Income statement',balance:'Balance sheet',cash:'Cash flow statement'} as const;

function FinancialTable({rows,fields,unit,label}:{rows:FundamentalPeriod[];fields:readonly FinancialKey[];unit:AmountUnit;label:string}){
  const {ui,t,number,percent}=useLocale();
  return <div className="fundamental-table-scroll" role="region" aria-label={ui(label)} tabIndex={0}><table className="fundamental-table text-xs">
    <caption className="sr-only">{ui(label)} · {ui(unitLabels[unit])} · {t('Dash means unavailable; missing is not zero.')}</caption>
    <thead><tr><th scope="col">{t('Metric')}</th>{rows.map(row=><th scope="col" key={row.period}>{row.period}</th>)}</tr></thead>
    <tbody>{fields.map(key=><tr key={key}><th scope="row">{ui(FINANCIAL_LABELS[key])}</th>{rows.map(row=><td key={row.period}>{engineAmounts.includes(key as typeof engineAmounts[number])?row[key]==null?'—':number(row[key]!/unitDivisor[unit],unit==='vnd'?0:2):multipleFields.includes(key as typeof multipleFields[number])?row[key]==null?'—':number(row[key])+'×':key==='eps_reported'?number(row[key]):percent(row[key],key.includes('growth'))}</td>)}</tr>)}</tbody>
  </table></div>;
}

function ChangeSummary({data,unit}:{data:FundamentalResearch;unit:AmountUnit}){
  const {t,ui,number,percent}=useLocale();
  const amount=(value:number|null,signed=false)=>value===null?'—':(signed&&value>0?'+':'')+number(value/unitDivisor[unit],unit==='vnd'?0:2);
  return <section className="border-t pt-4" aria-label={t('What changed?')}><h3 className="text-sm font-semibold">{t('What changed?')}</h3><p className="mt-1 text-xs text-muted-foreground">{t('Exact prior-year comparison. Numerical changes do not explain causes.')}</p>
    {!data.changes.length?<p className="stock-note">{t('Comparable prior-year data is unavailable.')}</p>:<div className="fundamental-table-scroll mt-3" role="region" tabIndex={0} aria-label={t(data.period_type==='annual'?'Annual changes':'Comparable period changes')}><table className="fundamental-table text-xs"><caption className="sr-only">{t(data.period_type==='annual'?'Annual changes':'Comparable period changes')} · {ui(unitLabels[unit])}</caption><thead><tr><th scope="col">{t('Metric')}</th><th scope="col">{data.changes[0].current_period}</th><th scope="col">{data.changes[0].prior_period}</th><th scope="col">{t('Absolute change')}</th><th scope="col">{t('YoY')}</th></tr></thead><tbody>{data.changes.map(change=><tr key={change.metric}><th scope="row">{ui(FINANCIAL_LABELS[change.metric])}</th><td>{amount(change.current)}</td><td>{amount(change.previous)}</td><td className={direction(change.absolute_change)}>{amount(change.absolute_change,true)}</td><td className={direction(change.growth_yoy)}>{percent(change.growth_yoy,true)}</td></tr>)}</tbody></table></div>}
    <p className="mt-2 text-[11px] text-muted-foreground">{t('Growth requires a positive comparable base. Missing, zero or negative bases remain unavailable.')}</p>
  </section>;
}

export default function FundamentalTrends({ticker,visible=true}:{ticker:string;visible?:boolean}){
  const [data,setData]=useState<FundamentalResearch|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState(false),[attempt,setAttempt]=useState(0),[frequency,setFrequency]=useState<FinancialFrequency>('annual');
  useEffect(()=>{
    const controller=new AbortController();let disposed=false;const timeout=setTimeout(()=>controller.abort(),60000);
    setLoading(true);setError(false);setData(null);
    stockRead<FundamentalResearch>(`/api/stocks/${encodeURIComponent(ticker)}/financials?frequency=${frequency}&limit=8&projection=display`,controller.signal)
      .then(value=>{const result=financialEngineData(value,ticker,frequency);if(!disposed)setData(result);})
      .catch(()=>{if(!disposed)setError(true);}).finally(()=>{clearTimeout(timeout);if(!disposed)setLoading(false);});
    return()=>{disposed=true;clearTimeout(timeout);controller.abort();};
  },[ticker,attempt,frequency]);
  return <FundamentalTrendsView data={data} loading={loading} error={error} retry={()=>setAttempt(value=>value+1)} visible={visible} frequency={frequency} onFrequency={setFrequency}/>;
}

export function FundamentalTrendsView({data,loading,error,retry,visible=true,frequency='annual',onFrequency=()=>{}}:{data:FundamentalResearch|null;loading:boolean;error:boolean;retry:()=>void;visible?:boolean;frequency?:FinancialFrequency;onFrequency?:(value:FinancialFrequency)=>void}){
  const {t,ui,number,percent,date}=useLocale();
  const [section,setSection]=useState<ResearchSection>('overview'),[unit,setUnit]=useState<AmountUnit>('billions'),[count,setCount]=useState(0),[statement,setStatement]=useState<keyof typeof statementLabels>('income');
  const rows=count?data?.rows.slice(-count)||[]:data?.rows||[];
  const latest=rows.at(-1);
  const amounts:readonly FinancialKey[]=data?.profile==='bank'?['operating_income','net_profit']:data?.financial_identity_guard?['net_profit']:amountFields;
  const growth:readonly FinancialKey[]=data?.profile==='bank'?['operating_income_growth_yoy','net_profit_growth_yoy']:data?.financial_identity_guard?['net_profit_growth_yoy']:growthFields;
  const ratios:readonly FinancialKey[]=data?.financial_identity_guard?['roe','roa']:['gross_margin','net_margin','roe','roa'];
  const quote=(key:FinancialKey)=>engineAmounts.includes(key as typeof engineAmounts[number])?latest?.[key]==null?'—':number(latest[key]!/unitDivisor[unit],unit==='vnd'?0:2):percent(latest?.[key]);
  const chartProps={rows,visible,unit,frequency,chartRows:data?.chart_rows?.filter(row=>row.period>=(rows[0]?.period||'')&&row.period<=(latest?.period||''))};
  const statementPeriods=data?.statements?.[statement]?.periods.filter(row=>rows.some(value=>value.period===row.period))||[];
  return <section className="min-w-0 space-y-5" aria-labelledby="fundamental-engine-title" hidden={!visible}>
    <header className="flex flex-wrap items-start justify-between gap-3"><div><p className="eyebrow mb-1">{t('Company performance')}</p><h2 id="fundamental-engine-title" className="text-xl">{t('Fundamental analysis')}</h2><p className="mt-1 text-xs text-muted-foreground">{t('Reported financials')}{latest?' · '+latest.period+' · '+data!.source:''}</p></div>
      <div className="flex flex-wrap items-center gap-2 text-xs"><div className="inline-flex rounded-md border p-0.5" role="group" aria-label={t('Reporting frequency')}>{(['annual','quarterly','ttm'] as const).map(value=><button key={value} type="button" aria-pressed={frequency===value} disabled={loading||!!data&&!data.available_period_types.includes(value)} onClick={()=>onFrequency(value)} className={`rounded px-3 py-1.5 disabled:opacity-50 ${frequency===value?'bg-primary/10 text-primary':'text-muted-foreground'}`}>{t(value==='annual'?'Annual':value==='quarterly'?'Quarterly':'TTM')}</button>)}</div>
        <label className="sr-only" htmlFor="financial-engine-units">{t('Amount units')}</label><select id="financial-engine-units" value={unit} onChange={e=>setUnit(e.target.value as AmountUnit)} className="rounded border bg-background px-2 py-2">{Object.entries(unitLabels).map(([key,label])=><option key={key} value={key}>{ui(label)}</option>)}</select>
        <label className="sr-only" htmlFor="financial-engine-periods">{t('Historical periods')}</label><select id="financial-engine-periods" value={count} onChange={e=>setCount(Number(e.target.value))} className="rounded border bg-background px-2 py-2"><option value={0}>{t('All loaded periods')}</option>{[2,4,8].map(n=><option key={n} value={n}>{t('{count} reporting periods',{count:n})}</option>)}</select>
      </div>
    </header>
    <nav aria-label={t('Financial research sections')} className="flex gap-1 overflow-x-auto border-b pb-2">{researchSections.map(key=><button key={key} type="button" aria-pressed={section===key} onClick={()=>setSection(key)} className={`shrink-0 rounded-md px-3 py-2 text-xs focus-visible:outline-2 focus-visible:outline-ring ${section===key?'bg-primary/10 font-medium text-primary':'text-muted-foreground hover:bg-muted'}`}>{t(sectionLabels[key])}</button>)}</nav>
    {loading?<div role="status" aria-label={t('Loading financial statements')} className="space-y-4"><Skeleton className="h-24"/><Skeleton className="h-64"/></div>:error?<div role="alert" className="border-y py-8 text-center"><p className="mb-3 text-sm">{t('Financial statements are temporarily unavailable.')}</p><Button variant="outline" onClick={retry}>{t('Retry financials')}</Button></div>:!data||!rows.length?<p className="py-8 text-sm text-muted-foreground">{t('No financial observations are available for this frequency.')}</p>:<>
      <div className="flex flex-wrap justify-between gap-2 text-[11px] leading-5 text-muted-foreground"><p>{frequency==='quarterly'?t('Quarterly ROE and ROA are period returns, not annualized.'):frequency==='ttm'?t('TTM sums four contiguous qualified quarters; balance values remain period-end.'):t('Reported annual statements are kept independently of quarterly totals.')}</p><span>{rows[0]?.period}–{latest?.period} · {ui(unitLabels[unit])}</span></div>
      {data.is_fixture&&<p className="stock-note">{t('Fixture data; not live financial evidence.')}</p>}
      {data.financial_identity_guard&&<p className="rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs leading-5">{t('Financial issuer metrics use qualified statement fields. Generic revenue and liquidity ratios are excluded.')}</p>}
      {section==='overview'&&<><dl className="grid grid-cols-2 gap-x-6 gap-y-4 border-y py-4 sm:grid-cols-3 xl:grid-cols-5">{[...amounts,'equity','roe','roa' as FinancialKey].map(key=><div key={key}><dt className="text-xs text-muted-foreground">{ui(FINANCIAL_LABELS[key as FinancialKey])}</dt><dd className="financial mt-2 break-words text-lg font-semibold">{quote(key as FinancialKey)}</dd></div>)}</dl><ChangeSummary data={data} unit={unit}/><div className="grid min-w-0 gap-6 xl:grid-cols-2"><FinancialResearchChart {...chartProps} fields={amounts} title="Revenue and profit trends"/><FinancialResearchChart {...chartProps} fields={growth} title="Year-over-year growth" percentage/></div></>}
      {section==='performance'&&<><div className="grid min-w-0 gap-6 xl:grid-cols-2"><FinancialResearchChart {...chartProps} fields={amounts} title="Revenue and profit trends"/><FinancialResearchChart {...chartProps} fields={growth} title="Year-over-year growth" percentage/></div><FinancialTable rows={rows} fields={[...amounts,'profit_parent',...growth]} unit={unit} label="Business performance"/></>}
      {section==='statements'&&<section aria-label={t('Financial statements')}><div className="mb-4 flex flex-wrap gap-2" role="group" aria-label={t('Statement type')}>{Object.entries(statementLabels).map(([key,label])=><Button key={key} size="sm" variant={statement===key?'secondary':'outline'} aria-pressed={statement===key} onClick={()=>setStatement(key as keyof typeof statementLabels)}>{t(label)}</Button>)}</div>{frequency==='ttm'&&<p className="mb-3 text-xs text-muted-foreground">{t('Statement tables show original quarterly reports, not synthetic TTM statements.')}</p>}{statementPeriods.length?<FinancialStatementTable periods={statementPeriods} unit={unit} label={statementLabels[statement]}/>:<p className="stock-note">{t('This statement is unavailable for the selected periods.')}</p>}</section>}
      {section==='ratios'&&<><FinancialResearchChart {...chartProps} fields={ratios} title="Profitability" percentage/><FinancialTable rows={rows} fields={[...ratios,...growth]} unit={unit} label="Financial ratios"/><div className="grid min-w-0 gap-5 border-t pt-5 xl:grid-cols-2"><FinancialTable rows={rows} fields={data.financial_identity_guard?['liabilities_assets']:['debt_equity','liabilities_assets','current_ratio','quick_ratio']} unit={unit} label="Financial position / leverage"/><FinancialTable rows={rows} fields={data.financial_identity_guard?['cash_operating']:['cash_operating','cash_investing','cash_financing','free_cash_flow','cash_conversion']} unit={unit} label="Cash flow statement"/></div><p className="stock-note">{t('Valuation, NIM, NPL and CASA require verified inputs and remain unavailable.')}</p></>}
      <details className="border-t pt-3 text-xs text-muted-foreground"><summary className="cursor-pointer font-medium">{t('Financial source and coverage')}</summary><dl className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-2"><div><dt>{t('Source')}</dt><dd>{data.source} · {data.source_version}</dd></div><div><dt>{t('Read at')}</dt><dd>{date(data.read_at,true)} · {t('Provider or process cache; not a publication timestamp.')}</dd></div><div><dt>{t('Report basis')}</dt><dd>{data.consolidation||t('Consolidated / standalone status is not supplied.')}</dd></div><div><dt>{t('Publication date')}</dt><dd>{t('Source dates are shown as reported, without inferred timezone.')}</dd></div></dl>
        {data.source_receipts?.map(receipt=><details key={receipt.statement} className="mt-4 border-t pt-2"><summary className="cursor-pointer">{ui(statementLabels[receipt.statement as keyof typeof statementLabels])} · {ui(receipt.status)}</summary><p className="mt-2">{t('Observed at')}: {date(receipt.observed_at,true)}</p><p className="mt-1 break-all">{receipt.source_url}</p><p className="mt-1 break-all">SHA-256: {receipt.content_sha256||'—'}</p>{receipt.periods.filter(period=>rows.some(row=>row.period===period.period)).map(period=><p key={period.period} className="mt-2">{period.period} · {ui(period.basis)} · {t('Publication date')}: {period.source_dates.publicDate||'—'} · {period.diagnostics.join(', ')}</p>)}</details>)}
        <details className="mt-4 border-t pt-2"><summary className="cursor-pointer">{t('Calculation evidence')}</summary><p className="mt-2">{t('ROE uses total profit and average total equity, not parent-shareholder ROE.')}</p>{Object.entries(latest?.calculations||{}).map(([metric,evidence])=><details key={metric} className="mt-3"><summary className="cursor-pointer">{ui(FINANCIAL_LABELS[metric as FinancialKey]||metric)}{evidence.reason?' · '+ui(evidence.reason):''}</summary><p className="mt-1">{evidence.formula}</p><pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap break-all text-[10px]">{JSON.stringify(evidence.inputs,null,2)}</pre></details>)}</details>
        {!!data.reconciliations?.length&&<details className="mt-4 border-t pt-2"><summary className="cursor-pointer">{t('Annual / quarterly differences')}</summary><p className="mt-2">{t('Differences retain source versions; no cause is inferred.')}</p>{data.reconciliations.map(item=><p className="mt-2" key={`${item.statement}-${item.period}-${item.field}`}>{item.period} · {ui(FINANCIAL_LABELS[item.field as FinancialKey]||item.field)} · {t('Annual')}: {number(item.annual_reported/unitDivisor[unit])} · {t('Quarter sum')}: {number(item.quarter_sum/unitDivisor[unit])} · {t('Absolute change')}: {number(item.difference/unitDivisor[unit])} {ui(unitLabels[unit])}</p>)}</details>}
        <ul className="mt-3 space-y-1">{data.limitations?.map(value=><li key={value}>{ui(value)}</li>)}</ul>
      </details>
    </>}
  </section>;
}
