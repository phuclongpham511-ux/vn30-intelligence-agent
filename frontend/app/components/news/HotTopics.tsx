"use client";
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {useLocale} from '@/lib/i18n';
import {uniqueHotTopics} from '@/lib/news';
import {cacheRefresh} from '@/lib/cacheRefresh';
import {newsSymbols} from '@/lib/newsPresentation';
import {LivePrices} from '../stock/LivePrice';
import TopStory,{type TopStoryData} from './TopStory';

type ViewProps={stories:TopStoryData[]|null;error:boolean;retry:()=>void;expanded:boolean;toggle:()=>void;embedded?:boolean;active?:boolean};
export function HotTopicsView({stories,error,retry,expanded,toggle,embedded=false,active=true}:ViewProps){
  const {t}=useLocale();
  const rows=stories?uniqueHotTopics(stories):null;
  return <section aria-label={t('Hot Topics')} className="hot-topics">
    {!embedded&&<div className="market-news-heading"><h2>{t('Hot Topics')}</h2><Link href="/news">{t('All news ↗')}</Link></div>}
    <p className="market-news-window">{t('Last 72 hours · independent publisher coverage.')}</p>
    {error&&<p role="alert" className="market-news-state">{t('Hot Topics is temporarily unavailable.')} <button type="button" onClick={retry}>{t('Retry')}</button></p>}
    {!rows&&!error&&<p role="status" className="market-news-state">{t('Loading publisher reporting…')}</p>}
    {rows&&!rows.length&&!error&&<p role="status" className="market-news-state">{t('No stories with independent publisher coverage qualify yet.')}</p>}
    {error&&!!rows?.length&&<p className="market-news-state">{t('Previously loaded headlines are shown below.')}</p>}
    <LivePrices symbols={active?newsSymbols(rows||[]):[]} interval={30000}>
      <div className="hot-topics-stories" data-expanded={expanded}>
        {rows?.map((item,index)=><div key={item.story.id} className={index>=3?'hot-topic-extra':index===2?'hot-topic-third':undefined}><TopStory item={item} compact textOnly showMovement showThumbnail/></div>)}
      </div>
    </LivePrices>
    {rows&&rows.length>2&&<button type="button" className={'hot-topics-expand'+(rows.length===3?' hot-topics-expand-mobile':'')} onClick={toggle} aria-expanded={expanded}>{t(expanded?'Show fewer headlines':'More headlines')}</button>}
    <details className="market-news-method"><summary>{t('About these headlines')}</summary><p>{t('At least two independent publisher groups within 72 hours. Existing publisher-coverage ranking; not sentiment or an investment signal.')}</p></details>
  </section>;
}

export default function HotTopics({active=true,embedded=false}:{active?:boolean;embedded?:boolean}){
  const [stories,setStories]=useState<TopStoryData[]|null>(null),[error,setError]=useState(false),[attempt,setAttempt]=useState(0),[expanded,setExpanded]=useState(false);
  useEffect(()=>{
    if(!active)return;
    const controller=new AbortController();let busy=false;
    const load=async()=>{if(busy)return;busy=true;try{
      const response=await fetch('/api/news/hot?limit=4',{signal:controller.signal,cache:'no-store'});
      if(!response.ok)throw Error();
      const rows:TopStoryData[]=await response.json();
      if(!controller.signal.aborted){setStories(uniqueHotTopics(rows));setError(false);}
    }catch{if(!controller.signal.aborted)setError(true);}finally{busy=false;}};
    void load();const stop=cacheRefresh(()=>{void load();});
    return()=>{controller.abort();stop();};
  },[active,attempt]);
  return <HotTopicsView stories={stories} error={error} retry={()=>setAttempt(n=>n+1)} expanded={expanded} toggle={()=>setExpanded(value=>!value)} embedded={embedded} active={active}/>;
}
