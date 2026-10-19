"use client";
import Link from 'next/link';
import {useEffect,useState} from 'react';
import {useLocale} from '@/lib/i18n';
import {useLiveIndex} from '@/lib/useLiveMarket';
import type {LiveIndex} from '@/lib/live-market';
import {indexDisplayStatus,indexMovement,indexUiState} from '@/lib/marketIndex';
import {MascotIllustration} from '../mascot/Mascot';

export function MarketContextView({data,failed,refresh,prominent=false,now=new Date()}:{data:LiveIndex|null;failed:boolean;refresh:()=>void;prominent?:boolean;now?:Date}){
  const {t,ui,number,date}=useLocale(),row=data?.snapshot;
  const status=indexDisplayStatus(data,failed,now);
  if(prominent){
    const movement=indexMovement(row||null),state=indexUiState(data,failed,now);
    const signed=(value:number|null)=>typeof value==='number'&&Number.isFinite(value)?(value>0?'+':'')+number(value):'—';
    return <section className="market-context market-context-prominent" aria-label={t('VN-Index')} data-index-status={status}>
      <div className="market-index-mascot"><MascotIllustration state={state} size={64}/></div>
      <div className="market-index-summary">
        <Link className="market-index-label" href="/indices/VNINDEX">{t('VN-Index')} ↗</Link>
        <div className="market-index-reading">
          <strong className="market-index-value">{row?number(row.level):'—'}</strong>
          {row?<span className={'market-index-change '+(status==='fresh'?movement.color:'text-muted-foreground')}><span>{ui(movement.label)}</span> <b>{signed(row.change)} {t('pts')}</b><span>({signed(row.change_percent)}%)</span></span>:<span role="status">{t(!data&&!failed?'Loading index…':'VN-Index data unavailable.')}</span>}
        </div>
        <p className="market-index-meta">{t(status==='fresh'?'Current source observation':status==='stale'?'Stale market data':'Unavailable')}{row&&<> · {row.source} · <time dateTime={row.updated_at}>{date(row.updated_at,true)}</time> · ICT · {ui(data?.session==='active'?'Active trading session':data?.session==='closed'?'Market closed':data?.session==='break'?'Midday break':'Session unconfirmed')}</>}</p>
        {failed&&<p role="alert" className="market-index-error">{t(row?'Refresh failed; showing the previous summary.':'VN-Index data unavailable.')} <button type="button" onClick={refresh}>{t('Retry')}</button></p>}
      </div>
      <details><summary>{t('Source & session')}</summary><p>{row?<>{row.source} · {date(row.trading_date)} · {ui(data?.session==='active'?'Active trading session':data?.session==='closed'?'Market closed':data?.session==='break'?'Midday break':'Session unconfirmed')} · <time dateTime={row.updated_at}>{date(row.updated_at,true)}</time> · ICT</>:t('VN-Index data unavailable.')}</p></details>
    </section>;
  }
  return <div className="market-context"><div><Link href="/indices/VNINDEX">{t('VN-Index')} ↗</Link>{row?<><strong>{number(row.level)}</strong><span className={status!=='fresh'?'text-muted-foreground':row.change_percent==null?'text-muted-foreground':row.change_percent>0?'positive':row.change_percent<0?'negative':'unchanged'}>{row.change_percent==null?'—':(row.change_percent>0?'+':'')+number(row.change_percent)+'%'}</span></>:<span role="status">{t(failed||data?'VN-Index data unavailable.':'Loading index…')}</span>}</div>
    <details><summary>{t('Source & session')}{row&&<> · {date(row.trading_date)} · {ui(data?.session==='active'?'Active trading session':data?.session==='closed'?'Market closed':data?.session==='break'?'Midday break':'Session unconfirmed')}{status==='stale'&&<> · {t('Stale')}</>}</>}</summary><p>{row?<>{row.source} · <time dateTime={row.updated_at}>{date(row.updated_at,true)}</time> · ICT</>:t('VN-Index data unavailable.')}</p>{failed&&<p role="alert">{t('Refresh failed; showing the previous summary.')} <button onClick={refresh}>{t('Retry')}</button></p>}</details>
    {!row&&failed&&<button onClick={refresh}>{t('Retry')}</button>}
  </div>;
}
export default function MarketContext({prominent=false}:{prominent?:boolean}={}){
  const live=useLiveIndex();
  const [,setClock]=useState(0);
  useEffect(()=>{const timer=setInterval(()=>setClock(n=>n+1),30000);return()=>clearInterval(timer);},[]);
  return <MarketContextView {...live} prominent={prominent}/>;
}
