"use client";
import {useEffect,useRef,useState} from 'react';
import {useLocale} from '@/lib/i18n';
import type {FundamentalResearch,FundamentalPeriod,FinancialFrequency,FinancialPanel} from '@/lib/types';
import {FINANCIAL_LABELS,type FinancialKey} from '@/lib/fundamental-data';
import {amountFields,growthFields,engineAmounts,multipleFields,researchSections,availableFinancialSections,unitDivisor,unitLabels,consolidationLabel,type AmountUnit,type ResearchSection} from '@/lib/fundamental-research';
import {financialEngineData} from '@/lib/financial-engine-data';
import {verificationEvidence,verificationDimensions,verificationDimensionLabels} from '@/lib/financial-verification';
import {formatFinancialAmount} from '@/lib/financial-format';
import {direction} from '@/lib/presentation';
import {stockRead} from '@/lib/stock-detail';
import FinancialResearchChart from './FinancialResearchCharts';
import FinancialStatementTable from './FinancialStatementTable';
import FinancialAnalysisPanel from './FinancialAnalysisPanel';
import {selectFinancialPanel,financialSourceLink,panelTitles} from '@/lib/financial-panels';
import {Button} from '../ui/button';
import {Skeleton} from '../ui/skeleton';

const sectionLabels={overview:'Financial overview',performance:'Revenue, earnings & growth',balance:'Balance sheet',cashflow:'Cash flow analysis',profitability:'Profitability',health:'Financial health',valuation:'Valuation',statements:'Financial statements',sources:'Documents and sources'} as const;
const statementLabels={income:'Income statement',balance:'Balance sheet',cash:'Cash flow statement'} as const;

export function FinancialVerificationSummary({data}:{data:FundamentalResearch}){
  const {ui}=useLocale(),v=data.verification;
  if(!v||data.is_fixture)return null;
  const latest=v.periods.at(-1);
  return <details className="rounded-md border px-3 py-2 text-xs" data-financial-verification>
    <summary className="cursor-pointer font-medium">{ui('Verification and availability')} · {latest?.period} · {ui('VERIFIED')}: {v.statuses.VERIFIED} · {ui('PARTIALLY_VERIFIED')}: {v.statuses.PARTIALLY_VERIFIED} · {ui('UNAVAILABLE')}: {v.statuses.UNAVAILABLE}</summary>
    <p className="stock-note">{ui('Evidence grades do not grant public display rights. Partial source observations may be visible in the authorized local research view; missing metadata remains explicit.')}</p>
    <div className="fundamental-table-scroll mt-2" role="region" tabIndex={0} aria-label={ui('Verification and availability')}><table className="fundamental-table"><thead><tr><th>{ui('Metric')}</th><th>{ui('Verification')}</th><th>{ui('Available in this view')}</th><th>{ui('Missing evidence')}</th></tr></thead><tbody>{Object.entries(latest?.metrics||{}).map(([key,m])=><tr key={key}><th scope="row">{ui(FINANCIAL_LABELS[key as FinancialKey]||key.replaceAll('_',' '))}</th><td>{ui(m.status)}{m.dimensions&&<dl className="mt-1 space-y-1 text-muted-foreground">{verificationDimensions.map(k=><div key={k}><dt className="inline">{ui(verificationDimensionLabels[k])}: </dt><dd className="inline">{ui(m.dimensions![k]?'Yes':'No')}</dd></div>)}</dl>}</td><td>{ui(m.display_eligible?'Yes':'No')}</td><td className="whitespace-normal">{m.missing_evidence.length?m.missing_evidence.map(code=>ui(verificationEvidence[code]||code.replaceAll('_',' '))).join(' · '):'—'}</td></tr>)}</tbody></table></div>
  </details>;
}

