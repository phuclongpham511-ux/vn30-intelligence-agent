"use client";
import {useEffect,useState} from 'react';
import {stockRead} from '@/lib/stock-detail';

export function useStockRead<T>(url:string) {
  const [data,setData]=useState<T|null>(null);
  const [error,setError]=useState(false);
  const [attempt,setAttempt]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();
    setData(null);setError(false);
    const timeout=setTimeout(()=>controller.abort(new Error('Request timed out')),20000);
    let disposed=false;
    stockRead<T>(url,controller.signal).then(value=>{if(!disposed)setData(value);}).catch(()=>{if(!disposed)setError(true);}).finally(()=>clearTimeout(timeout));
    return()=>{disposed=true;clearTimeout(timeout);controller.abort();};
  },[url,attempt]);
  return {data,error,retry:()=>setAttempt(value=>value+1)};
}
