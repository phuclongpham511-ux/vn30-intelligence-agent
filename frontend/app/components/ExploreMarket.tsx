"use client";
import {useEffect,useState} from 'react';
import {MascotIllustration,MascotState} from './mascot/Mascot';
import TopStory,{type TopStoryData} from './news/TopStory';
import {indexMovement,type IndexSnapshot} from '@/lib/marketIndex';
const signed=(value:number|null,suffix='')=>value==null?'Unavailable':`${value>0?'+':''}${value.toLocaleString('en-GB',{minimumFractionDigits:2,maximumFractionDigits:2})}${suffix}`;
export default function ExploreMarket(){
  const [index,setIndex]=useState<IndexSnapshot|null>(null);const [indexError,setIndexError]=useState(false);const [indexLoading,setIndexLoading]=useState(true);
  const [stories,setStories]=useState<TopStoryData[]|null>(null);const [newsError,setNewsError]=useState(false);const [attempt,setAttempt]=useState(0);
  useEffect(()=>{const controller=new AbortController();
    const loadIndex=async()=>{try{const r=await fetch('/api/stocks/index-snapshot',{signal:controller.signal,cache:'no-store'});if(!r.ok)throw Error();const row=await r.json();if(!controller.signal.aborted){setIndex(row);setIndexError(false);}}catch{if(!controller.signal.aborted)setIndexError(true);}finally{if(!controller.signal.aborted)setIndexLoading(false);}};
    const loadNews=async()=>{try{const r=await fetch('/api/news/hot?limit=4',{signal:controller.signal,cache:'no-store'});if(!r.ok)throw Error();const rows=await r.json();if(!controller.signal.aborted){setStories(rows);setNewsError(false);}}catch{if(!controller.signal.aborted)setNewsError(true);}};
    void loadIndex();void loadNews();const timer=setInterval(()=>{void loadIndex();void loadNews();},5*60*1000);return()=>{controller.abort();clearInterval(timer);};
  },[attempt]);
  const movement=indexMovement(index);
  return <>
    <section aria-labelledby="market-state" className="panel flex items-center justify-between gap-4 p-5 md:p-6">
      <div className="min-w-0"><h2 id="market-state" className="text-sm text-muted-foreground">VN-Index · Latest market movement</h2>
        {indexLoading&&!index ? <p role="status" className="mt-3 text-sm">Loading index…</p> : index ? <><p className={`mt-2 text-3xl font-semibold tabular-nums md:text-4xl ${movement.color}`}>{index.level.toLocaleString('en-GB',{minimumFractionDigits:2,maximumFractionDigits:2})}<span className="ml-2 text-xs font-normal text-muted-foreground">points</span></p><p className={`mt-2 flex flex-wrap gap-x-3 gap-y-1 text-sm font-medium tabular-nums ${movement.color}`}><span>{movement.label}</span><span>{signed(index.change)} pts</span><span>{signed(index.change_percent,'%')}</span></p><p className="mt-3 text-[11px] text-muted-foreground">{index.source} · Trading date {index.trading_date} · Latest provider summary</p></> : <p className="mt-3 text-sm text-muted-foreground">VN-Index data unavailable.</p>}
        {indexError&&<p role="alert" className="mt-2 text-xs text-muted-foreground">{index?'Refresh failed; showing the previous summary.':'The provider could not supply the index.'} <button className="text-primary underline" onClick={()=>setAttempt(v=>v+1)}>Retry</button></p>}
      </div><MascotIllustration state={movement.mascot} size={64}/>
    </section>
    <section aria-labelledby="hot-topics"><h2 id="hot-topics">Hot Topics</h2><p className="mt-1 text-xs text-muted-foreground">Independent publisher coverage · also available in News</p>
      {newsError&&<p role="alert" className="mt-3 text-sm">Hot Topics is temporarily unavailable. <button onClick={()=>setAttempt(v=>v+1)} className="text-primary underline">Retry</button></p>}
      {!stories&&!newsError&&<MascotState state="loading" role="status">Loading publisher reporting…</MascotState>}
      {stories&&!stories.length&&<MascotState state="noMatches">No multi-source stories qualify yet.</MascotState>}
      <div className="mt-3 grid gap-x-8 md:grid-cols-2">{stories?.map(item=><TopStory key={item.story.id} item={item}/>)}</div>
    </section>
  </>;
}
