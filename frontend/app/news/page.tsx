"use client";
import {useLocale} from "@/lib/i18n";
import { useEffect, useState } from "react";
import { MascotState } from "../components/mascot/Mascot";
import { Button } from "../components/ui/button";
import SourceCoverage from "../components/news/SourceCoverage";
import TopStory from "../components/news/TopStory";
import {useNewsArchive} from "@/lib/useNewsArchive";
import CommunityPulse from "../components/news/CommunityPulse";
import { emptyNewsFilters, newsQuery, readNewsFilters, newsViewQuery, readNewsView, newsSectionLabels } from "@/lib/news";
import type { NewsFilters, NewsSource, NewsView } from "@/lib/news";


export default function NewsPage() {
  const {t,ui}=useLocale();
  const [filters, setFilters] = useState<NewsFilters>(emptyNewsFilters);
  const [draft, setDraft] = useState<NewsFilters>(emptyNewsFilters);
  const [sources, setSources] = useState<NewsSource[]>([]);
  const [ready, setReady] = useState(false);
  const [view, setView] = useState<NewsView>("industry");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const sync = () => {
      const initial = readNewsFilters(window.location.search);
      const mode = readNewsView(window.location.search);
      setView(mode.view);
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
      const query = newsViewQuery(filters, view);
      window.history.replaceState(null, '', `/news${query ? `?${query}` : ''}`);
    }
  }, [filters, ready, view]);
  const category=view==='community'?null:{company:'COMPANY',industry:'INDUSTRY',briefing:'MARKET_BRIEF'}[view];
  const {page:data,loading,error,loadMore}=useNewsArchive(ready&&category?`research_category=${category}&${newsQuery(filters)}`:null,attempt);
  return <div className="page-stack">
    <div className="flex items-start justify-between gap-4"><div><div className="eyebrow mb-3">{t("News")}</div><h1>{t("Market Today")}</h1><p className="mt-2 text-sm text-muted-foreground">{t("Company reporting, industry developments and market-wide attention.")}</p></div><Button variant="outline" disabled={loading && view !== "community"} onClick={() => setAttempt(value => value + 1)}>{t("Refresh")}</Button></div>
    <SourceCoverage attempt={attempt}/>
    <div className="flex flex-wrap items-center justify-between gap-3">
      <nav aria-label={t("News sections")} className="flex flex-wrap gap-2">{(Object.entries(newsSectionLabels) as [NewsView, string][]).map(([key, label]) => <button key={key} type="button" aria-pressed={view === key} onClick={() => setView(key)} className={`rounded border px-3 py-2 text-sm ${view === key ? "border-primary text-primary" : "text-muted-foreground hover:bg-muted"}`}>{ui(label)}</button>)}</nav>
    </div>
    {view !== "community" && <details className="rounded border p-3" key={newsQuery(filters) ? "filtered" : "unfiltered"} open={Boolean(newsQuery(filters))}>
    <summary className="cursor-pointer text-sm">{t("Filter news")}{newsQuery(filters) ? " · "+t("Filters active") : ""}</summary>
    <form aria-label={t("Filter news")} onSubmit={event => { event.preventDefault(); setFilters({ ...draft }); }} className="flex flex-wrap items-end gap-3 pt-4">
      <label className="text-xs">{t("Ticker")}<input value={draft.ticker} onChange={event => setDraft({ ...draft, ticker: event.target.value })} maxLength={20} placeholder={t("Any ticker")} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"/></label>

      <label className="text-xs">{t("Country")}<select value={draft.country} onChange={event => setDraft({ ...draft, country: event.target.value })} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"><option value="">{t("All countries")}</option>{[...new Set([...sources.map(source => source.country), ...(draft.country ? [draft.country] : [])])].sort().map(country => <option key={country} value={country}>{country}</option>)}</select></label>
      <label className="text-xs">{t("Source")}<select value={draft.source} onChange={event => setDraft({ ...draft, source: event.target.value })} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"><option value="">{t("All sources")}</option>{sources.map(source => <option key={source.source_id} value={source.source_id}>{source.name}{!source.enabled && " ("+t("disabled")+")"}</option>)}{draft.source && !sources.some(source => source.source_id === draft.source) && <option value={draft.source}>{draft.source}</option>}</select></label>
      <label className="text-xs">{t("Topic")}<input value={draft.topic} onChange={event => setDraft({ ...draft, topic: event.target.value })} placeholder={t("Any topic")} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"/></label>
      <Button type="submit" variant="outline">{t("Apply filters")}</Button>
      <button type="button" className="pb-2 text-xs text-primary underline" onClick={() => { setDraft(emptyNewsFilters); setFilters(emptyNewsFilters); }}>{t("Clear all")}</button>
      <details className="w-full text-xs" open={Boolean(draft.sector)}><summary className="cursor-pointer text-muted-foreground">{t("Advanced: headline sector tags (partial coverage)")}</summary><label className="mt-3 block">{t("Sector")}<select value={draft.sector} onChange={event => setDraft({ ...draft, sector: event.target.value })} className="ml-3 h-9 rounded border bg-background px-2"><option value="">{t("All sector tags")}</option>{[...new Set(["Financials", "Real Estate", "Technology", "Energy", "Consumer", "Industrials", ...(draft.sector ? [draft.sector] : [])])].map(sector => <option key={sector} value={sector}>{ui(sector)}</option>)}</select></label><p className="mt-2 text-muted-foreground">{t("Headline tags only. Company sector mapping is currently incomplete; use ticker or topic for broader coverage.")}</p></details>
    </form>
    </details>}
    {view !== "community" && newsQuery(filters) && <p className="text-xs text-muted-foreground">{t("Publisher sections show this filtered view. These filters do not change story ranking or factual tags.")}</p>}
    {view === "community" && <CommunityPulse ticker="" topic="" attempt={attempt}/>}
    {view !== "community" && error && <MascotState state="dataUnavailable" role="alert">{t("News is temporarily unavailable.")} {data && t("Previously loaded headlines are shown below.")} <button className="ml-2 text-primary underline" onClick={() => setAttempt(value => value + 1)}>{t("Retry")}</button></MascotState>}
    {view !== "community" && loading && !data && <MascotState state="loading" role="status">{t("Loading news…")}</MascotState>}
    {view !== "community" && data && <>
      <section aria-label={ui(newsSectionLabels[view])}>
        {!data.items.length && <MascotState state="noMatches">{t("No qualifying recent reporting matches this view. Coverage may be incomplete.")}</MascotState>}
        <div className="mt-3 divide-y">{data.items.map(item => <TopStory key={item.story.id} item={item}/>)}</div>
        <div className="mt-6 flex flex-col items-center gap-2">
          {data.has_more&&<Button variant="outline" disabled={loading} onClick={loadMore}>{t(loading?"Loading more…":"Show more")}</Button>}
          <p className="text-xs text-muted-foreground">{t("Only reporting with source thumbnails is shown.")}</p>
          <p className="text-xs text-muted-foreground">{t("Reporting from the last 72 hours. Older items appear when you choose Show more.")}</p>
        </div>
      </section>
    </>}
  </div>;
}
