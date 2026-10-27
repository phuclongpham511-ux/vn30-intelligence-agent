"use client";
import {useLocale} from "@/lib/i18n";
import { useEffect, useState } from "react";
import { MascotState } from "../components/mascot/Mascot";
import { Button } from "../components/ui/button";
import SourceCoverage from "../components/news/SourceCoverage";
import TopStory from "../components/news/TopStory";
import {LivePrices} from "../components/stock/LivePrice";
import {newsSymbols} from "@/lib/newsPresentation";
import {useNewsArchive} from "@/lib/useNewsArchive";
import CommunityPulse from "../components/news/CommunityPulse";
import { emptyNewsFilters, newsQuery, readNewsFilters, newsViewQuery, readNewsView, newsSectionLabels, readCommunityWindow } from "@/lib/news";
import type { NewsFilters, NewsSource, NewsView } from "@/lib/news";


export default function NewsPage() {
  const {t,ui}=useLocale();
  const [filters, setFilters] = useState<NewsFilters>(emptyNewsFilters);
  const [draft, setDraft] = useState<NewsFilters>(emptyNewsFilters);
  const [sources, setSources] = useState<NewsSource[]>([]);
  const [ready, setReady] = useState(false);
  const [view, setView] = useState<NewsView>("industry");
  const [communityWindow, setCommunityWindow] = useState<'today'|'last24h'>('today');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const sync = () => {
      const initial = readNewsFilters(window.location.search);
      const mode = readNewsView(window.location.search);
      setView(mode.view);
      setCommunityWindow(readCommunityWindow(window.location.search));
      setFilters(initial); setDraft(initial); setReady(true);
    };
    sync();
    window.addEventListener("popstate", sync);
    const controller = new AbortController();
    fetch("/api/news/sources", { signal: controller.signal }).then(async response => {
      if (response.ok) {
        const rows = await response.json();
        if (!controller.signal.aborted) setSources(rows);
      }
    }).catch(() => {});
    return () => { window.removeEventListener("popstate", sync); controller.abort(); };
  }, []);
  useEffect(() => {
    if (ready) {
      const query = newsViewQuery(filters, view, communityWindow);
      window.history.replaceState(null, '', `/news${query ? `?${query}` : ''}`);
    }
  }, [filters, ready, view, communityWindow]);
  const category=view==='community'?null:{company:'COMPANY',industry:'INDUSTRY',briefing:'MARKET_BRIEF'}[view];
  const {page:data,loading,error,loadMore}=useNewsArchive(ready&&category?`research_category=${category}&${newsQuery(filters)}`:null,attempt);
  return <div className="page-stack news-page">
    <header className="news-page-header"><div><div className="eyebrow">{t("News")}</div><h1>{t("Market Today")}</h1><p>{t("Company reporting, industry developments and market-wide attention.")}</p></div><div className="news-header-actions"><SourceCoverage attempt={attempt}/><Button variant="outline" disabled={loading && view !== "community"} onClick={() => setAttempt(value => value + 1)}>{t("Refresh")}</Button></div></header>
    <nav aria-label={t("News sections")} className="news-section-nav">{(Object.entries(newsSectionLabels) as [NewsView, string][]).map(([key, label]) => <button key={key} type="button" aria-pressed={view === key} onClick={() => setView(key)}>{ui(label)}</button>)}</nav>
    {view !== "community" && <form aria-label={t("Filter news")} onSubmit={event => { event.preventDefault(); setFilters({ ...draft }); }} className="news-filter-toolbar">
      <label className="text-xs">{t("Ticker")}<input value={draft.ticker} onChange={event => setDraft({ ...draft, ticker: event.target.value })} maxLength={20} placeholder={t("Any ticker")} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"/></label>

      <label className="text-xs">{t("Country")}<select value={draft.country} onChange={event => setDraft({ ...draft, country: event.target.value })} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"><option value="">{t("All countries")}</option>{[...new Set([...sources.map(source => source.country), ...(draft.country ? [draft.country] : [])])].sort().map(country => <option key={country} value={country}>{country}</option>)}</select></label>
      <label className="text-xs">{t("Source")}<select value={draft.source} onChange={event => setDraft({ ...draft, source: event.target.value })} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"><option value="">{t("All sources")}</option>{sources.map(source => <option key={source.source_id} value={source.source_id}>{source.name}{!source.enabled && " ("+t("disabled")+")"}</option>)}{draft.source && !sources.some(source => source.source_id === draft.source) && <option value={draft.source}>{draft.source}</option>}</select></label>
      <label className="text-xs">{t("Topic")}<input value={draft.topic} onChange={event => setDraft({ ...draft, topic: event.target.value })} placeholder={t("Any topic")} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"/></label>
      <Button type="submit" variant="outline">{t("Apply filters")}</Button>
      <button type="button" className="pb-2 text-xs text-primary underline" onClick={() => { setDraft(emptyNewsFilters); setFilters(emptyNewsFilters); }}>{t("Clear all")}</button>
      <details className="news-advanced-filter" open={Boolean(draft.sector)}><summary>{t("Advanced: headline sector tags (partial coverage)")}</summary><label>{t("Sector")}<select value={draft.sector} onChange={event => setDraft({ ...draft, sector: event.target.value })}><option value="">{t("All sector tags")}</option>{[...new Set(["Financials", "Real Estate", "Technology", "Energy", "Consumer", "Industrials", ...(draft.sector ? [draft.sector] : [])])].map(sector => <option key={sector} value={sector}>{ui(sector)}</option>)}</select></label><p>{t("Headline tags only. Company sector mapping is currently incomplete; use ticker or topic for broader coverage.")}</p></details>
    </form>}
    {view !== "community" && newsQuery(filters) && <p className="text-xs text-muted-foreground">{t("Publisher sections show this filtered view. These filters do not change story ranking or factual tags.")}</p>}
    {view === "community" && <CommunityPulse key={filters.ticker} ticker={filters.ticker} topic="" attempt={attempt} initialWindow={communityWindow} onWindowChange={setCommunityWindow} onTickerChange={ticker=>{setFilters(current=>({...current,ticker}));setDraft(current=>({...current,ticker}));}}/>}
    {view !== "community" && error && <MascotState state="dataUnavailable" role="alert">{t("News is temporarily unavailable.")} {data && t("Previously loaded headlines are shown below.")} <button className="ml-2 text-primary underline" onClick={() => setAttempt(value => value + 1)}>{t("Retry")}</button></MascotState>}
    {view !== "community" && loading && !data && <MascotState state="loading" role="status">{t("Loading news…")}</MascotState>}
    {view !== "community" && data && <>
      <section aria-label={ui(newsSectionLabels[view])}>
        {!data.items.length && <MascotState state="noMatches">{t("No qualifying recent reporting matches this view. Coverage may be incomplete.")}</MascotState>}
        <LivePrices symbols={newsSymbols(data.items)} interval={30000}><div className="news-results">
          {data.items[0]&&<TopStory key={data.items[0].story.id} item={data.items[0]} featured reserveThumbnailSpace/>}
          {data.items.length>1&&<div className="news-results-grid">{data.items.slice(1).map(item=><TopStory key={item.story.id} item={item} compact reserveThumbnailSpace/>)}</div>}
        </div></LivePrices>
        <div className="mt-6 flex flex-col items-center gap-2">
          {data.has_more&&<Button variant="outline" disabled={loading} onClick={loadMore}>{t(loading?"Loading more…":"Show more")}</Button>}
          <details className="text-xs text-muted-foreground"><summary>{ui("About this feed")}</summary><p>{t("Qualified reporting appears with or without a source image.")}</p><p>{t("Reporting from the last 72 hours. Older items appear when you choose Show more.")}</p><details className="mt-3"><summary>{t("Source archive")}</summary><ul className="mt-2 space-y-2">{data.items.map(item=><li key={item.story.id}><a className="underline focus-visible:ring-2 focus-visible:ring-primary" href={`/news/stories/${item.story.id}`}>{item.representative_article.title}</a></li>)}</ul></details></details>
        </div>
      </section>
    </>}
  </div>;
}
