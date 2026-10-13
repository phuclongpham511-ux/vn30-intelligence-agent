"use client";
import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import {useLiveMarket} from '@/lib/useLiveMarket';
import {movement,type LiveBatch} from '@/lib/live-market';
import {useLocale} from '@/lib/i18n';
import {quoteStatus} from '@/lib/newsPresentation';

const Context=createContext<{data:LiveBatch|null;failed:boolean}>({data:null,failed:false});
export function LivePrices({symbols,interval,children}:{symbols:string[];interval:number;children:ReactNode}) {
  const value=useLiveMarket(symbols,interval);
  const [,setClock]=useState(0);
  useEffect(()=>{const timer=setInterval(()=>setClock(n=>n+1),30000);return()=>clearInterval(timer);},[]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function LivePrice({symbol,prominent=false,showSession=false,compact=false}:{symbol:string;prominent?:boolean;showSession?:boolean;compact?:boolean}) {
  const {data,failed}=useContext(Context);const {ui,locale,date}=useLocale();
  const item=data?.items[symbol];const row=item?.snapshot;
  const status=quoteStatus(item,failed);
  const direction=movement(row?.change);
  const format=(value:number|null|undefined,signed=false)=>value==null?ui('Unavailable'):value.toLocaleString(locale,{maximumFractionDigits:2,signDisplay:signed?'exceptZero':'auto'});
  return <div data-live-symbol={symbol} className={`financial tabular-nums transition-colors duration-200 ${prominent||compact?'text-right':'text-xs'}`}>
    <div className={prominent?'text-[32px] font-semibold':compact?'text-sm font-semibold leading-5':'font-medium'}>{format(row?.last_price)} {row&&<span className="text-xs font-normal text-muted-foreground">VND</span>}</div>
    {row&&<div className={`flex flex-wrap gap-x-2 ${prominent?'justify-end text-sm':''} ${compact?'justify-end gap-x-1 whitespace-nowrap text-[11px] leading-4':''} ${direction.color}`}><span>{ui(direction.label)}</span>{row.change!=null&&<span>{format(row.change,true)}</span>}{row.change_percent!=null&&<span>{format(row.change_percent,true)}%</span>}</div>}
    <div className={`${compact?'mt-0.5':'mt-1'} text-[10px] leading-4 text-muted-foreground`}>{ui(status==='fresh'?'Current market':status==='stale'?'Stale market data':'Market data unavailable')}{row?' · '+date(row.updated_at,true):''}</div>
    {showSession&&row&&<p className="mt-1 text-[10px] text-muted-foreground">{ui('Source session')}: {ui(row.session==='active'?'Active trading session':row.session==='break'?'Midday break':row.session==='closed'?'Market closed':'Session unconfirmed')} · {row.source}</p>}
    {row&&<details className={`mt-0.5 text-[10px] leading-4 text-muted-foreground ${compact?'text-right':''}`}><summary className="cursor-pointer">{ui('Source & session')}</summary><p className="break-words">{row.source} · {ui('Trading date ·')} {date(row.trading_date)} · {ui('Reference price')} {format(row.reference_price)} VND</p></details>}
  </div>;
}
export function TickerMovement({symbol}:{symbol:string}) {
  const {data,failed}=useContext(Context);const {ui,locale,date}=useLocale();
  const item=data?.items[symbol];const row=item?.snapshot;const status=quoteStatus(item,failed);
  const value=row?.change_percent;const direction=movement(value);
  const valid=typeof value==='number'&&Number.isFinite(value);
  const label=valid?`${value>0?'▲ ':value<0?'▼ ':'＝ '}${value.toLocaleString(locale,{minimumFractionDigits:2,maximumFractionDigits:2,signDisplay:'exceptZero'})}%`:'—';
  return <span className={direction.color} title={`${ui(direction.label)} · ${ui(status==='fresh'?'Current market':status==='stale'?'Stale market data':'Market data unavailable')}${row?' · '+date(row.trading_date)+' · '+row.source+' · '+ui('Reference price')+' '+row.reference_price:''}`}><span aria-hidden="true">{label}</span><span className="sr-only">{ui(direction.label)} {valid?label:''}; {ui(status==='fresh'?'Current market':status==='stale'?'Stale market data':'Market data unavailable')}</span>{status==='stale'&&valid&&<span className="ml-1 text-[9px] text-muted-foreground">{date(row!.trading_date)}</span>}</span>;
}
