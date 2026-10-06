"use client";
import {useLocale} from "@/lib/i18n";
import {useEffect,useState} from 'react';
import {MascotIllustration,MascotState} from './mascot/Mascot';
import TopStory,{type TopStoryData} from './news/TopStory';
import { indexMovement, signedIndex as signed, indexAggregate, type IndexSnapshot } from '@/lib/marketIndex';
export default function ExploreMarket(){
  const {t,ui,locale,date:localDate}=useLocale();
  const [index,setIndex]=useState<IndexSnapshot|null>(null);const [indexError,setIndexError]=useState(false);const [indexLoading,setIndexLoading]=useState(true);
  const [stories,setStories]=useState<TopStoryData[]|null>(null);const [newsError,setNewsError]=useState(false);const [attempt,setAttempt]=useState(0);
  useEffect(()=>{const controller=new AbortController();
    const loadIndex=async()=>{try{const r=await fetch('/api/stocks/index-snapshot',{signal:controller.signal,cache:'no-store'});if(!r.ok)throw Error();const row=await r.json();if(!controller.signal.aborted){setIndex(row);setIndexError(false);}}catch{if(!controller.signal.aborted)setIndexError(true);}finally{if(!controller.signal.aborted)setIndexLoading(false);}};
    const loadNews=async()=>{try{const r=await fetch('/api/news/hot?limit=4',{signal:controller.signal,cache:'no-store'});if(!r.ok)throw Error();const rows=await r.json();if(!controller.signal.aborted){setStories(rows);setNewsError(false);}}catch{if(!controller.signal.aborted)setNewsError(true);}};
    void loadIndex();void loadNews();const timer=setInterval(()=>{void loadIndex();void loadNews();},5*60*1000);return()=>{controller.abort();clearInterval(timer);};
  },[attempt]);
  const movement=indexMovement(index);
  return <>
    <header className="flex flex-col gap-6 border-b pb-6 lg:flex-row lg:items-center lg:justify-between">
      <div className="min-w-0"><div className="eyebrow mb-3">{t("Workspace / Explore")}</div><h1>{t("Vietnam equities")}</h1><p className="mt-3 text-sm text-muted-foreground">{t("Market movement, publisher attention and stock research.")}</p></div>
      <div className="flex min-w-0 items-center gap-2 sm:gap-5">
        <div className="min-w-0 flex-1"><div className="p-1">
          <h2 id="market-state" className="text-sm text-muted-foreground">{t("VN-Index")}</h2>
          {indexLoading&&!index?<p role="status" className="mt-3 text-sm">{t("Loading index…")}</p>:index?<>
            <p className={`mt-2 text-3xl font-semibold tabular-nums ${movement.color}`}>{index.level.toLocaleString(locale,{minimumFractionDigits:2,maximumFractionDigits:2})}</p>
            <p className={`mt-1 flex flex-wrap gap-x-3 text-xs font-medium tabular-nums ${movement.color}`}><span>{ui(movement.label)}</span><span>{ui(signed(index.change,'',locale))} {t("pts")}</span><span>{ui(signed(index.change_percent,'%',locale))}</span></p>
            <p className="mt-2 text-[11px] text-muted-foreground">{t("Trading date ·")} {localDate(index.trading_date)}</p>
            <dl className="mt-2 grid grid-cols-2 gap-x-4 text-[11px] tabular-nums"><div><dt className="text-muted-foreground">{t("Total volume")}</dt><dd>{ui(indexAggregate(index.total_volume,ui('shares'),locale))}</dd></div><div><dt className="text-muted-foreground">{t("Total value")}</dt><dd>{ui(indexAggregate(index.total_value,ui('VND'),locale))}</dd></div></dl>
          </>:<p className="mt-3 text-sm text-muted-foreground">{t("VN-Index data unavailable.")}</p>}
        </div>{indexError&&<p role="alert" className="mt-2 text-xs text-muted-foreground">{ui(index?'Refresh failed; showing the previous summary.':'Index data could not be loaded.')} <button className="text-primary underline" onClick={()=>setAttempt(v=>v+1)}>{t("Retry")}</button></p>}</div>
        <div className="w-32 shrink-0"><MascotIllustration state={movement.mascot} size={128}/></div>
      </div>
    </header>
    <section aria-labelledby="hot-topics"><h2 id="hot-topics">{t("Hot Topics")}</h2><p className="mt-1 text-xs text-muted-foreground">{t("Independent publisher coverage · also available in News")}</p>
      {newsError&&<p role="alert" className="mt-3 text-sm">{t("Hot Topics is temporarily unavailable.")} <button onClick={()=>setAttempt(v=>v+1)} className="text-primary underline">{t("Retry")}</button></p>}
      {!stories&&!newsError&&<MascotState state="loading" role="status">{t("Loading publisher reporting…")}</MascotState>}
      {stories&&!stories.length&&<MascotState state="noMatches">{t("No multi-source stories with available images qualify yet.")}</MascotState>}
      <div className="mt-3 grid gap-x-8 md:grid-cols-2">{stories?.map(item=><TopStory key={item.story.id} item={item} requireImage onImageUnavailable={()=>setStories(rows=>rows?.filter(row=>row.story.id!==item.story.id)||[])}/>)}</div>
    </section>
  </>;
}
