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
import WatchlistBriefing from '../components/WatchlistBriefing';
import QuoteMap from '../components/stock/QuoteMap';
import {reviewBriefingItem} from '@/lib/dailyBriefing';
import {safeExternalUrl} from '@/lib/presentation';
import {emptyNewsFilters,newsViewQuery,type NewsArticle} from '@/lib/news';
import type {CommunityItem} from '@/lib/community';
import {collectionLabels} from '@/lib/collectionStatus';
import {emptyWatchlist,readWatchlist,followStock,unfollowStock,watchlistStorageKey,loadIntelligence,isUnread,reviewUpdates,baselineLegacyReviews,uniqueUpdates,technicalCountKnown,type WatchlistState,type Intelligence,type AttentionUpdate,type UpdatePage} from '@/lib/watchlist';

function UpdateSection({label,page,symbol,state,disabled,sourceNames={}}: {label:string;page:UpdatePage;symbol:string;state:WatchlistState;disabled:boolean;sourceNames?:Record<string,string>}) {
  const {t,date}=useLocale();
  const [expanded,setExpanded]=useState(false);
  const rows=uniqueUpdates(page.items);
  rows.sort((a,b)=>Number(isUnread(state,symbol,b))-Number(isUnread(state,symbol,a)) || b.occurred_at.localeCompare(a.occurred_at) || a.id.localeCompare(b.id));
  const unread=rows.filter(item=>isUnread(state,symbol,item));
  // All loaded unread items remain visible. Older reviewed rows are secondary.
  const shown=expanded||disabled?rows:unread.length?unread:rows.slice(0,1);
  if(!rows.length)return (page.has_more||page.truncated)?<p className="text-xs text-amber-700 dark:text-amber-300">{label} · {t('The bounded source sample is incomplete. Open the source archive for more.')}</p>:null;
  return <section aria-label={label}>
    <h3 className="mb-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">{label}{label===t('Community')?' · '+t('Unverified'):''}</h3>
    <ul className="divide-y">{shown.map(item=>{
        const url=safeExternalUrl(item.url);
        const revised=!!state.receipts?.[symbol]?.[item.id]&&isUnread(state,symbol,item);
        const discussion=item.kind==='community'?item.evidence as CommunityItem:null;
        const publisher=item.kind==='news'?(item.evidence as NewsArticle[])[0]?.source_name:discussion?sourceNames[discussion.source_id]||discussion.source_id:null;
        const published=item.kind==='news'?(item.evidence as NewsArticle[])[0]?.published_at:null;
        return <li key={item.id} data-update={item.id} data-unread={!disabled&&isUnread(state,symbol,item)} className="py-2">
          <h4 className={`break-words text-sm leading-5 ${!disabled&&isUnread(state,symbol,item)?'font-medium':'text-muted-foreground'}`}>{url?<a href={url} target="_blank" rel="noopener noreferrer" className="rounded-sm hover:text-primary focus-visible:outline focus-visible:outline-2">{item.title}</a>:item.title}</h4>
          <div className="mt-1 flex flex-wrap gap-x-2 gap-y-1 text-[11px] text-muted-foreground">{publisher&&<span>{publisher}</span>}<time dateTime={published||item.occurred_at}>{date(published||item.occurred_at,true)}</time>
            {!disabled&&<span className={isUnread(state,symbol,item)?'text-primary':''}>{t(isUnread(state,symbol,item)?revised?'Updated since review':'Unreviewed':'Reviewed')}</span>}{discussion?.is_fixture&&<span>{t('Fixture')}</span>}</div>
        </li>;
      })}</ul>
    {rows.length>shown.length||expanded?<button className="mt-1 text-xs text-primary hover:underline" onClick={()=>setExpanded(v=>!v)}>{t(expanded?'Show fewer updates':'Show all {count} loaded updates',{count:rows.length})}</button>:null}
    {(page.has_more||page.truncated)&&<p className="mt-2 text-xs text-amber-700 dark:text-amber-300">{t(page.truncated?'The bounded source sample is incomplete. Open the source archive for more.':'More updates are available on the next page.')}</p>}
  </section>;
}

