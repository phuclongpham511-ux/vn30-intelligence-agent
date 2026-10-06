"use client";
import { useCallback, useEffect, useState } from "react";
import { MascotState } from "../components/mascot/Mascot";
import { Button } from "../components/ui/button";
import SourceCoverage from "../components/news/SourceCoverage";
import TopStory from "../components/news/TopStory";
import type { TopStoryData } from "../components/news/TopStory";
import CommunityPulse from "../components/news/CommunityPulse";
import { emptyNewsFilters, newsQuery, readNewsFilters, newsViewQuery, readNewsView, newsSectionLabels } from "@/lib/news";
import type { NewsFilters, NewsSource, NewsView } from "@/lib/news";

type Story = TopStoryData;
type Data = { feed: Story[] };

export default function NewsPage() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
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
  const load = useCallback(async (signal?: AbortSignal) => {
    if (!ready || view === 'community') return;
    setLoading(true); setError(false);
    try {
      const query = newsQuery(filters);
      const category = {company:'COMPANY', industry:'INDUSTRY', briefing:'MARKET_BRIEF'}[view];
      const paths = [`feed?research_category=${category}&limit=30&${query}`];
      const results = await Promise.all(paths.map(async path => {
        const response = await fetch(`/api/news/${path}`, { signal, cache: "no-store" });
        if (!response.ok) throw new Error("News unavailable");
        return response.json();
      }));
      if (!signal?.aborted) setData({ feed: results[0] });
    } catch {
      if (!signal?.aborted) setError(true);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [filters, ready, view]);
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    void load(controller.signal);
    const timer = setInterval(() => void load(controller.signal), 15 * 60 * 1000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [load, attempt]);
  return <div className="page-stack">
    <div className="flex items-start justify-between gap-4"><div><div className="eyebrow mb-3">News</div><h1>Market Today</h1><p className="mt-2 text-sm text-muted-foreground">Company reporting, industry developments and market-wide attention.</p></div><Button variant="outline" disabled={loading && view !== "community"} onClick={() => setAttempt(value => value + 1)}>Refresh</Button></div>
    <SourceCoverage attempt={attempt}/>
    <div className="flex flex-wrap items-center justify-between gap-3">
      <nav aria-label="News sections" className="flex flex-wrap gap-2">{(Object.entries(newsSectionLabels) as [NewsView, string][]).map(([key, label]) => <button key={key} type="button" aria-pressed={view === key} onClick={() => setView(key)} className={`rounded border px-3 py-2 text-sm ${view === key ? "border-primary text-primary" : "text-muted-foreground hover:bg-muted"}`}>{label}</button>)}</nav>
    </div>
    {view !== "community" && <details className="rounded border p-3" key={newsQuery(filters) ? "filtered" : "unfiltered"} open={Boolean(newsQuery(filters))}>
    <summary className="cursor-pointer text-sm">Filter news{newsQuery(filters) ? " · filters active" : ""}</summary>
    <form aria-label="Filter news" onSubmit={event => { event.preventDefault(); setFilters({ ...draft }); }} className="flex flex-wrap items-end gap-3 pt-4">
      <label className="text-xs">Ticker<input value={draft.ticker} onChange={event => setDraft({ ...draft, ticker: event.target.value })} maxLength={20} placeholder="Any ticker" className="mt-1 block h-9 rounded border bg-background px-2 text-sm"/></label>

      <label className="text-xs">Country<select value={draft.country} onChange={event => setDraft({ ...draft, country: event.target.value })} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"><option value="">All countries</option>{[...new Set([...sources.map(source => source.country), ...(draft.country ? [draft.country] : [])])].sort().map(country => <option key={country} value={country}>{country}</option>)}</select></label>
      <label className="text-xs">Source<select value={draft.source} onChange={event => setDraft({ ...draft, source: event.target.value })} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"><option value="">All sources</option>{sources.map(source => <option key={source.source_id} value={source.source_id}>{source.name}{!source.enabled && " (disabled)"}</option>)}{draft.source && !sources.some(source => source.source_id === draft.source) && <option value={draft.source}>{draft.source}</option>}</select></label>
      <label className="text-xs">Topic<input value={draft.topic} onChange={event => setDraft({ ...draft, topic: event.target.value })} placeholder="Any topic" className="mt-1 block h-9 rounded border bg-background px-2 text-sm"/></label>
      <Button type="submit" variant="outline">Apply filters</Button>
      <button type="button" className="pb-2 text-xs text-primary underline" onClick={() => { setDraft(emptyNewsFilters); setFilters(emptyNewsFilters); }}>Clear all</button>
      <details className="w-full text-xs" open={Boolean(draft.sector)}><summary className="cursor-pointer text-muted-foreground">Advanced: headline sector tags (partial coverage)</summary><label className="mt-3 block">Sector<select value={draft.sector} onChange={event => setDraft({ ...draft, sector: event.target.value })} className="ml-3 h-9 rounded border bg-background px-2"><option value="">All sector tags</option>{[...new Set(["Financials", "Real Estate", "Technology", "Energy", "Consumer", "Industrials", ...(draft.sector ? [draft.sector] : [])])].map(sector => <option key={sector}>{sector}</option>)}</select></label><p className="mt-2 text-muted-foreground">Headline tags only. Company sector mapping is currently incomplete; use ticker or topic for broader coverage.</p></details>
    </form>
    </details>}
    {view !== "community" && newsQuery(filters) && <p className="text-xs text-muted-foreground">Publisher sections show this filtered view. These filters do not change story ranking or factual tags.</p>}
    {view === "community" && <CommunityPulse ticker="" topic="" attempt={attempt}/>}
    {view !== "community" && error && <MascotState state="dataUnavailable" role="alert">News is temporarily unavailable. {data && "Previously loaded headlines are shown below."} <button className="ml-2 text-primary underline" onClick={() => setAttempt(value => value + 1)}>Retry</button></MascotState>}
    {view !== "community" && loading && !data && <MascotState state="loading" role="status">Loading news…</MascotState>}
    {view !== "community" && data && <>
      <section aria-labelledby="research-feed"><h2 id="research-feed">{newsSectionLabels[view]}</h2>{view === 'briefing' && <p className="mt-1 text-xs text-muted-foreground">Broad market and policy reporting with at least two independent publishers.</p>}
        {!data.feed.length && <MascotState state="noMatches">No qualifying recent reporting matches this view. Coverage may be incomplete.</MascotState>}
        <div className="mt-3 grid gap-x-8 md:grid-cols-2">{data.feed.map(item => <TopStory key={item.story.id} item={item}/>)}</div>
      </section>
    </>}
  </div>;
}
