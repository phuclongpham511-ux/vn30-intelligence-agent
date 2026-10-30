"use client";
import {useState} from 'react';
import {ResponsiveContainer,ComposedChart,Bar,Line,XAxis,YAxis,CartesianGrid,Tooltip,ReferenceLine} from 'recharts';
import {useLocale} from '@/lib/i18n';
import {FINANCIAL_LABELS,availableSeries,type FinancialKey} from '@/lib/fundamental-data';
import {financialChartRows,unitDivisor,unitLabels,type AmountUnit} from '@/lib/fundamental-research';
import type {FundamentalPeriod} from '@/lib/types';
import {useChartMotion} from '@/lib/chart-motion';

const colors=['var(--chart)','var(--chart-secondary)','var(--ma20)'];
const axis={fill:'var(--muted-foreground)',fontSize:11};

export default function FinancialResearchChart({rows,fields,title,percentage=false,unit,visible=true,chartRows,frequency='annual'}:{rows:FundamentalPeriod[];fields:readonly FinancialKey[];title:string;percentage?:boolean;unit:AmountUnit;visible?:boolean;chartRows?:FundamentalPeriod[];frequency?:string}){
  const {ui,t,number,percent}=useLocale();
  const animate=useChartMotion();
  const available=availableSeries(rows,fields);
  const [hidden,setHidden]=useState<Set<FinancialKey>>(()=>new Set());
  const selected=available.filter(key=>!hidden.has(key));
  const values=chartRows??financialChartRows(rows);
  const format=(value:unknown)=>percentage?percent(value):typeof value==='number'?number(value/unitDivisor[unit],unit==='vnd'?0:2):'—';
  return <article className="min-w-0 border-t pt-4" aria-label={ui(title)}>
    <div className="mb-3 flex flex-wrap items-start justify-between gap-2"><div><h3 className="text-sm font-semibold">{ui(title)}</h3><p className="mt-1 text-[11px] text-muted-foreground">{percentage?frequency==='annual'?t('Percent · Comparable annual periods'):t('Percent · Comparable reporting periods'):ui(unitLabels[unit])}</p></div>
      <div className="financial-chart-legend flex flex-wrap gap-2" role="group" aria-label={t('Chart series')}>{available.map((key,index)=><button key={key} type="button" aria-pressed={!hidden.has(key)} onClick={()=>setHidden(current=>{const next=new Set(current);if(next.has(key))next.delete(key);else next.add(key);return next;})} className={`inline-flex min-h-7 items-center gap-2 rounded-md border px-2 py-1 text-[11px] focus-visible:outline-2 focus-visible:outline-ring ${hidden.has(key)?'opacity-45':'text-muted-foreground'}`}><span aria-hidden="true" className="h-2 w-2 shrink-0 rounded-sm" style={{background:colors[index]}}/>{ui(FINANCIAL_LABELS[key])}{percentage?' · %':''}</button>)}</div>
    </div>
    {!visible?null:!available.length?<p className="financial-series-unavailable">{t('No supported series for these periods.')}</p>:!selected.length?<p className="financial-series-unavailable">{t('Select a series to view the chart.')}</p>:<div className="financial-research-chart-canvas min-w-0" data-financial-chart={percentage?'percent':'amount'}><ResponsiveContainer width="100%" height="100%" minWidth={0}>
      <ComposedChart data={values} margin={{top:14,right:12,left:4,bottom:8}} accessibilityLayer>
        <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 5"/><XAxis dataKey="period" tick={axis} axisLine={false} tickLine={false} minTickGap={10} tickMargin={9}/><YAxis tick={axis} width={60} tickFormatter={format} axisLine={false} tickLine={false}/>
        <Tooltip cursor={{fill:'var(--muted)',fillOpacity:.3}} filterNull content={({active,payload,label})=>{if(!active||!payload?.length)return null;return <div className="financial-chart-tooltip" role="status" aria-live="polite"><p className="mb-1 font-semibold">{String(label)}</p>{payload.map((entry,index)=><p className="flex items-center justify-between gap-4" key={`${String(entry.dataKey)}-${index}`}><span>{String(entry.name)}</span><strong className="font-semibold">{format(entry.value)}{percentage?'%':' '+ui(unitLabels[unit])}</strong></p>)}</div>}}/>
        <ReferenceLine y={0} stroke="var(--border)" strokeDasharray="3 4"/>
        {selected.map(key=>{const index=available.indexOf(key)%colors.length;return percentage?<Line key={key} dataKey={key} name={ui(FINANCIAL_LABELS[key])} stroke={colors[index]} strokeWidth={2.5} dot={{r:2.5,strokeWidth:0}} activeDot={{r:5,stroke:'var(--card)',strokeWidth:2}} connectNulls={false} isAnimationActive={animate} animationDuration={560} animationEasing="ease-out"/>:<Bar key={key} dataKey={key} name={ui(FINANCIAL_LABELS[key])} fill={colors[index]} maxBarSize={42} radius={[3,3,0,0]} isAnimationActive={animate} animationDuration={560} animationEasing="ease-out"/>;})}
      </ComposedChart>
    </ResponsiveContainer></div>}
  </article>;
}