function ReviewEvidence({items,symbol,state,disabled,review}: {items:AttentionUpdate[];symbol:string;state:WatchlistState;disabled:boolean;review:(items:AttentionUpdate[])=>void}){
  const {t}=useLocale();
  return <ul className="mt-3 divide-y">{uniqueUpdates(items).map(item=><li key={item.id} className="py-3" data-review-update={item.id}>
    <div className="flex items-start justify-between gap-4"><div className="min-w-0"><p className="text-[11px] text-muted-foreground">{t(item.kind==='news'?'News':item.kind==='community'?'Community':'Technical updates')}</p><p className="mt-1 text-xs">{item.title}</p></div>
      <button aria-label={t('Review update: {title}',{title:item.title})} disabled={disabled||!isUnread(state,symbol,item)} className="shrink-0 text-xs text-primary underline disabled:text-muted-foreground" onClick={()=>review([item])}>{t(isUnread(state,symbol,item)?'Mark reviewed':'Reviewed')}</button></div>
    <details className="mt-2 text-xs"><summary className="cursor-pointer text-muted-foreground">{t('View source evidence')}</summary>{item.kind==='news'?(item.evidence as NewsArticle[]).map(article=><ArticleRow key={article.id} article={article} requireImage={false} associations={item.ticker_associations}/>):<pre className="mt-2 whitespace-pre-wrap break-all rounded bg-muted/40 p-3">{JSON.stringify(item.evidence,null,2)}</pre>}{item.evidence_truncated&&<p className="mt-2">{t('Additional source evidence is available in News.')}</p>}</details>
  </li>)}</ul>;
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
  const activityCount=(symbol:string)=>{const row=data?.stocks.find(stock=>stock.symbol===symbol);return [...(row?.news?.items||[]),...(row?.community?.items||[]),...(row?.technical?.items||[])].filter(item=>isUnread(state,symbol,item)).length;};
  const orderedSymbols=[...state.symbols].sort((a,b)=>activityCount(b)-activityCount(a)||state.symbols.indexOf(a)-state.symbols.indexOf(b));
  const more=data?.stocks.some(row=>row.news?.has_more||row.community?.has_more);
  const coverageIncomplete=data?.stocks.some(row=>row.status==='unavailable'||row.news?.truncated||!technicalCountKnown(row.technical))||data?.news_sources.some(s=>s.enabled&&s.status!=='healthy')||data?.community_sources.some(s=>s.enabled&&s.status!=='healthy');
  return <LivePrices symbols={ready?state.symbols:[]} interval={20000}><div className="page-stack">
    <div className="flex flex-wrap items-start justify-between gap-3"><div><div className="eyebrow mb-3">{t('Workspace / Watchlist')}</div><h1>{t('Watchlist')}</h1><p className="mt-2 text-sm text-muted-foreground">{t('What changed for the stocks you follow?')}</p></div>
      <Button variant="outline" disabled={!ready||!state.symbols.length||loading} onClick={refresh}>{t('Refresh updates')}</Button></div>
    <details className="text-xs text-muted-foreground"><summary>{ui('Review & storage')}</summary><p>{t('Saved in this browser only. Reviews are explicit; opening content never marks it reviewed.')}</p></details>
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
          <div role="status" className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground">{storageError&&<span>{t('Review state unavailable. Unread counts are unknown.')}</span>}{coverageIncomplete&&<span className="text-amber-700 dark:text-amber-300">{t('Coverage incomplete; counts describe observed items only.')}</span>}</div>
          <details className="text-xs text-muted-foreground"><summary className="cursor-pointer">{t('Actual source freshness')} · {t('Response checked')} {date(data.as_of,true)}</summary>
            <p className="mt-2">{t('News: last 72 hours of ingestion · Community: last 24 hours · Technical: latest accepted session.')}</p>
            <ul className="mt-2 space-y-1">{[...data.news_sources,...data.community_sources].map(source=><li key={source.source_id}>{source.name} · {ui(collectionLabels[source.status])} · {t('Source checked')}: {date(source.last_success_at,true)}</li>)}</ul>
          </details>
        </>}
        {!loading&&!error&&data&&<WatchlistBriefing data={data} state={state} storageError={storageError} review={entry=>persist(current=>reviewBriefingItem(current,state,entry))}/>}
        <details className="panel p-4"><summary className="cursor-pointer text-sm font-medium">{t('Price map · followed stocks')}</summary>
          <div className="mt-3"><QuoteMap scope="watchlist" stocks={state.symbols.map(symbol=>{const row=data?.stocks.find(stock=>stock.symbol===symbol);return {symbol,company_name:row?.company_name,display_name_en:row?.display_name_en,exchange:row?.exchange};})}/></div>
        </details>
        <section id="watched-stocks" className="panel divide-y scroll-mt-20" aria-label={t('Watched stocks')}>{orderedSymbols.map(symbol=>{
          const row=data?.stocks.find(stock=>stock.symbol===symbol);
          const news=row?.news,community=row?.community,technical=row?.technical;
          const newItems=[...(news?.items||[]),...(community?.items||[]),...(technical?.items||[])].filter(item=>isUnread(state,symbol,item));
          const review=(items:AttentionUpdate[])=>persist(current=>reviewUpdates(current,symbol,items));
          return <article key={symbol} aria-label={t('{ticker} monitoring',{ticker:symbol})} className="grid gap-4 p-4 sm:p-5 md:grid-cols-[170px_minmax(0,1fr)]">
            <div><Link href={'/stocks/'+encodeURIComponent(symbol)} className="text-lg font-semibold text-primary hover:underline">{symbol}</Link><p className="mt-1 break-words text-xs text-muted-foreground">{(language==='vi'?row?.company_name:row?.display_name_en)||row?.company_name||t('Equity metadata unavailable')}</p>
              <div className="mt-3"><LivePrice symbol={symbol}/></div>
              </div>
            <div className="min-w-0 space-y-4">
              {loading?<p className="text-sm text-muted-foreground">{t('Checking recent developments…')}</p>:error?<p className="text-sm text-muted-foreground">{t('Development count unavailable.')}</p>:row?.status==='unavailable'?<p className="text-sm">{t('Stock data is unavailable. This is not a no-change result.')}</p>:row&&<>
                <div className="flex flex-wrap items-center justify-between gap-2"><p className="text-sm font-medium">{storageError?t('Review state unavailable. Unread counts are unknown.'):newItems.length?t('{count} unreviewed on this page',{count:newItems.length}):t('No unreviewed items on this page')}</p>
                  </div>
                {news&&<UpdateSection key={'news-'+offset} label={t('News')} page={news} symbol={symbol} state={state} disabled={storageError}/>}
                {community&&<UpdateSection key={'community-'+offset} label={t('Community')} page={community} symbol={symbol} state={state} disabled={storageError} sourceNames={Object.fromEntries(data?.community_sources.map(source=>[source.source_id,source.name])||[])}/>}
                {technical?.items.length? <UpdateSection label={t('Technical updates')} page={technical} symbol={symbol} state={state} disabled={storageError}/>:null}
                <details id={'watchlist-evidence-'+encodeURIComponent(symbol)} className="border-t pt-2 text-xs scroll-mt-20"><summary className="cursor-pointer text-primary">{t('Review & evidence')}</summary>
                  <p className="mt-2 text-muted-foreground">{t('Saved in this browser only. Reviews are explicit; opening content never marks it reviewed.')}</p>
                  <ReviewEvidence items={[...(news?.items||[]),...(community?.items||[]),...(technical?.items||[])]} symbol={symbol} state={state} disabled={storageError} review={review}/>
                  {!newItems.length&&<button disabled={storageError} className="mt-2 text-primary underline disabled:opacity-50" onClick={()=>review([])}>{t('Mark this check reviewed')}</button>}
                {technical&&<details open={technical.items.length>0} aria-label={t('Technical updates')} className="border-t pt-3"><summary className="cursor-pointer text-sm">{t('Technical updates')} · {ui(technical.waiting_for_gate?'Technical data pending the delayed EOD gate':technical.awaiting_source_check?'Delayed EOD gate elapsed; awaiting source check':technicalCountKnown(technical)?'Inspect technical evidence':'Count unavailable')}</summary>
                  {technical.waiting_for_gate||technical.awaiting_source_check?<div className="text-sm text-muted-foreground"><p>{t(technical.waiting_for_gate?'Technical data pending the delayed EOD gate':'Delayed EOD gate elapsed; awaiting source check')}</p><p className="mt-1 text-xs">{t('Next source check due')}: {date(technical.next_check_due_at,true)}</p><p className="mt-1 text-xs">{t('Source checked')}: {date(technical.last_checked_at,true)}</p></div>
                    :<TechnicalInsightsView sectionId={'watchlist-technical-'+symbol} ticker={symbol} data={technical.data} loading={false} error={false} retry={refresh}/>}
                </details>}
                  <div className="mt-3 flex flex-wrap gap-4 text-muted-foreground"><Link className="text-primary hover:underline" href={'/news?'+newsViewQuery({...emptyNewsFilters,ticker:symbol},'company')}>{t('News mentioning {ticker}',{ticker:symbol})}</Link><Link className="text-primary hover:underline" href={'/news?'+newsViewQuery({...emptyNewsFilters,ticker:symbol},'community')}>{t('Community Pulse')}</Link><button className="underline" aria-label={t('Remove {ticker} from Watchlist',{ticker:symbol})} disabled={storageError} onClick={()=>persist(current=>unfollowStock(current,symbol))}>{t('Remove')}</button></div>
                  {state.reviewedAt?.[symbol]&&<p className="mt-2 text-muted-foreground">{t('Last reviewed')}: {date(state.reviewedAt[symbol],true)}</p>}
                </details>
              </>}
            </div>
          </article>;
        })}</section>
        {data&&<div className="flex flex-wrap items-center justify-between gap-3"><Button variant="outline" disabled={loading||offset===0} onClick={()=>setOffset(value=>Math.max(0,value-12))}>{t('Previous page')}</Button><span className="text-xs text-muted-foreground">{t('Page {page} · up to 12 items per source and stock',{page:offset/12+1})}</span><Button variant="outline" disabled={loading||!more||offset>=984} onClick={()=>setOffset(value=>value+12)}>{t('Next page')}</Button></div>}
      </>}
  </div></LivePrices>;
}
