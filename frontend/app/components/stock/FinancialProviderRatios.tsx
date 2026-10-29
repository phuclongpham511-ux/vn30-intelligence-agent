"use client";
import {useEffect,useMemo,useState} from 'react';
import {CartesianGrid,Line,LineChart,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';
import {useLocale} from '@/lib/i18n';
import {useChartMotion} from '@/lib/chart-motion';
import type {FinancialFrequency} from '@/lib/types';

type RatioRow={metric_id:string;label:string|null;values:Record<string,number|null>};
type RatioData={contract:'vnstock-ratio-response-v1';ticker:string;frequency:'annual'|'quarterly';source:'KBS';periods:string[];rows:RatioRow[]};

function parseRatioData(value:unknown,ticker:string,frequency:'annual'|'quarterly'):RatioData{
 if(!value||typeof value!=='object')throw Error('Invalid ratio response');
 const data=value as RatioData,periodPattern=frequency==='annual'?/^\d{4}$/:/^\d{4}-Q[1-4]$/;
 if(data.contract!=='vnstock-ratio-response-v1'||data.ticker!==ticker||data.frequency!==frequency||data.source!=='KBS'||!Array.isArray(data.periods)||data.periods.length>8||!Array.isArray(data.rows)||data.rows.length>100)throw Error('Invalid ratio response');
 if(new Set(data.periods).size!==data.periods.length||data.periods.some(period=>!periodPattern.test(period)))throw Error('Invalid ratio periods');
 const ids=new Set<string>();
 for(const row of data.rows){
  if(!row||typeof row.metric_id!=='string'||!row.metric_id||ids.has(row.metric_id)||row.label!==null&&typeof row.label!=='string'||!row.values||typeof row.values!=='object')throw Error('Invalid ratio metric');
  ids.add(row.metric_id);
  if(Object.keys(row.values).some(period=>!data.periods.includes(period))||data.periods.some(period=>row.values[period]!==undefined&&row.values[period]!==null&&(typeof row.values[period]!=='number'||!Number.isFinite(row.values[period]))))throw Error('Invalid ratio value');
 }
 return data;
}

export default function FinancialProviderRatios({ticker,frequency}:{ticker:string;frequency:FinancialFrequency}){
 const {t,number}=useLocale(),animate=useChartMotion();
 const [data,setData]=useState<RatioData|null>(null),[metricId,setMetricId]=useState(''),[loading,setLoading]=useState(false);
 useEffect(()=>{
  if(frequency==='ttm'){setData(null);setLoading(false);return;}
  const controller=new AbortController();let disposed=false;setLoading(true);setData(null);
  fetch(`/api/personal-research/financial-ratios/${encodeURIComponent(ticker)}?frequency=${frequency}`,{cache:'no-store',signal:controller.signal})
   .then(async response=>{if(!response.ok)throw Error('Ratio data unavailable');return parseRatioData(await response.json(),ticker,frequency);})
   .then(value=>{if(!disposed){setData(value);setMetricId(current=>value.rows.some(row=>row.metric_id===current)?current:value.rows.find(row=>Object.values(row.values).some(item=>item!==null))?.metric_id||'');}})
   .catch(()=>{if(!disposed)setData(null);}).finally(()=>{if(!disposed)setLoading(false);});
  return()=>{disposed=true;controller.abort();};
 },[ticker,frequency]);
 const periods=useMemo(()=>[...(data?.periods||[])].sort(),[data]);
 const selected=data?.rows.find(row=>row.metric_id===metricId)||data?.rows.find(row=>Object.values(row.values).some(value=>value!==null));
 const availableMetrics=data?.rows.filter(row=>Object.values(row.values).some(value=>value!==null)).length||0;
 const availablePeriods=periods.filter(period=>data?.rows.some(row=>row.values[period]!==null)).length;
 const points=periods.map(period=>({period,value:selected?.values[period]??null}));
 if(frequency==='ttm')return null;
 return <section className="min-w-0 space-y-3 border-t pt-4" aria-label={t('Vnstock financial indicators')} aria-busy={loading}>
  <header className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-semibold">{t('Vnstock financial indicators')}</h3>{data&&<span className="text-[11px] text-muted-foreground">{data.source} · {availableMetrics} · {availablePeriods}</span>}</header>
  {loading&&!data?<p className="financial-series-unavailable">{t('Loading financial statements')}</p>:!data||!selected?<p className="financial-series-unavailable">{t('Unavailable')}</p>:<>
   <label className="sr-only" htmlFor={`ratio-metric-${ticker}`}>{t('Financial indicator')}</label>
   <select id={`ratio-metric-${ticker}`} className="max-w-full rounded-md border bg-background px-3 py-2 text-sm" value={selected.metric_id} onChange={event=>setMetricId(event.target.value)}>
    {data.rows.map(row=><option key={row.metric_id} value={row.metric_id}>{row.label||row.metric_id}</option>)}
   </select>
   <div className="financial-research-chart-canvas min-w-0" data-financial-chart="provider-ratio"><ResponsiveContainer width="100%" height="100%" minWidth={0}>
    <LineChart data={points} margin={{top:12,right:12,left:4,bottom:8}} accessibilityLayer><CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 5"/><XAxis dataKey="period" tick={{fill:'var(--muted-foreground)',fontSize:11}} axisLine={false} tickLine={false} minTickGap={10} tickMargin={9}/><YAxis tick={{fill:'var(--muted-foreground)',fontSize:11}} width={64} tickFormatter={value=>number(value)} axisLine={false} tickLine={false}/><Tooltip cursor={{stroke:'var(--border)',strokeDasharray:'3 4'}} filterNull content={({active,payload,label})=>!active||!payload?.length?null:<div className="financial-chart-tooltip" role="status"><p className="mb-1 font-semibold">{String(label)}</p><strong>{number(payload[0].value)}</strong></div>}/><Line dataKey="value" name={selected.label||selected.metric_id} stroke="var(--chart)" strokeWidth={2.5} dot={{r:2.5,strokeWidth:0}} activeDot={{r:5,stroke:'var(--card)',strokeWidth:2}} connectNulls={false} isAnimationActive={animate} animationDuration={560} animationEasing="ease-out"/></LineChart>
   </ResponsiveContainer></div>
   <div className="fundamental-table-scroll" role="region" aria-label={selected.label||selected.metric_id} tabIndex={0}><table className="fundamental-table text-xs"><thead><tr>{periods.map(period=><th scope="col" key={period}>{period}</th>)}</tr></thead><tbody><tr>{periods.map(period=><td key={period}>{selected.values[period]===null||selected.values[period]===undefined?'—':number(selected.values[period])}</td>)}</tr></tbody></table></div>
  </>}
 </section>;
}
