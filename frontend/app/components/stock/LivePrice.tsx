"use client";
import {createContext,useContext,type ReactNode} from 'react';
import {useLiveMarket} from '@/lib/useLiveMarket';
import {movement,type LiveBatch} from '@/lib/live-market';
import {useLocale} from '@/lib/i18n';

const Context=createContext<{data:LiveBatch|null;failed:boolean}>({data:null,failed:false});
export function LivePrices({symbols,interval,children}:{symbols:string[];interval:number;children:ReactNode}) {
  const value=useLiveMarket(symbols,interval);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function LivePrice({symbol,prominent=false}:{symbol:string;prominent?:boolean}) {
  const {data,failed}=useContext(Context);const {ui,locale,date}=useLocale();
  const item=data?.items[symbol];const row=item?.snapshot;
  const status=failed&&row?'stale':item?.status||'unavailable';
  const direction=movement(row?.change);
  const format=(value:number|null|undefined,signed=false)=>value==null?ui('Unavailable'):value.toLocaleString(locale,{maximumFractionDigits:2,signDisplay:signed?'exceptZero':'auto'});
  return <div data-live-symbol={symbol} className={`financial tabular-nums transition-colors duration-200 ${prominent?'text-right':'text-xs'}`}>
    <div className={prominent?'text-[32px] font-semibold':'font-medium'}>{format(row?.last_price)} {row&&<span className="text-xs font-normal text-muted-foreground">VND</span>}</div>
    {row&&<div className={`flex flex-wrap gap-x-2 ${prominent?'justify-end text-sm':''} ${direction.color}`}><span>{ui(direction.label)}</span>{row.change!=null&&<span>{format(row.change,true)}</span>}{row.change_percent!=null&&<span>{format(row.change_percent,true)}%</span>}</div>}
    <div className="mt-1 text-[10px] text-muted-foreground">{ui(status==='fresh'?'Current market':status==='stale'?'Stale market data':'Market data unavailable')}{row?' · '+date(row.updated_at,true):''}</div>
    {row&&<p className="mt-1 text-[10px] text-muted-foreground" title={`${ui('Source:')} ${row.source} · ${ui('Reference price')} ${format(row.reference_price)} VND`}>{ui('Source:')} SSI · {ui('Reference price')} {format(row.reference_price)}</p>}
  </div>;
}
