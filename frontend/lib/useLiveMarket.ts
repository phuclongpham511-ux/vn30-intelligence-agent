"use client";
import {useEffect,useState} from 'react';
import {liveRefresh,visibleSymbols,type LiveBatch,type LiveIndex} from './live-market';

function useLive<T extends {session:import('./live-market').Session}>(url:string,interval:number) {
  const [data,setData]=useState<T|null>(null);
  const [failed,setFailed]=useState(false);
  const [version,setVersion]=useState(0);
  useEffect(()=>{
    setData(null);setFailed(false);
    if(!url)return;
    const clientId=crypto.randomUUID();
    const leased=url.startsWith('/api/stocks/live?');
    const release=()=>{if(leased)void fetch('/api/stocks/live-release?client_id='+clientId,{method:'POST',keepalive:true}).catch(()=>{});};
    return liveRefresh<T>(async signal=>{
      const response=await fetch(url+(leased?'&client_id='+clientId:''),{signal,cache:'no-store'});
      if(!response.ok)throw Error('Live market unavailable');
      return response.json();
    },result=>{if(result){setData(result);setFailed(false);}else setFailed(true);},interval,document,
    {set:(fn,delay)=>window.setTimeout(fn,delay),clear:timer=>window.clearTimeout(timer as number)},release);
  },[url,interval,version]);
  return {data,failed,refresh:()=>setVersion(value=>value+1)};
}
export function useLiveMarket(symbols:string[],interval:number) {
  const key=visibleSymbols(symbols);
  return useLive<LiveBatch>(key?'/api/stocks/live?symbols='+encodeURIComponent(key):'',interval);
}
export function useLiveIndex(){return useLive<LiveIndex>('/api/stocks/live-index',15000);}