function FinancialTable({rows,fields,unit,label}:{rows:FundamentalPeriod[];fields:readonly FinancialKey[];unit:AmountUnit;label:string}){
  const {ui,t,number,percent}=useLocale();
  return <div className="fundamental-table-scroll" role="region" aria-label={ui(label)} tabIndex={0}><table className="fundamental-table text-xs">
    <caption className="sr-only">{ui(label)} · {ui(unitLabels[unit])} · {t('Dash means unavailable; missing is not zero.')}</caption>
    <thead><tr><th scope="col">{t('Metric')}</th>{rows.map(row=><th scope="col" key={row.period}>{row.period}</th>)}</tr></thead>
    <tbody>{fields.map(key=><tr key={key}><th scope="row"><details><summary className="cursor-pointer">{ui(FINANCIAL_LABELS[key])}</summary><p className="max-w-xs whitespace-normal py-2 text-muted-foreground">{rows.at(-1)?.calculations?.[key]?.formula||ui('Reported source amount')}</p></details></th>{rows.map(row=><td key={row.period}>{engineAmounts.includes(key as typeof engineAmounts[number])?row[key]==null?'—':formatFinancialAmount(row[key]!,unitDivisor[unit],unit==='vnd'?0:2,number):multipleFields.includes(key as typeof multipleFields[number])?row[key]==null?'—':number(row[key])+'×':key==='eps_reported'?number(row[key]):percent(row[key],key.includes('growth'))}</td>)}</tr>)}</tbody>
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

export function FundamentalOverview({data,unit,groups}:{data:FundamentalResearch;unit:AmountUnit;groups?:readonly string[]}){
  const {t,ui,number,percent}=useLocale();
  const summary=data.fundamental_summary;
  if(!summary)return <p className="stock-note">{t('Financial display qualification is unavailable.')}</p>;
  const labels={valuation:'Valuation',performance:'Business performance',profitability:'Profitability',health:'Financial health'} as const;
  return <section aria-label={t('Fundamental snapshot')} className="space-y-3">
    {data.display_scope==='personal_research'&&<p className="stock-note" data-financial-scope="personal_research"><strong>{t('Personal Research')}</strong> · {t('SOURCE_REPORTED')} · {t('Source-reported financial data. Consolidation basis not independently verified.')} · {t('Public display review required.')}</p>}
    {data.display_scope==='internal_research'&&<p className="stock-note" data-financial-scope="internal_research">{t('INTERNAL RESEARCH · Original filing evidence; public display is disabled.')}</p>}
    <p className="stock-note">{t('Qualification applies to the reported period; current freshness is not certified. Inspect each metric for its definition and limitations.')}</p>
    <div className="grid min-w-0 gap-x-6 gap-y-5 lg:grid-cols-2">{(Object.keys(labels) as (keyof typeof labels)[]).filter(group=>!groups||groups.includes(group)).map(group=><section key={group} className="min-w-0 border-t pt-3" aria-label={ui(labels[group])}>
      <h3 className="text-sm font-semibold">{ui(labels[group])}</h3>
      {group==='valuation'&&<p className="mt-1 text-[11px] text-muted-foreground">{t('Reported EPS is not a valuation ratio. Compatible price and share bases are required for valuation.')}</p>}
      <dl className="mt-2 divide-y">{summary.metrics.filter(metric=>metric.group===group).map(metric=>{
        const basis=metric.consolidation===undefined?summary.consolidation:metric.consolidation;
        const allowed=metric.status==='SOURCE_REPORTED'&&data.display_scope==='personal_research'&&metric.data_confidence==='SOURCE_REPORTED'||metric.status==='QUALIFIED'&&data.is_fixture===false&&['consolidated','standalone'].includes(basis||'')||metric.status==='DEMO'&&data.is_fixture===true;
        const value=allowed?metric.value:null;
        const formatted=value===null?'—':metric.unit==='fraction'?percent(value):metric.unit==='multiple'?number(value)+'×':metric.unit==='VND/share'?number(value)+' '+t('VND/share'):number(value/unitDivisor[unit],unit==='vnd'?0:2)+' '+ui(unitLabels[unit]);
        return <div key={metric.key} className="flex min-w-0 items-start justify-between gap-3 py-2"><dt className="min-w-0 text-xs"><details><summary className="cursor-pointer"><span>{ui(metric.label)}</span><span className="mt-0.5 block text-[10px] text-muted-foreground" data-financial-qualification={metric.status}>{ui(metric.status)}</span></summary><div className="mt-2 space-y-1 break-words text-[11px] text-muted-foreground"><p>{summary.period} · {ui(consolidationLabel(basis))}</p><p>{metric.formula}</p>{(metric.blockers?.length?metric.blockers:metric.reason?[metric.reason]:[]).map(reason=><p key={reason}>{ui(reason)}</p>)}</div></details></dt><dd className="financial mt-2 min-w-0 max-w-[55%] break-words text-right text-lg font-semibold">{formatted}</dd></div>;
      })}</dl>
    </section>)}</div>
  </section>;
}

export default function FundamentalTrends({ticker,visible=true,personalResearch=false,onActions}:{ticker:string;visible?:boolean;personalResearch?:boolean;onActions?:()=>void}){
  const [data,setData]=useState<FundamentalResearch|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState(false),[attempt,setAttempt]=useState(0),[frequency,setFrequency]=useState<FinancialFrequency>('annual');
  const [sourcePreference,setSourcePreference]=useState<'preferred'|'provider'>('preferred');
  const recent=useRef(new Map<string,{data:FundamentalResearch;at:number}>());
  useEffect(()=>{
    const key=`${personalResearch}:${ticker}:${frequency}:${sourcePreference}`,cached=recent.current.get(key);
    const age=cached?Date.now()-cached.at:Infinity;
    // Reuse only successful, validated reads during a brief frequency round-trip.
    // Original read/source times remain intact; this never promotes freshness.
    if(cached&&age>=0&&age<60000){
      recent.current.delete(key);recent.current.set(key,cached);
      setData(cached.data);setError(false);setLoading(false);return;
    }
    recent.current.delete(key);
    const controller=new AbortController();let disposed=false;const timeout=setTimeout(()=>controller.abort(),60000);
    setLoading(true);setError(false);setData(null);
    stockRead<FundamentalResearch>(personalResearch?`/api/personal-research/financials/${encodeURIComponent(ticker)}?frequency=${frequency}&evidence=${sourcePreference}`:`/api/stocks/${encodeURIComponent(ticker)}/financials?frequency=${frequency}&limit=8&projection=display`,controller.signal)
      .then(value=>{const result=financialEngineData(value,ticker,frequency,true,personalResearch,personalResearch);if(!disposed){
        recent.current.set(key,{data:result,at:Date.now()});
        while(recent.current.size>3)recent.current.delete(recent.current.keys().next().value!);
        setData(result);
      }})
      .catch(()=>{if(!disposed)setError(true);}).finally(()=>{clearTimeout(timeout);if(!disposed)setLoading(false);});
    return()=>{disposed=true;clearTimeout(timeout);controller.abort();};
  },[ticker,attempt,frequency,personalResearch,sourcePreference]);
  const matches=data?.ticker===ticker&&data?.period_type===frequency;
  return <FundamentalTrendsView data={matches?data:null} loading={loading||(!matches&&!error)} error={error} retry={()=>{recent.current.delete(`${personalResearch}:${ticker}:${frequency}:${sourcePreference}`);setAttempt(value=>value+1);}} visible={visible} frequency={frequency} onFrequency={setFrequency} sourcePreference={personalResearch?sourcePreference:undefined} onSourcePreference={setSourcePreference} onActions={onActions}/>;
}

export function FundamentalTrendsView({data,loading,error,retry,visible=true,frequency='annual',onFrequency=()=>{},sourcePreference,onSourcePreference,onActions,initialSection='overview'}:{data:FundamentalResearch|null;loading:boolean;error:boolean;retry:()=>void;visible?:boolean;frequency?:FinancialFrequency;onFrequency?:(value:FinancialFrequency)=>void;sourcePreference?:'preferred'|'provider';onSourcePreference?:(value:'preferred'|'provider')=>void;onActions?:()=>void;initialSection?:ResearchSection}){
  const {t,ui,number,percent,date}=useLocale();
  const [section,setSection]=useState<ResearchSection>(initialSection),[unit,setUnit]=useState<AmountUnit>('billions'),[count,setCount]=useState(0),[statement,setStatement]=useState<keyof typeof statementLabels>('income');
  const rows=count?data?.rows.slice(-count)||[]:data?.rows||[];
  const latest=rows.at(-1);
  const availableSections=availableFinancialSections(data,rows);
  const activeSection=rows.length&&!availableSections.includes(section)?'overview':section;
  const amounts:readonly FinancialKey[]=data?.profile==='bank'?['operating_income','net_profit']:data?.financial_identity_guard?['net_profit']:amountFields;
  const growth:readonly FinancialKey[]=data?.profile==='bank'?['operating_income_growth_yoy','net_profit_growth_yoy']:data?.financial_identity_guard?['net_profit_growth_yoy']:growthFields;
  const ratios:readonly FinancialKey[]=data?.financial_identity_guard?['roe','roa']:['gross_margin','net_margin','roe','roa'];
  const chartProps={rows,visible,unit,frequency,chartRows:data?.chart_rows?.filter(row=>row.period>=(rows[0]?.period||'')&&row.period<=(latest?.period||''))};
  const statementPeriods=data?.statements?.[statement]?.periods.filter(row=>rows.some(value=>value.period===row.period))||[];
  const panel=(kind:FinancialPanel['key'])=><FinancialAnalysisPanel key={`${data?.ticker}:${frequency}:${kind}`} kind={kind} panel={data?selectFinancialPanel(data,kind,rows.map(r=>r.period)):undefined} unit={unit} visible={visible} isFixture={data?.is_fixture===true} personalResearch={data?.display_scope==='personal_research'} onSources={()=>setSection('sources')}/>;
  const panels=(kinds:FinancialPanel['key'][])=>{
    const available=kinds.filter(kind=>{
      const selected=data?selectFinancialPanel(data,kind,rows.map(r=>r.period)):undefined;
      return selected?.rows.some(row=>Object.values(row.values).some(value=>value!==null));
    });
    const unavailable=kinds.filter(kind=>!available.includes(kind));
    const reasons=[...new Set(unavailable.flatMap(kind=>data?selectFinancialPanel(data,kind,rows.map(r=>r.period))?.reasons||[]:[]))];
    return <>{available.length>0&&<div className="grid min-w-0 gap-4 xl:grid-cols-2">{available.map(panel)}</div>}{unavailable.length>0&&<details className="rounded-md border px-3 py-2 text-xs" data-financial-unavailable-group>
      <summary className="cursor-pointer font-medium">{t('Charts awaiting qualified inputs')} · {unavailable.map(kind=>ui(kind==='growth'&&data?.profile==='bank'?'Operating income and profit trends':panelTitles[kind])).join(', ')}</summary>
      <p className="mt-2 text-muted-foreground">{t('Unavailable values are withheld; existing qualified metrics remain visible.')}</p>
      <ul className="mt-2 space-y-1">{reasons.map(reason=><li key={reason}>{ui(reason)}</li>)}</ul>
      <button type="button" className="mt-2 underline" onClick={()=>setSection('sources')}>{t('Inspect financial sources')}</button>
    </details>}</>;
  };
  return <section className="stock-financial-research min-w-0 space-y-4" aria-labelledby="fundamental-engine-title" hidden={!visible}>
    <header className="financial-research-header"><div><p className="eyebrow mb-1">{t('Company performance')}</p><h2 id="fundamental-engine-title" className="text-xl">{t('Fundamental analysis')}</h2><p className="mt-1 text-xs text-muted-foreground">{t('Reported financials')}{latest?' · '+latest.period+' · '+data!.source:''}</p></div>
      <div className="financial-research-toolbar"><div className="inline-flex rounded-md border p-0.5" role="group" aria-label={t('Reporting frequency')}>{(['annual','quarterly','ttm'] as const).map(value=><button key={value} type="button" aria-pressed={frequency===value} disabled={loading||!!data&&!data.available_period_types.includes(value)} onClick={()=>onFrequency(value)} className={`rounded px-3 py-1.5 disabled:opacity-50 ${frequency===value?'bg-primary/10 text-primary':'text-muted-foreground'}`}>{t(value==='annual'?'Annual':value==='quarterly'?'Quarterly':'TTM')}</button>)}</div>
        <label htmlFor="financial-engine-units">{t('Amount units')}<select id="financial-engine-units" value={unit} onChange={e=>setUnit(e.target.value as AmountUnit)} className="rounded border bg-background px-2 py-2">{Object.entries(unitLabels).map(([key,label])=><option key={key} value={key}>{ui(label)}</option>)}</select></label>
        <label htmlFor="financial-engine-periods">{t('Historical periods')}<select id="financial-engine-periods" value={count} onChange={e=>setCount(Number(e.target.value))} className="rounded border bg-background px-2 py-2"><option value={0}>{t('All loaded periods')}</option>{[2,4,8].map(n=><option key={n} value={n}>{t('{count} reporting periods',{count:n})}</option>)}</select></label>
        {sourcePreference&&<label>{ui('Evidence source')}<select value={sourcePreference} onChange={e=>onSourcePreference?.(e.target.value as 'preferred'|'provider')} className="rounded border bg-background px-2 py-2"><option value="preferred">{ui('Reviewed report when available')}</option><option value="provider">{ui('Saved provider history')}</option></select></label>}
      </div>
    </header>
    {!loading&&!error&&data&&<FinancialVerificationSummary data={data}/>}
    <a className="text-xs text-primary underline" href={`/industries?ticker=${encodeURIComponent(data?.ticker||'')}&period=${latest?.period||''}&frequency=${frequency}`}>{ui('Industry comparison')}</a><nav aria-label={t('Financial research sections')} className="financial-research-nav">{availableSections.map(key=><button key={key} type="button" aria-pressed={activeSection===key} onClick={()=>setSection(key)} className={`rounded-md px-3 py-2 text-xs focus-visible:outline-2 focus-visible:outline-ring ${activeSection===key?'bg-primary/10 font-medium text-primary':'text-muted-foreground hover:bg-muted'}`}>{t(sectionLabels[key])}</button>)}{onActions&&<button type="button" className="rounded-md px-3 py-2 text-xs text-muted-foreground hover:bg-muted" onClick={onActions}>{t('Dividends & corporate actions')}</button>}</nav>
    {loading?<div role="status" aria-label={t('Loading financial statements')} className="space-y-4"><Skeleton className="h-24"/><Skeleton className="h-64"/></div>:error?<div role="alert" className="border-y py-8 text-center"><p className="mb-3 text-sm">{t('Financial statements are temporarily unavailable.')}</p><Button variant="outline" onClick={retry}>{t('Retry financials')}</Button></div>:!data?<p className="py-8 text-sm text-muted-foreground">{t('No financial observations are available for this frequency.')}</p>:<>
      {!rows.length&&<p className="stock-note">{t('No financial observations are available for this frequency.')}</p>}
      <div className="flex flex-wrap justify-between gap-2 text-[11px] leading-5 text-muted-foreground"><p>{frequency==='quarterly'?t('Quarterly ROE and ROA are period returns, not annualized.'):frequency==='ttm'?t('TTM sums four contiguous qualified quarters; balance values remain period-end.'):t('Reported annual statements are kept independently of quarterly totals.')}</p><span>{rows[0]?.period}–{latest?.period} · {ui(unitLabels[unit])}</span></div>
      {data.is_fixture&&<p className="stock-note">{t('Fixture data; not live financial evidence.')}</p>}
      {data.display_scope==='personal_research'&&<p className="stock-note" data-financial-scope="personal_research"><strong>{t('Personal Research')}</strong> · {t('SOURCE_REPORTED')} · {t('Source-reported financial data. Consolidation basis not independently verified.')} · {t('Public display review required.')}</p>}
    {data.display_scope==='internal_research'&&<p className="stock-note" data-financial-scope="internal_research">{t('INTERNAL RESEARCH · Original filing evidence; public display is disabled.')}</p>}
      <p className="text-[11px] leading-5 text-muted-foreground">{t('Report basis')}: {ui(consolidationLabel(data.fundamental_summary?.consolidation??data.consolidation))} · {t('Read at')}: {date(data.read_at,true)} ICT · {t(data.display_scope==='personal_research'?'Saved personal research; not current data.':data.display_scope==='internal_research'?'Saved filing review; not current market data.':'Provider or process cache; not a publication timestamp.')}</p>
      {data.fundamental_summary&&<div className="financial-coverage-strip" aria-label={t('Loaded metric coverage')}><span>{t('Loaded metric coverage')}</span>{(['QUALIFIED','SOURCE_REPORTED','DEMO','UNQUALIFIED','UNAVAILABLE'] as const).map(status=><span key={status} data-financial-coverage={status}>{ui(status)}: {number(data.fundamental_summary!.metrics.filter(metric=>metric.status===status).length,0)}</span>)}<button type="button" onClick={()=>setSection('sources')}>{t('Inspect financial sources')}</button></div>}
      {data.financial_identity_guard&&<p className="rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-xs leading-5">{t('Financial issuer metrics use qualified statement fields. Generic revenue and liquidity ratios are excluded.')}</p>}
      <FinancialHeadlines data={data} rows={rows} unit={unit}/>
      {activeSection==='overview'&&<>{panels(data.display_scope==='personal_research'?['growth','balance_history','cashflow','profitability',...(data.profile==='bank'?['bank_funding'] as const:['liquidity'] as const)]:['growth','assets','funding','cashflow','profitability',...(data.profile==='bank'?['bank_funding'] as const:['liquidity'] as const)])}<section className="border-y py-3" aria-label={t('Business observations')}><h3 className="text-sm font-semibold">{t('Business observations')}</h3><p className="mt-1 text-xs text-muted-foreground">{t('Only individually qualified period metrics are shown below. Missing categories are not estimates; numerical changes do not establish causes.')}</p><FundamentalOverview data={data} unit={unit} groups={['profitability','health']}/></section><details className="border-t pt-3"><summary className="cursor-pointer text-sm font-medium">{t('Financial ratios')}</summary><div className="mt-4 space-y-4"><FinancialResearchChart {...chartProps} fields={ratios} title="Profitability" percentage/><FinancialTable rows={rows} fields={[...ratios,...growth]} unit={unit} label="Financial ratios"/><div className="grid min-w-0 gap-5 xl:grid-cols-2"><FinancialTable rows={rows} fields={data.financial_identity_guard?['liabilities_assets']:['debt_equity','liabilities_assets','current_ratio','quick_ratio']} unit={unit} label="Financial position / leverage"/><FinancialTable rows={rows} fields={data.financial_identity_guard?['cash_operating']:['cash_operating','cash_investing','cash_financing','free_cash_flow','cash_conversion']} unit={unit} label="Cash flow statement"/></div></div></details></>}
      {activeSection==='performance'&&<>{panels(['growth','quarterly'])}<FundamentalOverview data={data} unit={unit} groups={['performance','profitability']}/><p className="stock-note">{t('Operating margin requires a qualified operating-profit input and remains unavailable.')}</p><ChangeSummary data={data} unit={unit}/><FinancialTable rows={rows} fields={[...amounts,'profit_parent',...growth]} unit={unit} label="Business performance"/></>}
      {activeSection==='balance'&&<>{panels(data.display_scope==='personal_research'?['balance_history']:['assets','funding'])}<FinancialTable rows={rows} fields={['total_assets','total_liabilities','equity']} unit={unit} label="Balance sheet"/></>}
      {activeSection==='cashflow'&&<>{panels(['cashflow'])}<FinancialTable rows={rows} fields={['cash_operating','cash_investing','cash_financing',...(data.profile==='non_financial'?['free_cash_flow','cash_conversion'] as const:[])]} unit={unit} label="Cash flow analysis"/></>}
      {activeSection==='profitability'&&<>{panels(['profitability'])}<FinancialTable rows={rows} fields={ratios} unit={unit} label="Profitability"/></>}
      {activeSection==='health'&&<>{panels(data.profile==='bank'?['bank_funding','bank_quality']:['liquidity'])}<FinancialTable rows={rows} fields={data.profile==='bank'?['customer_demand_deposits','classified_loans','classified_nonperforming_loans','classified_loan_allowance','demand_deposit_share','npl_classified_ratio','classified_loan_coverage']:['current_ratio','quick_ratio','debt_equity','liabilities_assets']} unit={unit} label="Financial health"/>{data.profile==='bank'&&<p className="stock-note">{t('Loan quality ratios use classified loans and matching allowances, excluding securities margin lending. Demand-deposit share is an accounting definition, not vendor CASA. NIM remains unavailable.')}</p>}</>}
      {activeSection==='valuation'&&<><FundamentalOverview data={data} unit={unit} groups={['valuation']}/><p className="stock-note">{t('No price or market-cap comparison is added without compatible dated valuation inputs.')}</p></>}
      {activeSection==='statements'&&<section aria-label={t('Financial statements')}><div className="mb-4 flex flex-wrap gap-2" role="group" aria-label={t('Statement type')}>{Object.entries(statementLabels).map(([key,label])=><Button key={key} size="sm" variant={statement===key?'secondary':'outline'} aria-pressed={statement===key} onClick={()=>setStatement(key as keyof typeof statementLabels)}>{t(label)}</Button>)}</div>{frequency==='ttm'&&<p className="mb-3 text-xs text-muted-foreground">{t('Statement tables show original quarterly reports, not synthetic TTM statements.')}</p>}{statementPeriods.length?<FinancialStatementTable periods={statementPeriods} unit={unit} label={statementLabels[statement]}/>:<p className="stock-note">{t('This statement is unavailable for the selected periods.')}</p>}</section>}
      {activeSection==='sources'&&<section aria-label={t('Documents and sources')}><h3 className="text-sm font-semibold">{t('Documents and sources')}</h3><p className="stock-note">{t(data.display_scope==='internal_research'?data.source_version==='reviewed-report-v2'?'Selected original report fields verified against saved PDF pages. Publication timing and public rights remain separate.':'Original filing page evidence; selected fields only. PDF binary and visual verification remain unavailable.':'Provider receipts are available evidence, not original issuer filings. No filing document is invented.')}</p><details open className="border-t pt-3 text-xs text-muted-foreground"><summary className="cursor-pointer font-medium">{t('Financial source and coverage')}</summary><dl className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-2"><div><dt>{t('Source')}</dt><dd>{data.source} · {data.source_version}</dd></div><div><dt>{t('Read at')}</dt><dd>{date(data.read_at,true)} · {t(data.display_scope==='personal_research'?'Saved personal research; not current data.':data.display_scope==='internal_research'?'Saved filing review; not current market data.':'Provider or process cache; not a publication timestamp.')}</dd></div><div><dt>{t('Report basis')}</dt><dd>{ui(consolidationLabel(data.fundamental_summary?.consolidation??data.consolidation))}</dd></div><div><dt>{t('Publication date')}</dt><dd>{t('Source dates are shown as reported, without inferred timezone.')}</dd></div><div><dt>{t('Statement coverage')}</dt><dd>{Object.entries(statementLabels).map(([key,label])=><span className="block" key={key}>{t(label)}: {data.statements?.[key]?.periods.length||0} · {ui(data.statements?.[key]?.status||'unavailable')}</span>)}</dd></div></dl>
        {data.source_receipts?.map(receipt=><details key={receipt.statement} className="mt-4 border-t pt-2"><summary className="cursor-pointer">{ui(statementLabels[receipt.statement as keyof typeof statementLabels])} · {ui(receipt.status)}</summary><p className="mt-2">{t('Observed at')}: {date(receipt.observed_at,true)}</p><p className="mt-1 break-all">{financialSourceLink(receipt.source_url)?<a href={financialSourceLink(receipt.source_url)} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2">{receipt.source_url}</a>:receipt.source_url}</p><p className="mt-1 break-all">SHA-256: {receipt.content_sha256||'—'}</p>{receipt.periods.filter(period=>rows.some(row=>row.period===period.period)).map(period=><div key={period.period} className="mt-2"><p>{period.period} · {ui(period.basis)} · {t('Publication date')}: {period.source_dates.publicDate||'—'} · {period.diagnostics.join(', ')}</p>{period.source_context&&<details className="mt-1"><summary className="cursor-pointer">{t('Statement provenance')}</summary><p className="mt-1">{t('Source metadata is evidence, not filing verification or display permission.')}</p><pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap break-all text-[10px]">{JSON.stringify(period.source_context,null,2)}</pre></details>}</div>)}</details>)}
        <details className="mt-4 border-t pt-2"><summary className="cursor-pointer">{t('Calculation evidence')}</summary><p className="mt-2">{t('ROE uses total profit and average total equity, not parent-shareholder ROE.')}</p>{Object.entries(latest?.calculations||{}).map(([metric,evidence])=><details key={metric} className="mt-3"><summary className="cursor-pointer">{ui(FINANCIAL_LABELS[metric as FinancialKey]||metric)}{evidence.reason?' · '+ui(evidence.reason):''}</summary><p className="mt-1">{evidence.formula}</p><pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap break-all text-[10px]">{JSON.stringify(evidence.inputs,null,2)}</pre></details>)}</details>
        {!!data.reconciliations?.length&&<details className="mt-4 border-t pt-2"><summary className="cursor-pointer">{t('Annual / quarterly differences')}</summary><p className="mt-2">{t('Differences retain source versions; no cause is inferred.')}</p>{data.reconciliations.map(item=><p className="mt-2" key={`${item.statement}-${item.period}-${item.field}`}>{item.period} · {ui(FINANCIAL_LABELS[item.field as FinancialKey]||item.field)} · {t('Annual')}: {number(item.annual_reported/unitDivisor[unit])} · {t('Quarter sum')}: {number(item.quarter_sum/unitDivisor[unit])} · {t('Absolute change')}: {number(item.difference/unitDivisor[unit])} {ui(unitLabels[unit])}</p>)}</details>}
        <ul className="mt-3 space-y-1">{data.limitations?.map(value=><li key={value}>{ui(value)}</li>)}</ul>
      </details></section>}
    </>}
  </section>;
}

export function FinancialHeadlines({data,rows,unit}:{data:FundamentalResearch;rows:FundamentalPeriod[];unit:AmountUnit}){
 const {ui,number,percent}=useLocale();const latest=rows.at(-1);if(!latest)return null;
 const states=data.verification?.periods.find(p=>p.period===latest.period)?.metrics;
 const keys:FinancialKey[]=[data.profile==='bank'?'operating_income':'revenue','net_profit',data.profile==='bank'?'operating_income_growth_yoy':'revenue_growth_yoy','roe','total_assets','cash_operating'];
 const visible=keys.filter(k=>typeof latest[k]==='number'&&Number.isFinite(latest[k])&&(states?states[k]?.display_eligible:data.fundamental_summary?.metrics.some(m=>m.key===k&&m.value===latest[k]&&['QUALIFIED','SOURCE_REPORTED','DEMO'].includes(m.status))));
 if(!visible.length)return null;
 return <dl className="grid min-w-0 grid-cols-2 gap-x-5 gap-y-3 border-y py-4 lg:grid-cols-3" aria-label={ui('Financial highlights')}>{visible.map(key=><div className="min-w-0" key={key}><dt className="text-xs text-muted-foreground">{ui(FINANCIAL_LABELS[key])} · {latest.period}</dt><dd className="financial mt-1 break-words text-lg font-semibold">{key==='roe'||key.includes('growth')?percent(latest[key]):formatFinancialAmount(latest[key]!,unitDivisor[unit],unit==='vnd'?0:2,number)+' '+ui(unitLabels[unit])}</dd><dd className="mt-1 text-[10px] text-muted-foreground">{ui(states?.[key]?.dimensions?.ACCOUNTING_VERIFIED?'Accounting compatibility':data.is_fixture?'Synthetic financial evidence':'SOURCE_REPORTED')}</dd></div>)}</dl>;
}
