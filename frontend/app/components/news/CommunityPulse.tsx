"use client";
import {useLocale} from "@/lib/i18n";
import { useEffect, useState } from "react";
import Link from "next/link";
import {emptyNewsFilters,newsViewQuery} from '@/lib/news';
import {collectionLabels} from "@/lib/collectionStatus";
import {safeExternalUrl} from "@/lib/presentation";
import { loadCommunity } from "@/lib/community";
import type { CommunityPulseData } from "@/lib/community";
import { CommunityDiscussions } from "../stock/StockCommunity";

export default function CommunityPulse({ ticker, topic, attempt, compact=false, initialWindow="today", onWindowChange, onTickerChange }: { ticker: string; topic: string; attempt: number; compact?: boolean; initialWindow?: "today"|"last24h"; onWindowChange?: (window:"today"|"last24h")=>void; onTickerChange?: (ticker:string)=>void }) {
  const {t,ui,date:localDate}=useLocale();
  const [window,setWindow]=useState<"today"|"last24h">(initialWindow);
  useEffect(()=>{setWindow(initialWindow);},[initialWindow]);
  const [data, setData] = useState<CommunityPulseData | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  const [draftTicker, setDraftTicker] = useState(ticker);
  const [selectedTicker, setSelectedTicker] = useState(ticker);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError(false);
    const load = () => loadCommunity(selectedTicker, "", controller.signal,window).then(rows => {
      if (!controller.signal.aborted) { setData(rows); setError(false); }
    }).catch(() => { if (!controller.signal.aborted) setError(true); });
    void load();
    const timer = setInterval(load, 15 * 60 * 1000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [selectedTicker, attempt, retry, window]);
  const selectWindow=(next:"today"|"last24h")=>{setWindow(next);onWindowChange?.(next);};
  const selectTicker=(value:string)=>{const next=value.trim().toUpperCase();setDraftTicker(next);setSelectedTicker(next);onTickerChange?.(next);};
  const discussionHref=(ticker="")=>"/news?"+newsViewQuery({...emptyNewsFilters,ticker},"community",window);
  // News topics are publisher taxonomy, separate from Community extraction.
  void topic;
  if(compact)return <section aria-label={ui('Investor Attention')}>
    <div className="flex items-center justify-between gap-3 text-xs"><select aria-label={t('Discussion window')} value={window} onChange={e=>selectWindow(e.target.value as 'today'|'last24h')} className="h-8 rounded border bg-background px-2"><option value="today">{t('Today')}</option><option value="last24h">{t('Last 24 hours')}</option></select><span className="text-muted-foreground">{ui('Discussion activity, not sentiment.')}</span></div>
    {error&&<p role="alert" className="mt-4 text-sm">{ui('Community unavailable')} <button onClick={()=>setRetry(n=>n+1)} className="text-primary underline">{t('Retry')}</button></p>}
    {!data&&!error&&<p role="status" className="mt-4 text-sm">{ui('Loading discussions…')}</p>}
    {data&&<>{data.items.some(item=>item.is_fixture)&&<p role="status" className="mt-3 text-xs text-amber-700 dark:text-amber-300">{t('Fixture')} · {ui('Sample includes fixture data')}</p>}<p className="mt-4 text-xs text-muted-foreground">{t(data.unique_items===1?'{count} sampled discussion':'{count} sampled discussions',{count:data.unique_items})} · {localDate(data.as_of,true)}{data.coverage_partial||data.truncated?' · '+ui('Partial coverage'):''}{data.sources.some(source=>source.enabled&&source.status!=='healthy')?' · '+ui('Discussion coverage stale or unavailable'):''}</p>
      <div className="mt-4 space-y-4">{data.active_tickers.slice(0,5).map(row=><div key={row.ticker}><div className="mb-1 flex items-center justify-between text-sm"><Link href={`/stocks/${encodeURIComponent(row.ticker)}`} className="font-semibold text-primary hover:underline">{row.ticker}</Link><Link href={discussionHref(row.ticker)} className="text-xs text-muted-foreground hover:underline">{t(row.item_count===1?'{count} discussion':'{count} discussions',{count:row.item_count})}</Link></div><div className="attention-bar" style={{width:`${Math.max(3,row.item_count/Math.max(...data.active_tickers.map(r=>r.item_count),1)*100)}%`}}/></div>)}</div>
      {!data.unique_items&&<p className="mt-4 text-sm text-muted-foreground">{ui('No discussions in this sample.')}</p>}
      {data.themes.slice(0,2).map(theme=><Link key={theme.id} href={discussionHref()} className="mt-4 block text-sm hover:text-primary">{ui(theme.label)} <span className="text-xs text-muted-foreground">· {theme.item_count}</span></Link>)}
      <details className="mt-4 text-xs text-muted-foreground"><summary className="cursor-pointer">{ui('Sample & sources')}</summary><p className="mt-2">{ui('Unverified discussion sample; no market sentiment is inferred.')}</p>{data.sources.filter(source=>source.enabled).map(source=><p key={source.source_id}>{source.name} · {ui(collectionLabels[source.status])} · {localDate(source.last_success_at,true)}</p>)}{data.items.slice(0,3).map(item=><a key={item.id} href={safeExternalUrl(item.url)||undefined} target="_blank" rel="noopener noreferrer" className="mt-2 block text-primary hover:underline">{item.title||ui('Read original ↗')}{item.is_fixture?' · '+t('Fixture'):''}</a>)}</details>
    </>}
  </section>;
  return <section aria-label={t("Community Pulse")}>
    <div className="flex flex-wrap items-center justify-between gap-3"><label className="text-xs">{t("Discussion window")}<select aria-label={t("Discussion window")} value={window} onChange={e=>selectWindow(e.target.value as "today"|"last24h")} className="ml-2 h-9 rounded border bg-background px-2"><option value="today">{t("Today")}</option><option value="last24h">{t("Last 24 hours")}</option></select></label></div>
    {!compact&&<form className="mt-4 flex flex-wrap items-center gap-3" onSubmit={event => { event.preventDefault(); selectTicker(draftTicker); }}><label className="text-xs">{t("Discussion ticker")}<input aria-label={t("Discussion ticker")} value={draftTicker} onChange={event => setDraftTicker(event.target.value)} placeholder={t("Any ticker")} maxLength={20} className="ml-3 h-9 rounded border bg-background px-2 text-sm"/></label><button className="text-sm text-primary" type="submit">{t("Apply")}</button>{selectedTicker && <button type="button" className="text-xs text-primary" onClick={() => selectTicker("")}>{t("Clear discussion filter")}</button>}</form>}
    {compact&&selectedTicker&&<button type="button" className="mt-3 text-xs text-primary underline" onClick={()=>selectTicker('')}>{t('Clear discussion filter')} · {selectedTicker}</button>}
    {data && !error && <div className="mt-4 flex flex-wrap gap-4 text-xs"><span className="text-muted-foreground">{t("Active tickers ·")} {ui(data.window.label)}, {localDate(data.window.start)}:</span>{data.active_tickers.slice(0,compact?6:12).map(row => <span key={row.ticker}><button className="text-primary underline" onClick={() => selectTicker(row.ticker)}>{row.ticker} ({row.item_count})</button> <Link aria-label={t("Research {ticker}",{ticker:row.ticker})} href={`/stocks/${encodeURIComponent(row.ticker)}`} className="text-muted-foreground">{t("Research ↗")}</Link></span>)}</div>}
    <div className="mt-5"><CommunityDiscussions key={selectedTicker} ticker={selectedTicker || "Market"} showHeading={false} compact={compact} data={data} loading={!data && !error} error={error} retry={() => setRetry(value => value + 1)}/></div>
  </section>;
}
