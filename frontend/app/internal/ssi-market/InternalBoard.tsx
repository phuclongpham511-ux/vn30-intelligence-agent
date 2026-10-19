"use client";
import {useEffect,useState} from 'react';
import {QuoteMapView} from '../../components/stock/QuoteMap';
import {useLocale} from '@/lib/i18n';
import {provisionalMarketRecord,type ProvisionalMarket} from '@/lib/provisionalMarket';

/** Saved real observations under owner conventions, not synthetic or live data.
 * No provider lease, fetch, acquisition timer, backend, DB or Watchlist state.
 */
export default function InternalBoard({packet,asOf}:{packet:unknown;asOf:string}) {
  const {t}=useLocale();
  const [now,setNow]=useState(()=>new Date(asOf));
  const p=packet as ProvisionalMarket;
  const accepted=provisionalMarketRecord(packet,{symbol:p?.key?.symbol,exchange:p?.key?.exchange},now);
  useEffect(()=>{
    if(!accepted)return;
    const p=accepted;
    const foreground=()=>setNow(new Date());window.addEventListener('focus',foreground);
    // One local expiry, not a polling/acquisition loop. Source time is never
    // refreshed by this clock or by a foreground event.
    const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
    const midnight=Date.parse(today+'T00:00:00+07:00')+86400000;
    const expiry=p.matched.source_timestamp?Math.min(midnight,Date.parse(p.matched.source_timestamp)+120001):midnight;
    const delay=expiry-Date.now();
    const timer=p.key.trading_date===today&&delay>0?setTimeout(foreground,delay):undefined;
    return()=>{window.removeEventListener('focus',foreground);if(timer!==undefined)clearTimeout(timer);};
  },[accepted]);
  if(!accepted)return <p role="alert">{t('Provisional market data rejected; inspect the source contract.')}</p>;
  return <div><h1>{t('Internal provisional SSI data')}</h1><p>{t('Saved daily evidence, not a live quote.')}</p>
    <QuoteMapView stocks={[{symbol:p.key.symbol,exchange:p.key.exchange}]} data={{items:{},session:'unknown',as_of:asOf}} now={now} scope="page" internalProvisional={[packet]}/>
  </div>;
}
