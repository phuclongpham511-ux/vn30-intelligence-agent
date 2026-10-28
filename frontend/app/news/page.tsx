"use client";
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {useLocale} from '@/lib/i18n';
import {legacyCommunityHref} from '@/lib/community';
import {readNewsSearch,newsSearchQuery,newsSectionLabels,type NewsView} from '@/lib/news';
import {editorialStories} from '@/lib/newsPresentation';
import {useNewsArchive} from '@/lib/useNewsArchive';
import {MascotState} from '../components/mascot/Mascot';
import {Button} from '../components/ui/button';
import TopStory from '../components/news/TopStory';

export default function NewsPage(){
  const {t,ui,date}=useLocale();
  const [input,setInput]=useState('');
  const [query,setQuery]=useState('');
  const [view,setView]=useState<NewsView|null>('industry');
  const [ready,setReady]=useState(false);
  const [attempt,setAttempt]=useState(0);
  const navigate=(text:string,section:NewsView|null)=>{
    const next=text.trim(),selected=next?section:section||'industry';setInput(text);setQuery(next);setView(selected);
    const params=newsSearchQuery(next,selected),url='/news'+(params?'?'+params:'');
    if(window.location.search!==(params?'?'+params:''))window.history.pushState(null,'',url);
  };
  useEffect(()=>{
    const sync=()=>{
      const legacy=legacyCommunityHref(window.location.search);
      if(legacy){setReady(false);window.location.replace(legacy);return false;}
      const initial=readNewsSearch(window.location.search);
      setInput(initial.query);setQuery(initial.query);setView(initial.view);setReady(true);
      const params=newsSearchQuery(initial.query,initial.view);
      window.history.replaceState(null,'','/news'+(params?'?'+params:''));
    };
    if(sync()===false)return;window.addEventListener('popstate',sync);
    return()=>window.removeEventListener('popstate',sync);
  },[]);
  useEffect(()=>{
    if(!ready||input.trim()===query)return;
    const timer=setTimeout(()=>navigate(input,input.trim()?null:'industry'),300);
    return()=>clearTimeout(timer);
  },[input,query,ready]);
  const settling=input.trim()!==query;
  const category=view?{company:'COMPANY',industry:'INDUSTRY',briefing:'MARKET_BRIEF'}[view]:'ALL';
  const params=new URLSearchParams({research_category:category});if(query)params.set('q',query);
  const archive=useNewsArchive(ready&&!settling?params.toString():null,attempt);
  const data=settling?null:archive.page,loading=settling||archive.loading,error=!settling&&archive.error;
  const items=editorialStories(data?.items||[]);
  return <div className="page-stack news-page">
    <header className="news-page-header"><h1>{t('News')}</h1></header>
    <form role="search" className="news-search" onSubmit={event=>{event.preventDefault();navigate(input,input.trim()===query?view:null);}}>
      <label htmlFor="news-search" className="sr-only">{t('Search news')}</label>
      <input id="news-search" type="search" value={input} maxLength={120} autoComplete="off" placeholder={t('Search stocks, companies, industries, news...')} onChange={event=>setInput(event.target.value)}/>
      {input&&<button type="button" onClick={()=>navigate('','industry')} aria-label={t('Clear search')}>{t('Clear search')}</button>}
    </form>
    <nav aria-label={t('News sections')} className="news-section-nav">{(Object.entries(newsSectionLabels) as [NewsView,string][]).map(([key,label])=><button type="button" key={key} aria-pressed={view===key} onClick={()=>navigate(input,key)}>{ui(label)}</button>)}</nav>
    {error&&<MascotState state="dataUnavailable" role="alert">{t('News is temporarily unavailable.')} {data&&t('Previously loaded headlines are shown below.')} <button className="text-primary underline" onClick={()=>setAttempt(value=>value+1)}>{t('Retry')}</button></MascotState>}
    {loading&&!data&&<MascotState state="loading" role="status">{t('Loading news…')}</MascotState>}
    {data&&<section aria-label={view?ui(newsSectionLabels[view]):t('All news')} aria-busy={loading}>
      {!items.length&&!error&&<MascotState state="noMatches">{t('No qualifying recent reporting matches this view. Coverage may be incomplete.')}</MascotState>}
      <ol className="news-results news-feed" aria-label={t(query?'Relevant reporting first':'Latest reporting first')}>
        {items.map(item=><li key={item.story.id}><TopStory item={item} compact textOnly showThumbnail reserveThumbnailSpace/></li>)}
      </ol>
      <div className="mt-6 flex flex-col items-center gap-2">
        {data.has_more&&<Button variant="outline" disabled={loading} onClick={archive.loadMore}>{t(loading?'Loading more…':'Show more')}</Button>}
        <details className="text-xs text-muted-foreground"><summary>{ui('About this feed')}</summary>
          <p>{t('Feed snapshot')} <time dateTime={data.as_of}>{date(data.as_of,true)}</time> · {t('Times in Vietnam (UTC+7).')}</p>
          <p>{t('Search covers stored headlines and publisher-supplied text where available, not all full articles. New searches span all categories; tabs narrow the results.')}</p>
          <p>{t('Reporting from the last 72 hours. Older items appear when you choose Show more.')}</p>
          <p>{t('First seen is when Woofi first recorded a report, not its publication time. Rechecking a source does not make a story new.')}</p>
          <Link className="text-primary underline" href="/news/sources">{t('Source health')}</Link>
        </details>
      </div>
    </section>}
  </div>;
}
