"use client";
import {useLocale} from "@/lib/i18n";
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {useLiveIndex} from '@/lib/useLiveMarket';
import {indexMascot} from '@/lib/live-market';
import {MascotIllustration} from './mascot/Mascot';
import HotTopics from './news/HotTopics';
import { indexMovement, signedIndex as signed, indexAggregate,indexDisplayStatus } from '@/lib/marketIndex';
import MarketFocus from './news/MarketFocus';
export default function ExploreMarket(){
  const {t,ui,locale,date:localDate}=useLocale();
  const live=useLiveIndex();const index=live.data?.snapshot||null;const indexError=live.failed;const indexLoading=!live.data&&!live.failed;
  const [,setClock]=useState(0);
  useEffect(()=>{const timer=setInterval(()=>setClock(value=>value+1),30000);return()=>clearInterval(timer);},[]);
  const freshness=indexDisplayStatus(live.data,indexError);
  const movement=indexMovement(index);
  return <>
    <header className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-4"><div className="min-w-0"><div className="eyebrow mb-2">{t("Workspace / Explore")}</div><h1>{t("Vietnam equities")}</h1><p className="mt-2 text-sm text-muted-foreground">{t("Market movement, publisher attention and stock research.")}</p></div><nav aria-label={t('Explore sections')} className="flex flex-wrap gap-4 text-xs text-primary"><a href="#hot-topics" className="hover:underline">{t('Hot Topics')}</a><a href="#market-focus" className="hover:underline">{t('Market Focus')}</a><a href="#explore-stocks" className="hover:underline">{t('Explore stocks')}</a></nav></div>
      <div className="panel flex min-w-0 items-center gap-3 p-5 sm:gap-6 sm:p-6">
        <div className="w-20 shrink-0 sm:w-28"><MascotIllustration state={indexLoading?'loading':freshness!=='fresh'?'marketUncertain':indexMascot(live.data?.session||'unknown',index?.change)} size={128} className="max-w-full"/></div>
        <div className="min-w-0"><h2 id="market-state" className="text-sm text-muted-foreground"><Link href="/indices/VNINDEX" className="hover:underline">{t("VN-Index")} ↗</Link></h2>
          {indexLoading&&!index?<p role="status" className="mt-3 text-sm">{t("Loading index…")}</p>:index?<>
            <p className="mt-1 text-4xl font-semibold tabular-nums sm:text-5xl">{index.level.toLocaleString(locale,{minimumFractionDigits:2,maximumFractionDigits:2})}</p>
            <p className={`mt-2 flex flex-wrap gap-x-2 text-sm font-medium tabular-nums ${movement.color}`}><span>{ui(movement.label)}</span><span>{ui(signed(index.change,'',locale))} {t("pts")}</span><span>({ui(signed(index.change_percent,'%',locale))})</span></p>
            <p className="mt-2 text-xs text-muted-foreground">SSI · {localDate(index.trading_date)} · {ui(live.data?.session==='closed'?'Market closed':live.data?.session==='break'?'Midday break':live.data?.session==='active'?'Trading session active':'Session unconfirmed')}{freshness!=='fresh'&&<span> · {ui('Stale market data')}</span>}</p>
            <details className="mt-2 text-[11px] text-muted-foreground"><summary className="cursor-pointer">{ui('Source & session')}</summary><p>{index.source} · <time dateTime={index.updated_at}>{localDate(index.updated_at,true)}</time> · {t('Vietnam time')}</p>
              {(index.total_volume!=null||index.total_value!=null)&&<dl className="mt-2 flex flex-wrap gap-4">{index.total_volume!=null&&<div><dt>{t('Total volume')}</dt><dd>{indexAggregate(index.total_volume,ui('shares'),locale)}</dd></div>}{index.total_value!=null&&<div><dt>{t('Total value')}</dt><dd>{indexAggregate(index.total_value,ui('VND'),locale)}</dd></div>}</dl>}
            </details>
          </>:<p className="mt-3 text-sm text-muted-foreground">{t("VN-Index data unavailable.")} <button type="button" onClick={live.refresh} className="text-primary underline">{t('Retry')}</button></p>}
          {indexError&&index&&<p role="alert" className="mt-2 text-xs text-muted-foreground">{ui('Refresh failed; showing the previous summary.')} <button className="text-primary underline" onClick={live.refresh}>{t('Retry')}</button></p>}
        </div>
      </div>
    </header>
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] xl:gap-8">
    <div id="hot-topics" className="min-w-0"><HotTopics/></div>
    <MarketFocus/>
    </div>
  </>;
}
