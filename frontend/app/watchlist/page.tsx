"use client";
import Link from 'next/link';
import {useEffect,useState} from 'react';
import {useLocale} from '@/lib/i18n';
import {Button} from '../components/ui/button';
import {MascotState} from '../components/mascot/Mascot';
import StockSearch from '../components/stock/StockSearch';
import {LivePrices,LivePrice} from '../components/stock/LivePrice';
import {TechnicalInsightsView} from '../components/stock/TechnicalInsights';
import ArticleRow from '../components/news/ArticleRow';
import {safeExternalUrl} from '@/lib/presentation';
import {emptyNewsFilters,newsViewQuery,type NewsArticle} from '@/lib/news';
import type {CommunityItem} from '@/lib/community';
import {collectionLabels} from '@/lib/collectionStatus';
import {emptyWatchlist,readWatchlist,followStock,unfollowStock,watchlistStorageKey,loadIntelligence,isUnread,reviewUpdates,baselineLegacyReviews,uniqueUpdates,technicalCountKnown,type WatchlistState,type Intelligence,type AttentionUpdate,type UpdatePage} from '@/lib/watchlist';

function UpdateSection({label,page,symbol,state,disabled,review,sourceNames={}}: {label:string;page:UpdatePage;symbol:string;state:WatchlistState;disabled:boolean;review:(items:AttentionUpdate[])=>void;sourceNames?:Record<string,string>}) {
  const {t,date}=useLocale();
  const [expanded,setExpanded]=useState(false);
  const rows=uniqueUpdates(page.items);
  rows.sort((a,b)=>Number(isUnread(state,symbol,b))-Number(isUnread(state,symbol,a)) || b.occurred_at.localeCompare(a.occurred_at) || a.id.localeCompare(b.id));
  const shown=expanded?rows:rows.slice(0,3);
  const fresh=rows.filter(item=>isUnread(state,symbol,item)).length;
  return <section className="border-t pt-3" aria-label={label}>
    <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-medium">{label} · {disabled?t('Count unavailable'):t('{count} unreviewed on this page',{count:fresh})}</h3>
      {shown.length>0&&<button aria-label={t('Mark displayed {kind} reviewed',{kind:label})} className="text-xs text-primary underline disabled:opacity-50" disabled={disabled} onClick={()=>review(shown)}>{t('Review displayed')}</button>}</div>
    {label===t('Community')&&<p className="mt-1 text-xs text-muted-foreground">{t('Investor discussion · unverified · Vietnam time')}</p>}
    {!rows.length?<p className="mt-2 text-xs text-muted-foreground">{t('No matching updates on this page. Coverage may be incomplete.')}</p>
      :<ul className="mt-2 divide-y">{shown.map(item=>{
        const url=safeExternalUrl(item.url);
        const revised=!!state.receipts?.[symbol]?.[item.id]&&isUnread(state,symbol,item);
        const discussion=item.kind==='community'?item.evidence as CommunityItem:null;
        return <li key={item.id} data-update={item.id} className="py-3 first:pt-0">
          <div className="flex flex-wrap gap-2 text-[11px] text-muted-foreground"><time dateTime={item.occurred_at}>{date(item.occurred_at,true)}</time>
            {!disabled&&isUnread(state,symbol,item)&&<span className="text-primary">{t(revised?'Updated since review':'Unreviewed')}</span>}
            {item.source_count!==undefined&&<span>{t('{count} publisher groups',{count:item.source_count})}</span>}</div>
          {discussion&&<p className="mt-1 text-[11px] text-muted-foreground">{sourceNames[discussion.source_id]||discussion.source_id}{discussion.is_fixture?' · '+t('Fixture'):''}</p>}
          <h4 className="mt-1 break-words text-sm leading-6">{item.title}</h4>
          {discussion&&discussion.title&&<p className="mt-1 line-clamp-2 break-words text-xs text-muted-foreground">{discussion.excerpt.slice(0,180)}</p>}
          <div className="mt-1 flex flex-wrap gap-4 text-xs">{url&&<a href={url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{t('Read original ↗')}</a>}
            <button aria-label={t('Mark this update reviewed')} disabled={disabled} className="text-primary underline disabled:opacity-50" onClick={()=>review([item])}>{t('Mark reviewed')}</button></div>
          <details className="mt-2 text-xs"><summary className="cursor-pointer text-muted-foreground">{t('View source evidence')}</summary>
            {item.kind==='news'?(item.evidence as NewsArticle[]).map(article=><ArticleRow key={article.id} article={article}/>)
              :<pre className="mt-2 whitespace-pre-wrap break-all rounded bg-muted/40 p-3">{JSON.stringify(item.evidence,null,2)}</pre>}
            {item.evidence_truncated&&<p className="mt-2">{t('Additional source evidence is available in News.')}</p>}
          </details>
        </li>;
      })}</ul>}
    {rows.length>3&&<button className="mt-2 text-xs text-primary underline" onClick={()=>setExpanded(v=>!v)}>{t(expanded?'Show fewer updates':'Show all {count} loaded updates',{count:rows.length})}</button>}
    {(page.has_more||page.truncated)&&<p className="mt-2 text-xs text-amber-700 dark:text-amber-300">{t(page.truncated?'The bounded source sample is incomplete. Open the source archive for more.':'More updates are available on the next page.')}</p>}
  </section>;
}

export default function WatchlistPage() {
  const {t,ui,date,language}=useLocale();
  const [state,setState]=useState<WatchlistState>(emptyWatchlist);
  const [ready,setReady]=useState(false);
  const [storageError,setStorageError]=useState(false);
  const [selected,setSelected]=useState('');
  const [data,setData]=useState<Intelligence|null>(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState(false);
  const [offset,setOffset]=useState(0);
  const [attempt,setAttempt]=useState(0);
  const symbolsKey=state.symbols.join(',');
  const persist=(change:(current:WatchlistState)=>WatchlistState)=>{
    try {
      const current=readWatchlist(localStorage.getItem(watchlistStorageKey));
      const next=change(current);
      if(next!==current)localStorage.setItem(watchlistStorageKey,JSON.stringify(next));
      setState(next);setStorageError(false);return true;
    } catch {setStorageError(true);return false;}
  };
  useEffect(()=>{
    const restore=()=>{try{setState(readWatchlist(localStorage.getItem(watchlistStorageKey)));setStorageError(false);}catch{setStorageError(true);}setReady(true);};
    restore();
    const sync=(event:StorageEvent)=>{if(event.key===watchlistStorageKey||event.key===null)restore();};
    window.addEventListener('storage',sync);return()=>window.removeEventListener('storage',sync);
  },[]);
  useEffect(()=>setOffset(0),[symbolsKey]);
  useEffect(()=>{
    if(!ready||!symbolsKey){setData(null);setLoading(false);return;}
    let disposed=false;
    let current:AbortController|null=null;
    const load=async()=>{
      current?.abort();const controller=new AbortController();current=controller;
      setLoading(true);setError(false);setData(null);
      try {
        const result=await loadIntelligence(symbolsKey.split(','),offset,AbortSignal.any([controller.signal,AbortSignal.timeout(20000)]));
        if(!disposed&&!controller.signal.aborted){setData(result);persist(saved=>baselineLegacyReviews(saved,result));}
      } catch {if(!disposed&&!controller.signal.aborted)setError(true);}
      finally {if(!disposed&&!controller.signal.aborted)setLoading(false);}
    };
    void load();
    const visible=()=>{if(document.visibilityState==='visible')void load();};
    const timer=window.setInterval(visible,60000);
    window.addEventListener('focus',visible);document.addEventListener('visibilitychange',visible);
    return()=>{disposed=true;current?.abort();window.clearInterval(timer);window.removeEventListener('focus',visible);document.removeEventListener('visibilitychange',visible);};
  },[ready,symbolsKey,offset,attempt]);
  const refresh=()=>{setOffset(0);setAttempt(n=>n+1);};
  const loaded=data?.stocks.flatMap(row=>[...(row.news?.items||[]),...(row.community?.items||[]),...(row.technical?.items||[])].filter(item=>isUnread(state,row.symbol,item)))||[];
  const more=data?.stocks.some(row=>row.news?.has_more||row.community?.has_more);
  const coverageIncomplete=data?.stocks.some(row=>row.status==='unavailable'||row.news?.truncated||!technicalCountKnown(row.technical))||data?.news_sources.some(s=>s.enabled&&s.status!=='healthy')||data?.community_sources.some(s=>s.enabled&&s.status!=='healthy');
  return <LivePrices symbols={ready?state.symbols:[]} interval={20000}><div className="page-stack">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><div className="eyebrow mb-3">{t('Workspace / Watchlist')}</div><h1>{t('Watchlist')}</h1><p className="mt-2 text-sm text-muted-foreground">{t('What changed for the stocks you follow?')}</p></div>
      <Button variant="outline" disabled={!ready||!state.symbols.length||loading} onClick={refresh}>{t('Refresh updates')}</Button></div>
    <p className="text-xs text-muted-foreground">{t('Saved in this browser only. Reviews are explicit; opening content never marks it reviewed.')}</p>
    {storageError&&<p role="alert" className="rounded border p-3 text-sm">{t('Browser storage is unavailable or saved data cannot be read. Your saved Watchlist has not been overwritten. Reload to retry.')}</p>}
    <form aria-label={t('Follow a stock')} className="flex flex-wrap items-end gap-3" onSubmit={event=>{event.preventDefault();if(selected&&persist(current=>followStock(current,selected)))setSelected('');}}>
      <div className="w-full min-w-0 sm:w-80"><p className="mb-1 text-xs">{t('Stock to follow')}</p><StockSearch label="Stock to follow" onSelect={setSelected} disabled={!ready||storageError||state.symbols.length>=50}/></div>
      <Button disabled={!selected||storageError||!ready||state.symbols.length>=50}>{selected?t('Follow {ticker}',{ticker:selected}):t('Follow stock')}</Button>
      <Link href="/" className="py-2 text-xs text-primary hover:underline">{t('Find more stocks in Explore')}</Link>
    </form>
    {state.symbols.length>=50&&<p className="text-xs text-muted-foreground">{t('This browser Watchlist supports up to 50 stocks.')}</p>}
    {!ready?<MascotState state="loading" role="status">{t('Loading your Watchlist…')}</MascotState>
      :!state.symbols.length?!storageError&&<section className="panel p-5"><MascotState state="emptyWatchlist"><div><h2 className="text-sm">{t('No stocks followed yet')}</h2><p className="mt-1">{t('Choose a stock above to monitor recent developments.')}</p></div></MascotState></section>
      :<>
        {loading?<MascotState state="loading" role="status">{t('Checking recent developments…')}</MascotState>:error?<MascotState state="dataUnavailable" role="alert">{t('Watchlist updates are temporarily unavailable. Counts are unknown.')} <button className="text-primary underline" onClick={refresh}>{t('Retry updates')}</button></MascotState>:data&&<>
          <div role="status" className="flex flex-wrap gap-x-5 gap-y-2 border-y py-3 text-sm"><span>{storageError?t('Review state unavailable. Unread counts are unknown.'):t('{count} unreviewed ticker updates on this page',{count:loaded.length})}</span><span className="text-xs text-muted-foreground">{t('Page {page} · up to 12 items per source and stock',{page:offset/12+1})}</span>{coverageIncomplete&&<span className="text-xs text-amber-700 dark:text-amber-300">{t('Coverage incomplete; counts describe observed items only.')}</span>}</div>
          <details className="text-xs text-muted-foreground"><summary className="cursor-pointer">{t('Actual source freshness')} · {t('Response checked')} {date(data.as_of,true)}</summary>
            <p className="mt-2">{t('News: last 72 hours of ingestion · Community: last 24 hours · Technical: latest accepted session.')}</p>
            <ul className="mt-2 space-y-1">{[...data.news_sources,...data.community_sources].map(source=><li key={source.source_id}>{source.name} · {ui(collectionLabels[source.status])} · {t('Source checked')}: {date(source.last_success_at,true)}</li>)}</ul>
          </details>
        </>}
        <section className="panel divide-y" aria-label={t('Watched stocks')}>{state.symbols.map(symbol=>{
          const row=data?.stocks.find(stock=>stock.symbol===symbol);
          const news=row?.news,community=row?.community,technical=row?.technical;
          const newItems=[...(news?.items||[]),...(community?.items||[]),...(technical?.items||[])].filter(item=>isUnread(state,symbol,item));
          const review=(items:AttentionUpdate[])=>persist(current=>reviewUpdates(current,symbol,items));
          return <article key={symbol} aria-label={t('{ticker} monitoring',{ticker:symbol})} className="grid gap-4 p-4 sm:p-5 md:grid-cols-[170px_minmax(0,1fr)]">
            <div><Link href={'/stocks/'+encodeURIComponent(symbol)} className="text-lg font-semibold text-primary hover:underline">{symbol}</Link><p className="mt-1 break-words text-xs text-muted-foreground">{(language==='vi'?row?.company_name:row?.display_name_en)||row?.company_name||t('Equity metadata unavailable')}</p>
              <div className="mt-3"><LivePrice symbol={symbol}/></div>
              <p className="mt-3 text-xs text-muted-foreground">{storageError?t('Review state unavailable. Unread counts are unknown.'):state.reviewedAt?.[symbol]?<>{t('Last reviewed')}: <time dateTime={state.reviewedAt[symbol]}>{date(state.reviewedAt[symbol],true)}</time></>:t(Object.hasOwn(state.seen,symbol)||Object.hasOwn(state.communitySeen,symbol)?'Legacy review time unavailable':'Not reviewed yet')}</p>
              <button className="mt-3 text-xs text-muted-foreground underline" aria-label={t('Remove {ticker} from Watchlist',{ticker:symbol})} disabled={storageError} onClick={()=>persist(current=>unfollowStock(current,symbol))}>{t('Remove')}</button></div>
            <div className="min-w-0 space-y-4">
              {loading?<p className="text-sm text-muted-foreground">{t('Checking recent developments…')}</p>:error?<p className="text-sm text-muted-foreground">{t('Development count unavailable.')}</p>:row?.status==='unavailable'?<p className="text-sm">{t('Stock data is unavailable. This is not a no-change result.')}</p>:row&&<>
                <div className="flex flex-wrap items-center justify-between gap-2"><p className="text-sm font-medium">{storageError?t('Review state unavailable. Unread counts are unknown.'):newItems.length?t('{count} unreviewed on this page',{count:newItems.length}):t('No unreviewed items on this page')}</p>
                  {!newItems.length&&<button disabled={storageError} className="text-xs text-primary underline disabled:opacity-50" onClick={()=>review([])}>{t('Mark this check reviewed')}</button>}</div>
                {news&&<UpdateSection key={'news-'+offset} label={t('News')} page={news} symbol={symbol} state={state} disabled={storageError} review={review}/>}
                {community&&<UpdateSection key={'community-'+offset} label={t('Community')} page={community} symbol={symbol} state={state} disabled={storageError} review={review} sourceNames={Object.fromEntries(data?.community_sources.map(source=>[source.source_id,source.name])||[])}/>}
                {technical&&<section aria-label={t('Technical updates')} className="border-t pt-3">
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-medium">{t('Technical updates')} · {storageError||!technicalCountKnown(technical)?t('Count unavailable'):t('{count} unreviewed on this page',{count:technical.items.filter(item=>isUnread(state,symbol,item)).length})}</h3>
                    {technical.items.length>0&&<button aria-label={t('Mark displayed {kind} reviewed',{kind:t('Technical updates')})} disabled={storageError} className="text-xs text-primary underline disabled:opacity-50" onClick={()=>review(technical.items.slice(0,3))}>{t('Review displayed')}</button>}</div>
                  {technical.waiting_for_gate||technical.awaiting_source_check?<div className="text-sm text-muted-foreground"><p>{t(technical.waiting_for_gate?'Technical data pending the delayed EOD gate':'Delayed EOD gate elapsed; awaiting source check')}</p><p className="mt-1 text-xs">{t('Next source check due')}: {date(technical.next_check_due_at,true)}</p><p className="mt-1 text-xs">{t('Source checked')}: {date(technical.last_checked_at,true)}</p></div>
                    :<TechnicalInsightsView sectionId={'watchlist-technical-'+symbol} ticker={symbol} data={technical.data} loading={false} error={false} retry={refresh}/>}
                </section>}
              </>}
              <div className="flex flex-wrap gap-4 text-xs"><Link className="text-primary hover:underline" href={'/stocks/'+encodeURIComponent(symbol)}>{t('Open {ticker} stock detail',{ticker:symbol})}</Link><Link className="text-primary hover:underline" href={'/news?'+newsViewQuery({...emptyNewsFilters,ticker:symbol},'company')}>{t('News mentioning {ticker}',{ticker:symbol})}</Link><Link className="text-primary hover:underline" href={'/news?'+newsViewQuery({...emptyNewsFilters,ticker:symbol},'community')}>{t('Community Pulse')}</Link></div>
            </div>
          </article>;
        })}</section>
        {data&&<div className="flex flex-wrap items-center justify-between gap-3"><Button variant="outline" disabled={loading||offset===0} onClick={()=>setOffset(value=>Math.max(0,value-12))}>{t('Previous page')}</Button><span className="text-xs text-muted-foreground">{t('Page {page} · up to 12 items per source and stock',{page:offset/12+1})}</span><Button variant="outline" disabled={loading||!more||offset>=984} onClick={()=>setOffset(value=>value+12)}>{t('Next page')}</Button></div>}
      </>}
  </div></LivePrices>;
}
