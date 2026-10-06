"use client";
import {useEffect,useRef,useState} from 'react';
import Link from 'next/link';
import {useTheme} from 'next-themes';
import {createChart,CandlestickSeries,HistogramSeries,ColorType} from 'lightweight-charts';
import {rangeDates,type Range} from '@/lib/chart-data';
import {indexMovement,indexAggregate,indexDate,signedIndex,type IndexSnapshot} from '@/lib/marketIndex';
import {Button} from '@/app/components/ui/button';
type IndexBar={date:string;open:number;high:number;low:number;close:number;volume:number;source:string};
export default function IndexResearch(){
  const [snapshot,setSnapshot]=useState<IndexSnapshot|null>(null);
  const [rows,setRows]=useState<IndexBar[]>([]);const [selected,setSelected]=useState<IndexBar|null>(null);
  const [range,setRange]=useState<Range>('3M');const [attempt,setAttempt]=useState(0);
  const [loading,setLoading]=useState(true);const [error,setError]=useState(false);const [summaryError,setSummaryError]=useState(false);
  const host=useRef<HTMLDivElement>(null);const {resolvedTheme}=useTheme();
  useEffect(()=>{const controller=new AbortController();
    fetch('/api/stocks/index-snapshot',{signal:controller.signal,cache:'no-store'}).then(async r=>{if(!r.ok)throw Error();return r.json();}).then(row=>{if(!controller.signal.aborted){setSnapshot(row);setSummaryError(false);}}).catch(()=>{if(!controller.signal.aborted)setSummaryError(true);});
    return()=>controller.abort();
  },[attempt]);
  useEffect(()=>{const controller=new AbortController();setLoading(true);setError(false);setRows([]);setSelected(null);
    fetch('/api/stocks/index-history?'+new URLSearchParams(rangeDates(range)),{signal:controller.signal}).then(async r=>{if(!r.ok)throw Error();return r.json();}).then(data=>{if(!controller.signal.aborted)setRows(data);}).catch(()=>{if(!controller.signal.aborted)setError(true);}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return()=>controller.abort();
  },[range,attempt]);
  useEffect(()=>{if(!host.current||!rows.length)return;
    const chart=createChart(host.current,{autoSize:true,height:430,layout:{background:{type:ColorType.Solid,color:'transparent'},textColor:resolvedTheme==='dark'?'#cbd5e1':'#475569'},grid:{vertLines:{visible:false},horzLines:{color:resolvedTheme==='dark'?'#25313c':'#e2e8f0'}},localization:{locale:'en-GB'},timeScale:{timeVisible:false},handleScroll:{vertTouchDrag:false}});
    const candles=chart.addSeries(CandlestickSeries,{upColor:'#10b981',downColor:'#ef4444',borderVisible:false,wickUpColor:'#10b981',wickDownColor:'#ef4444',priceFormat:{type:'price',precision:2,minMove:0.01}},0);
    const volume=chart.addSeries(HistogramSeries,{priceFormat:{type:'volume'},priceLineVisible:false,lastValueVisible:false},1);
    candles.setData(rows.map(row=>({time:row.date,...row})));volume.setData(rows.map(row=>({time:row.date,value:row.volume,color:row.close>=row.open?'#10b98180':'#ef444480'})));chart.panes()[1].setHeight(100);chart.timeScale().fitContent();
    chart.subscribeCrosshairMove(event=>setSelected(rows.find(row=>row.date===String(event.time))||null));
    return()=>chart.remove();
  },[rows,resolvedTheme]);
  const movement=indexMovement(snapshot);const bar=selected||rows.at(-1);
  return <div className="page-stack"><header><Link className="text-xs text-primary" href="/">← Explore</Link><h1 className="mt-3">VN-Index research</h1><p className="mt-2 text-sm text-muted-foreground">Daily index movement and trading activity.</p></header>
    {snapshot&&<section aria-label="Latest index summary" className="flex flex-wrap gap-x-8 gap-y-4 border-y py-4 text-sm tabular-nums"><div><p className="text-xs text-muted-foreground">Latest level · {indexDate(snapshot.trading_date)}</p><p className={`mt-1 text-2xl font-semibold ${movement.color}`}>{snapshot.level.toLocaleString('en-GB',{minimumFractionDigits:2})}</p><p className={movement.color}>{movement.label} · {signedIndex(snapshot.change)} pts · {signedIndex(snapshot.change_percent,'%')}</p></div><div><p className="text-xs text-muted-foreground">Total trading volume</p><p className="mt-2">{indexAggregate(snapshot.total_volume,'shares')}</p></div><div><p className="text-xs text-muted-foreground">Total trading value</p><p className="mt-2">{indexAggregate(snapshot.total_value,'VND')}</p></div></section>}
    {summaryError&&<p role="alert">Latest index summary unavailable. <button className="text-primary" onClick={()=>setAttempt(v=>v+1)}>Retry</button></p>}
    <section aria-label="Index history"><div className="flex flex-wrap items-center justify-between gap-3"><h2>Daily movement</h2><div className="flex gap-1">{(['3M','6M','1Y','2Y'] as Range[]).map(value=><Button key={value} variant={range===value?'secondary':'ghost'} size="sm" aria-pressed={range===value} onClick={()=>setRange(value)}>{value}</Button>)}</div></div>
      {bar&&<div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs tabular-nums"><span>{indexDate(bar.date)}</span>{(['open','high','low','close'] as const).map(key=><span key={key} className="capitalize">{key} {bar[key].toLocaleString('en-GB',{minimumFractionDigits:2})}</span>)}<span>Volume {indexAggregate(bar.volume,'shares')}</span></div>}
      {loading&&<p role="status" className="py-8">Loading index history…</p>}{error&&<p role="alert" className="py-8">Index history unavailable. <button className="text-primary" onClick={()=>setAttempt(v=>v+1)}>Retry</button></p>}{!loading&&!error&&!rows.length&&<p className="py-8 text-muted-foreground">No index history for this range.</p>}
      <div ref={host} className="mt-4 min-w-0"/>
      <details className="mt-4 text-xs text-muted-foreground"><summary className="cursor-pointer">Data evidence</summary><p className="mt-2">Source: {snapshot?.source||rows[0]?.source||'Unavailable'} · {rows.length} completed daily sessions in the selected range. Latest summary retrieved: {snapshot?new Date(snapshot.fetched_at).toLocaleString('en-GB'):'Unavailable'}. Index levels are points; trading value is VND. Historical value is not supplied by the daily OHLC endpoint.</p></details>
    </section></div>;
}
