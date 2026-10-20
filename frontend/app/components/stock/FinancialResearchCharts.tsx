"use client";
import {useState} from 'react';
import {ResponsiveContainer,ComposedChart,Bar,Line,XAxis,YAxis,CartesianGrid,Tooltip,ReferenceLine} from 'recharts';
import {useLocale} from '@/lib/i18n';
import {FINANCIAL_LABELS,availableSeries,type FinancialKey} from '@/lib/fundamental-data';
import {financialChartRows,unitDivisor,unitLabels,type AmountUnit} from '@/lib/fundamental-research';
import type {FundamentalPeriod} from '@/lib/types';

const colors=['var(--chart)','var(--chart-secondary)','var(--ma20)'];
const axis={fill:'var(--muted-foreground)',fontSize:11};
const tip={background:'var(--card)',border:'1px solid var(--border)',borderRadius:6,color:'var(--foreground)',fontSize:12,maxWidth:'min(320px, 80vw)',overflowWrap:'anywhere' as const};

export default function FinancialResearchChart({rows,fields,title,percentage=false,unit,visible=true,chartRows,frequency='annual'}:{rows:FundamentalPeriod[];fields:readonly FinancialKey[];title:string;percentage?:boolean;unit:AmountUnit;visible?:boolean;chartRows?:FundamentalPeriod[];frequency?:string}){
  const {ui,t,number,percent}=useLocale();
  const available=availableSeries(rows,fields);
  const [hidden,setHidden]=useState<Set<FinancialKey>>(()=>new Set());
  const selected=available.filter(key=>!hidden.has(key));
  const values=chartRows??financialChartRows(rows);
  const format=(value:unknown)=>percentage?percent(value):typeof value==='number'?number(value/unitDivisor[unit],unit==='vnd'?0:2):'—';
  return <article className="min-w-0 border-t pt-4" aria-label={ui(title)}>
    <div className="mb-3 flex flex-wrap items-start justify-between gap-2"><div><h3 className="text-sm font-semibold">{ui(title)}</h3><p className="mt-1 text-[11px] text-muted-foreground">{percentage?frequency==='annual'?t('Percent · Comparable annual periods'):t('Percent · Comparable reporting periods'):ui(unitLabels[unit])}</p></div>
      <div className="flex flex-wrap gap-x-3 gap-y-2" role="group" aria-label={t('Chart series')}>{available.map((key,index)=><button key={key} type="button" aria-pressed={!hidden.has(key)} onClick={()=>setHidden(current=>{const next=new Set(current);if(next.has(key))next.delete(key);else next.add(key);return next;})} className={`inline-flex items-center gap-1.5 rounded-sm text-[11px] focus-visible:outline-2 focus-visible:outline-ring ${hidden.has(key)?'opacity-40':'text-muted-foreground'}`}><span aria-hidden="true" className="h-2 w-2 rounded-sm" style={{background:colors[index]}}/>{ui(FINANCIAL_LABELS[key])}</button>)}</div>
    </div>
    {!visible?null:!available.length?<p className="financial-series-unavailable">{t('No supported series for these periods.')}</p>:!selected.length?<p className="financial-series-unavailable">{t('Select a series to view the chart.')}</p>:<div className="h-64 min-w-0" data-financial-chart={percentage?'percent':'amount'}><ResponsiveContainer width="100%" height="100%" minWidth={0}>
      <ComposedChart data={values} margin={{top:8,right:8,left:0,bottom:0}} accessibilityLayer>
        <CartesianGrid vertical={false} stroke="var(--border)"/><XAxis dataKey="period" tick={axis} axisLine={false} tickLine={false} minTickGap={8}/><YAxis tick={axis} width={60} tickFormatter={format} axisLine={false} tickLine={false}/>
        <Tooltip contentStyle={tip} cursor={{fill:'var(--muted)',fillOpacity:.35}} formatter={(value:unknown,name:unknown)=>[format(value)+(percentage?'':' '+ui(unitLabels[unit])),String(name)]} filterNull/>
        <ReferenceLine y={0} stroke="var(--border)"/>
        {selected.map(key=>{const index=available.indexOf(key)%colors.length;return percentage?<Line key={key} dataKey={key} name={ui(FINANCIAL_LABELS[key])} stroke={colors[index]} strokeWidth={2} dot={{r:3}} connectNulls={false} isAnimationActive={false}/>:<Bar key={key} dataKey={key} name={ui(FINANCIAL_LABELS[key])} fill={colors[index]} maxBarSize={38} radius={[2,2,0,0]} isAnimationActive={false}/>;})}
      </ComposedChart>
    </ResponsiveContainer></div>}
  </article>;
}
