"use client";
import {useEffect,useState} from 'react';
import {useLocale} from '@/lib/i18n';
import {loadIntelligence,readWatchlist,baselineLegacyReviews,watchlistStorageKey,watchlistChangedEvent,type Intelligence,type WatchlistState,type AttentionUpdate} from '@/lib/watchlist';
import {reviewBriefingItem} from '@/lib/dailyBriefing';
import {stockResearch,type ResearchEntry} from '@/lib/stock-intelligence';
import {collectionLabels} from '@/lib/collectionStatus';
import {newsViewQuery,emptyNewsFilters} from '@/lib/news';
import {actionUrl} from '@/lib/stock-detail';

export function StockIntelligenceView({ticker,data,state,error=false,storageError=false,retry,review,preview=false,focus='all'}:{
  ticker:string;data:Intelligence|null;state:WatchlistState|null;error?:boolean;storageError?:boolean;
  retry:()=>void;review:(item:AttentionUpdate)=>void;preview?:boolean;focus?:'all'|'community';
}){
  const {t,ui,date,number}=useLocale();
  const [expanded,setExpanded]=useState(false),[earnings,setEarnings]=useState(false);
  let research:ReturnType<typeof stockResearch>|null=null;
  try{if(data)research=stockResearch(data,ticker,storageError?null:state);}catch{/* Fail closed on cross-ticker or malformed evidence. */}
  const sources=data?[...data.news_sources,...data.community_sources]:[];
  const coverageUnknown=!data?.news_sources.some(s=>s.enabled)||!data?.community_sources.some(s=>s.enabled)||sources.some(s=>s.enabled&&s.status!=='healthy');
  const countsKnown=!!research&&!research.unavailable&&!error&&!storageError&&!!state&&research.following;
  const renderEntry=(entry:ResearchEntry)=><li key={entry.item.id} data-stock-update={entry.item.id} className="min-w-0 py-3 first:pt-0">
    <div className="flex flex-wrap gap-x-2 gap-y-1 text-[11px] text-muted-foreground"><span>{entry.source}</span><span>{t('Source status at read')}: {entry.sourceStatus==='unknown'?t('Unavailable'):ui(collectionLabels[entry.sourceStatus])}</span>{entry.discussion&&<span>{t('Unverified')}</span>}{entry.discussion?.is_fixture&&<strong>DEMO · {t('Fixture')}</strong>}</div>
    <h3 className="mt-1 break-words text-sm font-medium leading-5"><a href={entry.url} target="_blank" rel="noopener noreferrer" className="hover:text-primary focus-visible:outline-2">{entry.item.title}</a></h3>
    <p className="mt-1 text-[11px] text-muted-foreground">{t('Published')}: {entry.published?<time dateTime={entry.published}>{date(entry.published,true)}</time>:t('Unavailable')} · {t('First observed')}: {entry.observed?<time dateTime={entry.observed}>{date(entry.observed,true)}</time>:t('Unavailable')} ICT</p>
    <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[11px]"><span className="text-muted-foreground">{t(entry.relevance)}{entry.unread!==null?' · '+t(entry.unread?entry.corrected?'Updated since review':'Unreviewed':'Reviewed'):''}</span>
      {entry.unread===true&&!storageError&&<button type="button" className="text-primary underline" aria-label={t('Mark reviewed: {title}',{title:entry.item.title})} onClick={()=>review(entry.item)}>{t('Mark reviewed')}</button>}
    </div>
    {entry.discussion&&<p className="mt-1 text-[11px] text-muted-foreground">{entry.discussion.replies==null?t('Replies unavailable'):t('{count} replies',{count:number(entry.discussion.replies,0)})} · {entry.discussion.views==null?t('Views unavailable'):t('{count} views',{count:number(entry.discussion.views,0)})}</p>}
    <details className="mt-2 text-xs text-muted-foreground"><summary className="cursor-pointer">{t('Source evidence')}</summary>
      {entry.updated&&<p className="mt-2">{t('Last observed')}: <time dateTime={entry.updated}>{date(entry.updated,true)}</time> ICT</p>}
      {entry.topics.length>0&&<p className="mt-2">{t('Recorded topics')}: {entry.topics.map(ui).join(' · ')}</p>}
      {entry.proofs.map((proof,index)=><p key={index} className="mt-2 break-words">{t(proof.evidence_origin==='publisher_text'?'Publisher text':'Headline evidence')} · {proof.matched_text}{proof.evidence_excerpt?' · '+proof.evidence_excerpt:''}</p>)}
      {entry.discussion&&<p className="mt-2 whitespace-pre-wrap break-words">{entry.discussion.excerpt}</p>}
      {entry.articles.map(article=>{const link=actionUrl(article.url);return <div key={article.id} className="mt-2 break-words"><p>{link?<a href={link} target="_blank" rel="noopener noreferrer" className="text-primary underline">{article.source_name} · {article.title}</a>:article.source_name+' · '+article.title}</p><p>{t('Published')}: {date(article.published_at,true)} · {t('First observed')}: {date(article.first_seen_at,true)} ICT</p></div>;})}
      <a className="mt-2 inline-block text-primary underline" href={entry.url} target="_blank" rel="noopener noreferrer">{t(entry.discussion?'Original discussion ↗':'Original report ↗')}</a>
      {entry.item.evidence_truncated&&<p className="mt-2">{t('Source evidence is truncated.')}</p>}
    </details>
  </li>;
  const news=research?.news.filter(entry=>!earnings||entry.topics.includes('Earnings'))||[];
  const shown=preview?news.slice(0,3):expanded?news:news.slice(0,6);
  return <section className="panel min-w-0 p-4 sm:p-5" aria-label={t('Company research updates')}>
    <header className="flex flex-wrap items-start justify-between gap-2"><div><h2>{t('Company research updates')} · {ticker}</h2><p className="stock-note">{t('Unreviewed first, then publication time. Coverage is not financial materiality.')}</p></div><button type="button" onClick={retry} className="text-xs text-primary underline">{t('Refresh stored evidence')}</button></header>
    <nav className="mt-2 flex flex-wrap gap-4 text-xs" aria-label={t('Related company research')}><a className="text-primary underline" href="#stock-fundamentals">{t('Fundamental analysis')}</a><a className="text-primary underline" href="#stock-actions">{t('Dividends & corporate actions')}</a><a className="text-primary underline" href="#stock-news">{t('Company news')}</a><a className="text-primary underline" href="#stock-community">{t('Community context')}</a><a className="text-primary underline" href="/watchlist">{t('Watchlist')}</a></nav>
    {error||data&&!research?<p className="stock-note" role="alert">{t('Company research is unavailable. Unread counts are unknown.')}</p>:!data?<p className="stock-note" role="status">{t('Loading company research…')}</p>:research?.unavailable?<p className="stock-note" role="status">{t('Stored research identity is unavailable; coverage is unknown.')}</p>:research&&<>
      <div className="mt-3 border-y py-3 text-xs"><p>{t('Evidence evaluated')}: <time dateTime={data.as_of}>{date(data.as_of,true)}</time> ICT</p>
        {countsKnown?<p className="mt-1">{t('{count} unreviewed loaded stories',{count:research.news.filter(entry=>entry.unread).length})} · {t('{count} unreviewed loaded discussions',{count:research.community.filter(entry=>entry.unread).length})}</p>:<p className="mt-1">{t(storageError?'Review state unavailable. Unread counts are unknown.':!state?'Loading saved review state…':'Follow this stock to use its saved Watchlist review context.')}</p>}
        {countsKnown&&<p className="mt-1 text-muted-foreground">{t('Last recorded review')}: {date(state?.reviewedAt?.[ticker]??null,true)}</p>}
        <p className="mt-1 text-muted-foreground">{t('Opening a report never marks it reviewed. Reviews affect only the selected story or discussion.')}</p>
      </div>
      {(coverageUnknown||research.incomplete)&&<p role="status" className="stock-note">{t('Coverage incomplete; source checks may be stale or unavailable. Counts describe the loaded sample only.')}</p>}
      <div hidden={focus==='community'} data-stock-research="news">
      <div className="mt-4 flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-semibold">{t('Company news')} · {t('72-hour window')}</h3><label className="text-xs"><input className="mr-2" type="checkbox" checked={earnings} onChange={event=>setEarnings(event.target.checked)}/>{t('Financial results · existing Earnings tags')}</label></div>
      <p className="stock-note">{t('The window uses existing acquisition rules; publication may be older. News does not confirm financial metrics or corporate actions.')}</p>
      {shown.length?<ul className="mt-3 divide-y">{shown.map(renderEntry)}</ul>:<p className="stock-note">{t(earnings?'No loaded stories have the existing Earnings tag.':'No matching stored stories in this window. This does not establish that no development occurred.')}</p>}
      {!preview&&news.length>6&&<button type="button" className="mt-2 text-xs text-primary underline" aria-expanded={expanded} onClick={()=>setExpanded(value=>!value)}>{t(expanded?'Show fewer updates':'Show all {count} loaded updates',{count:news.length})}</button>}
      {preview&&<a className="mt-2 inline-block text-xs text-primary underline" href="#stock-news">{t('Open company research')}</a>}
      </div>
      <details open={focus==='community'?true:undefined} data-stock-research="community" className="mt-4 border-t pt-3"><summary className="cursor-pointer text-sm font-semibold">{t('Community context')} · {t('24-hour window')} · {research.community.length}</summary><p className="stock-note">{t('Investor discussion is unverified. Engagement is attention, not sentiment or corroboration.')}</p>
        <p className="stock-note">{t('Repeated copies share a display group; each source item keeps its own review state.')}</p>
        {research.community.length?<ul className="mt-3 divide-y">{(preview?research.communityGroups.slice(0,3):research.communityGroups).map(group=><li key={group[0].item.id} className="py-3"><ul>{renderEntry(group[0])}</ul>{group.length>1&&<details className="mt-2 text-xs"><summary className="cursor-pointer">{t('Additional source copies ({count})',{count:group.length-1})}</summary><ul>{group.slice(1).map(renderEntry)}</ul></details>}</li>)}</ul>:<p className="stock-note">{t('No matching stored discussions in this window. Coverage may be incomplete.')}</p>}
      </details>
      <details className="mt-4 border-t pt-3 text-xs text-muted-foreground"><summary className="cursor-pointer">{t('Source coverage and review rules')}</summary><p className="mt-2">{t('Saved story IDs and content revisions determine unread state; publication and observation times are separate.')}</p>
        {sources.map((source,index)=><p key={index} className="mt-2">{source.name} · {ui(collectionLabels[source.status])} · {t('Last successful fetch')}: {date(source.last_success_at,true)} ICT</p>)}
        <a className="mt-3 inline-block text-primary underline" href={'/news?'+newsViewQuery({...emptyNewsFilters,ticker},'company')}>{t('View source archive')}</a>
      </details>
    </>}
  </section>;
}

