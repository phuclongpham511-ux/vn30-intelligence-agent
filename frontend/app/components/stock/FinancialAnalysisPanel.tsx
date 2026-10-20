"use client";
import {useState} from 'react';
import {ResponsiveContainer,ComposedChart,Bar,Line,XAxis,YAxis,CartesianGrid,Tooltip,ReferenceLine} from 'recharts';
import {useLocale} from '@/lib/i18n';
import type {FinancialPanel} from '@/lib/types';
import {panelTitles} from '@/lib/financial-panels';
import {unitDivisor,unitLabels,type AmountUnit} from '@/lib/fundamental-research';

const colors=['var(--chart)','var(--chart-secondary)','var(--ma20)','var(--ma50)'];
const axis={fill:'var(--muted-foreground)',fontSize:11};

/** Only the backend-qualified projection enters a chart. Null stays a gap. */
export default function FinancialAnalysisPanel({panel,kind,unit,visible=true,isFixture=false,personalResearch=false,onSources}:{panel?:FinancialPanel;kind:FinancialPanel['key'];unit:AmountUnit;visible?:boolean;isFixture?:boolean;personalResearch?:boolean;onSources?:()=>void}){
 const {t,ui,number,percent}=useLocale();
 const [hidden,setHidden]=useState<Set<string>>(()=>new Set());
 const series=panel?.series||[],selected=series.filter(s=>!hidden.has(s.key));
 const title=kind==='growth'&&series.some(s=>s.key==='operating_income')?'Operating income and profit trends':panelTitles[kind];
 const safeRows=panel?.rows.map(r=>({...r,values:Object.fromEntries(series.map(s=>{const value=r.values[s.key],status=r.statuses[s.key];const allowed=status==='SOURCE_REPORTED'&&personalResearch&&!isFixture&&panel?.status==='SOURCE_REPORTED'||status==='QUALIFIED'&&!isFixture&&['consolidated','standalone'].includes(r.bases[s.key]||'')||status==='DEMO'&&isFixture;return [s.key,allowed&&typeof value==='number'&&Number.isFinite(value)?value:null];}))}));
 const hasValues=safeRows?.some(r=>selected.some(s=>r.values[s.key]!==null));
 const format=(value:unknown,metricUnit:string)=>typeof value!=='number'||!Number.isFinite(value)?'—':metricUnit==='fraction'?percent(value):metricUnit==='multiple'?number(value)+'×':number(value/unitDivisor[unit],unit==='vnd'?0:2);
 const points=safeRows?.map(row=>({period:row.period,...row.values}));
 const status=panel?.status||'UNAVAILABLE';
 const selectedHasRatio=selected.some(s=>s.unit!=='VND');
 const rateUnit=selected.find(s=>s.unit!=='VND')?.unit||'fraction';
 const selectedHasAmount=selected.some(s=>s.unit==='VND');
 return <article className="financial-analysis-panel" aria-label={ui(title)} data-financial-panel={kind} data-chart-availability={hasValues?'available':'unavailable'}>
  <header className="flex flex-wrap items-start justify-between gap-2"><div><h3 className="text-sm font-semibold">{ui(title)}</h3><p className="mt-1 text-[11px] text-muted-foreground">{kind==='pe'||kind==='pb'?t('Multiple (×)'):selectedHasRatio&&!selectedHasAmount?(rateUnit==='multiple'?ui('Multiple (×)'):'%'):ui(unitLabels[unit])}{selectedHasRatio&&selectedHasAmount?' · '+(rateUnit==='multiple'?'×':'%'):''} · {panel?ui(panel.frequency==='annual'?'Annual':panel.frequency==='quarterly'?'Quarterly':'TTM'):'—'}</p></div><span className="financial-qualification" data-financial-qualification={status}>{ui(status)}</span></header>
  <details className="financial-chart-method"><summary>{t('Chart method & source')}</summary><p>{panel?ui(panel.methodology):t('The qualified chart projection is unavailable. No values are inferred from raw evidence.')}</p>{panel&&<p>{panel.source}</p>}</details>
  {panel?.partial&&<p className="mb-3 text-[11px] font-medium text-muted-foreground">{t('Partial coverage; missing components and periods are not zero.')}</p>}
  <div className="mb-3 flex flex-wrap gap-3" role="group" aria-label={t('Chart series')}>{series.map((s,i)=><button type="button" key={s.key} aria-pressed={!hidden.has(s.key)} onClick={()=>setHidden(before=>{const next=new Set(before);if(next.has(s.key))next.delete(s.key);else next.add(s.key);return next;})} className={`inline-flex items-center gap-1.5 rounded text-[11px] focus-visible:outline-2 focus-visible:outline-ring ${hidden.has(s.key)?'opacity-50':''}`}><span className="h-2 w-2 rounded-sm" aria-hidden="true" style={{background:colors[i%colors.length]}}/>{ui(s.label)}{s.unit==='fraction'?' · %':''}</button>)}</div>
  {!visible?null:!hasValues?<div className="financial-chart-unavailable" role="note"><p>{selected.length||!series.length?t(status==='UNQUALIFIED'?'Inputs exist, but reporting basis, provenance or display rights are not qualified.':'No qualified observations are available for this chart.'):t('Select a series to view the chart.')}</p>{!!panel?.reasons.length&&<details className="mt-2"><summary className="cursor-pointer">{t('Qualification details')}</summary><ul className="mt-2 space-y-1">{panel.reasons.map(reason=><li key={reason}>{ui(reason)}</li>)}</ul></details>}{onSources&&<button type="button" className="text-primary underline" onClick={onSources}>{t('Inspect financial sources')}</button>}</div>:<div className="h-72 min-w-0" data-financial-chart={panel?.chart}><ResponsiveContainer width="100%" height="100%" minWidth={0}><ComposedChart data={points} margin={{top:8,right:0,left:0,bottom:0}} accessibilityLayer>
   <CartesianGrid vertical={false} stroke="var(--border)"/><XAxis dataKey="period" tick={axis} axisLine={false} tickLine={false} minTickGap={12}/>{selectedHasAmount&&<YAxis yAxisId="amount" tick={axis} width={64} tickFormatter={v=>format(v,'VND')} axisLine={false} tickLine={false}/>} {selectedHasRatio&&<YAxis yAxisId="rate" orientation={selectedHasAmount?'right':'left'} tick={axis} width={52} tickFormatter={v=>format(v,rateUnit)} axisLine={false} tickLine={false}/>}
   <Tooltip contentStyle={{background:'var(--card)',color:'var(--foreground)',border:'1px solid var(--border)',fontSize:12,maxWidth:'min(320px, 80vw)',overflowWrap:'anywhere'}} filterNull formatter={(value,name,entry)=>{const s=series.find(s=>s.key===entry.dataKey);return [format(value,s?.unit||'VND')+(s?.unit==='VND'?' '+ui(unitLabels[unit]):''),String(name)];}}/>
   <ReferenceLine yAxisId={selectedHasAmount?'amount':'rate'} y={0} stroke="var(--border)"/>
   {selected.map(s=>{const color=colors[series.indexOf(s)%colors.length];return s.unit!=='VND'?<Line key={s.key} yAxisId="rate" dataKey={s.key} name={ui(s.label)} stroke={color} strokeWidth={2} dot={{r:2}} connectNulls={false} isAnimationActive={false}/>:<Bar key={s.key} yAxisId="amount" stackId={panel?.chart==='stacked'?'components':undefined} dataKey={s.key} name={ui(s.label)} fill={color} maxBarSize={42} isAnimationActive={false}/>;})}
  </ComposedChart></ResponsiveContainer></div>}
  {hasValues&&!!panel?.reasons.length&&<details className="mt-2 text-[11px] text-muted-foreground"><summary className="cursor-pointer">{t('Qualification details')}</summary><ul className="mt-2 space-y-1">{panel.reasons.map(reason=><li key={reason}>{ui(reason)}</li>)}</ul></details>}
  {panel&&<footer className="mt-3 border-t pt-2 text-[11px] text-muted-foreground">{panel.source} · {panel.rows[0]?.period||'—'}–{panel.rows.at(-1)?.period||'—'}<details className="mt-2"><summary className="cursor-pointer">{t('Chart observations')}</summary><div className="fundamental-table-scroll mt-2" tabIndex={0} role="region" aria-label={t('Chart observations')}><table className="fundamental-table text-xs"><caption className="sr-only">{ui(title)}</caption><thead><tr><th scope="col">{t('Reporting period')}</th>{series.map(s=><th scope="col" key={s.key}>{ui(s.label)}</th>)}</tr></thead><tbody>{safeRows?.map(r=><tr key={r.period}><th scope="row">{r.period}</th>{series.map(s=><td key={s.key}>{format(r.values[s.key],s.unit)}<span className="block text-[10px]">{ui(r.statuses[s.key])}</span></td>)}</tr>)}</tbody></table></div></details></footer>}
 </article>;
}
