"use client";
import Link from 'next/link';
import {useEffect,useState} from 'react';
import {useLocale} from '@/lib/i18n';
import {useLiveIndex} from '@/lib/useLiveMarket';
import {indexDisplayStatus} from '@/lib/marketIndex';
export default function MarketContext(){
  const {t,ui,number,date}=useLocale();const live=useLiveIndex(),row=live.data?.snapshot;
  const [,setClock]=useState(0);
  useEffect(()=>{const timer=setInterval(()=>setClock(n=>n+1),30000);return()=>clearInterval(timer);},[]);
  const status=indexDisplayStatus(live.data,live.failed);
  return <div className="market-context"><div><Link href="/indices/VNINDEX">{t('VN-Index')} ↗</Link>{row?<><strong>{number(row.level)}</strong><span className={status!=='fresh'?'text-muted-foreground':row.change_percent==null?'text-muted-foreground':row.change_percent>0?'positive':row.change_percent<0?'negative':'unchanged'}>{row.change_percent==null?'—':(row.change_percent>0?'+':'')+number(row.change_percent)+'%'}</span></>:<span role="status">{t(live.failed||live.data?'VN-Index data unavailable.':'Loading index…')}</span>}</div>
    <details><summary>{t('Source & session')}{row&&<> · {date(row.trading_date)} · {ui(live.data?.session==='active'?'Active trading session':live.data?.session==='closed'?'Market closed':live.data?.session==='break'?'Midday break':'Session unconfirmed')}{status==='stale'&&<> · {t('Stale')}</>}</>}</summary><p>{row?<>{row.source} · <time dateTime={row.updated_at}>{date(row.updated_at,true)}</time> · ICT</>:t('VN-Index data unavailable.')}</p>{live.failed&&<p role="alert">{t('Refresh failed; showing the previous summary.')} <button onClick={live.refresh}>{t('Retry')}</button></p>}</details>
    {!row&&live.failed&&<button onClick={live.refresh}>{t('Retry')}</button>}
  </div>;
}