export default function StockIntelligence({ticker,preview=false,focus='all'}:{ticker:string;preview?:boolean;focus?:'all'|'community'}){
  const [data,setData]=useState<Intelligence|null>(null),[state,setState]=useState<WatchlistState|null>(null);
  const [error,setError]=useState(false),[storageError,setStorageError]=useState(false),[attempt,setAttempt]=useState(0);
  const publish=(next:WatchlistState,current:WatchlistState)=>{
    if(next!==current){localStorage.setItem(watchlistStorageKey,JSON.stringify(next));window.dispatchEvent(new Event(watchlistChangedEvent));}
    setState(next);setStorageError(false);
  };
  useEffect(()=>{
    const restore=()=>{try{setState(readWatchlist(localStorage.getItem(watchlistStorageKey)));setStorageError(false);}catch{setState(null);setStorageError(true);}};
    restore();window.addEventListener('storage',restore);window.addEventListener('focus',restore);window.addEventListener(watchlistChangedEvent,restore);
    return()=>{window.removeEventListener('storage',restore);window.removeEventListener('focus',restore);window.removeEventListener(watchlistChangedEvent,restore);};
  },[ticker]);
  useEffect(()=>{
    const controller=new AbortController();let disposed=false;
    const timeout=setTimeout(()=>controller.abort(),20000);
    setData(null);setError(false);
    loadIntelligence([ticker],0,controller.signal,fetch,{community_groups:true}).then(result=>{
      if(disposed)return;controller.signal.throwIfAborted();
      stockResearch(result,ticker,null);setData(result);
      try{const current=readWatchlist(localStorage.getItem(watchlistStorageKey));publish(current.symbols.includes(ticker)?baselineLegacyReviews(current,result):current,current);}catch{setState(null);setStorageError(true);}
    }).catch(()=>{if(!disposed)setError(true);}).finally(()=>clearTimeout(timeout));
    return()=>{disposed=true;clearTimeout(timeout);controller.abort();};
  },[ticker,attempt]);
  const review=(item:AttentionUpdate)=>{
    if(!state)return;
    try{const current=readWatchlist(localStorage.getItem(watchlistStorageKey));publish(reviewBriefingItem(current,state,{references:[{symbol:ticker,item}]}),current);}catch{setState(null);setStorageError(true);}
  };
  const matches=data?.stocks.length===1&&data.stocks[0].symbol===ticker;
  return <StockIntelligenceView ticker={ticker} data={matches?data:null} state={state} error={error} storageError={storageError} retry={()=>setAttempt(value=>value+1)} review={review} preview={preview} focus={focus}/>;
}
