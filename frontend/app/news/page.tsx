"use client";
import { useCallback, useEffect, useState } from "react";
import { MascotState } from "../components/mascot/Mascot";
import { Button } from "../components/ui/button";
import ArticleRow from "../components/news/ArticleRow";
import SourceCoverage from "../components/news/SourceCoverage";
import TopStory from "../components/news/TopStory";
import type { TopStoryData } from "../components/news/TopStory";
import CommunityPulse from "../components/news/CommunityPulse";
import { emptyNewsFilters, newsQuery, readNewsFilters, newsViewQuery, readNewsView } from "@/lib/news";
import type { NewsArticle as Article, NewsFilters, NewsSource, NewsView } from "@/lib/news";

type Story = TopStoryData;
type Topic = { topic: string; story_count: number; source_count: number; mention_velocity: number };
type Data = { top: Story[]; topics: Topic[]; latest: Article[]; global: Article[] };

export default function NewsPage() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState("");
  const [filters, setFilters] = useState<NewsFilters>(emptyNewsFilters);
  const [draft, setDraft] = useState<NewsFilters>(emptyNewsFilters);
  const [sources, setSources] = useState<NewsSource[]>([]);
  const [ready, setReady] = useState(false);
  const [view, setView] = useState<NewsView>("briefing");
  const [financialOnly, setFinancialOnly] = useState(true);
  const [attempt, setAttempt] = useState(0);
  const chooseTopic = (topic: string) => {
    setSelectedTopic(topic);
    setDraft(previous => ({ ...previous, topic }));
  };
  useEffect(() => {
    const sync = () => {
      const initial = readNewsFilters(window.location.search);
      const mode = readNewsView(window.location.search);
      setView(mode.view); setFinancialOnly(mode.financialOnly);
      setFilters(initial); setDraft(initial); setSelectedTopic(initial.topic); setReady(true);
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
      const query = newsViewQuery({ ...filters, topic: selectedTopic }, view, financialOnly);
      window.history.replaceState(null, "", `/news${query ? `?${query}` : ""}`);
    }
  }, [filters, selectedTopic, ready, view, financialOnly]);
  const load = useCallback(async (signal?: AbortSignal) => {
    if (!ready) return;
    setLoading(true); setError(false);
    try {
      const query = `${newsQuery({ ...filters, topic: selectedTopic })}&financial_only=${financialOnly}`;
      const paths = [`top?limit=6&${query}`, `topics/trending?limit=10&${query}`, `latest?limit=30&${query}`, `latest?category=GLOBAL&limit=12&${query}`];
      const results = await Promise.all(paths.map(async path => {
        const response = await fetch(`/api/news/${path}`, { signal, cache: "no-store" });
        if (!response.ok) throw new Error("News unavailable");
        return response.json();
      }));
      if (!signal?.aborted) setData({ top: results[0], topics: results[1], latest: results[2], global: results[3] });
    } catch {
      if (!signal?.aborted) setError(true);
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [selectedTopic, filters, ready, financialOnly]);
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    void load(controller.signal);
    const timer = setInterval(() => void load(controller.signal), 15 * 60 * 1000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [load, attempt]);
  return <div className="page-stack">
    <div className="flex items-start justify-between gap-4"><div><div className="eyebrow mb-3">News</div><h1>Market Today</h1><p className="mt-2 text-sm text-muted-foreground">Market-wide reporting from Vietnam and global markets.</p></div><Button variant="outline" disabled={loading && view !== "community"} onClick={() => setAttempt(value => value + 1)}>Refresh</Button></div>
    <SourceCoverage attempt={attempt}/>
    <div className="flex flex-wrap items-center justify-between gap-3">
      <nav aria-label="News sections" className="flex flex-wrap gap-2">{([["briefing", "Market briefing"], ["latest", "Latest News"], ["global", "Global Markets"], ["community", "Community Pulse"]] as const).map(([key, label]) => <button key={key} type="button" aria-pressed={view === key} onClick={() => setView(key)} className={`rounded border px-3 py-2 text-sm ${view === key ? "border-primary text-primary" : "text-muted-foreground hover:bg-muted"}`}>{label}</button>)}</nav>
      {view !== "community" && <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={financialOnly} onChange={event => setFinancialOnly(event.target.checked)}/>Financially tagged only</label>}
    </div>
    {view !== "community" && <p className="text-xs text-muted-foreground">{financialOnly ? "Shows headlines with detected financial topics, sectors or tickers. Tags can be incomplete; uncheck to see all ingested news." : "All ingested business headlines, including articles without financial tags."} Coverage and popularity are not investor materiality.</p>}
    {view !== "community" && <details className="rounded border p-3" key={newsQuery(filters) ? "filtered" : "unfiltered"} open={Boolean(newsQuery(filters))}>
    <summary className="cursor-pointer text-sm">Filter news{newsQuery({ ...filters, topic: selectedTopic }) ? " · filters active" : ""}</summary>
    <form aria-label="Filter news" onSubmit={event => { event.preventDefault(); setFilters({ ...draft }); setSelectedTopic(draft.topic); }} className="flex flex-wrap items-end gap-3 pt-4">
      <label className="text-xs">Ticker<input value={draft.ticker} onChange={event => setDraft({ ...draft, ticker: event.target.value })} maxLength={20} placeholder="Any ticker" className="mt-1 block h-9 rounded border bg-background px-2 text-sm"/></label>

      <label className="text-xs">Country<select value={draft.country} onChange={event => setDraft({ ...draft, country: event.target.value })} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"><option value="">All countries</option>{[...new Set([...sources.map(source => source.country), ...(draft.country ? [draft.country] : [])])].sort().map(country => <option key={country} value={country}>{country}</option>)}</select></label>
      <label className="text-xs">Source<select value={draft.source} onChange={event => setDraft({ ...draft, source: event.target.value })} className="mt-1 block h-9 rounded border bg-background px-2 text-sm"><option value="">All sources</option>{sources.map(source => <option key={source.source_id} value={source.source_id}>{source.name}{!source.enabled && " (disabled)"}</option>)}{draft.source && !sources.some(source => source.source_id === draft.source) && <option value={draft.source}>{draft.source}</option>}</select></label>
      <label className="text-xs">Topic<input value={draft.topic} onChange={event => setDraft({ ...draft, topic: event.target.value })} placeholder="Any topic" className="mt-1 block h-9 rounded border bg-background px-2 text-sm"/></label>
      <Button type="submit" variant="outline">Apply filters</Button>
      <button type="button" className="pb-2 text-xs text-primary underline" onClick={() => { setDraft(emptyNewsFilters); setFilters(emptyNewsFilters); setSelectedTopic(""); }}>Clear all</button>
      <details className="w-full text-xs" open={Boolean(draft.sector)}><summary className="cursor-pointer text-muted-foreground">Advanced: headline sector tags (partial coverage)</summary><label className="mt-3 block">Sector<select value={draft.sector} onChange={event => setDraft({ ...draft, sector: event.target.value })} className="ml-3 h-9 rounded border bg-background px-2"><option value="">All sector tags</option>{[...new Set(["Financials", "Real Estate", "Technology", "Energy", "Consumer", "Industrials", ...(draft.sector ? [draft.sector] : [])])].map(sector => <option key={sector}>{sector}</option>)}</select></label><p className="mt-2 text-muted-foreground">Headline tags only. Company sector mapping is currently incomplete; use ticker or topic for broader coverage.</p></details>
    </form>
    </details>}
    {view !== "community" && newsQuery({ ...filters, topic: selectedTopic }) && <p className="text-xs text-muted-foreground">Publisher sections show this filtered view. These filters do not change story ranking or factual tags.</p>}
    {view === "community" && <CommunityPulse ticker="" topic="" attempt={attempt}/>}
    {view !== "community" && error && <MascotState state="dataUnavailable" role="alert">News is temporarily unavailable. {data && "Previously loaded headlines are shown below."} <button className="ml-2 text-primary underline" onClick={() => setAttempt(value => value + 1)}>Retry</button></MascotState>}
    {view !== "community" && loading && !data && <MascotState state="loading" role="status">Loading news…</MascotState>}
    {view !== "community" && data && <>
      {view === "briefing" && <><section aria-labelledby="top-stories"><h2 id="top-stories">Top Stories</h2><p className="mt-1 text-xs text-muted-foreground">Ranked by independent sources, story activity and recency · recent 72-hour coverage.</p>
        {!data.top.length && <MascotState state="noMatches">No recent ingested stories match this view. Try clearing filters or checking source updates.</MascotState>}
        <div className="mt-3 grid gap-x-8 md:grid-cols-2">{data.top.map(item => <TopStory key={item.story.id} item={item}/>)}</div>
      </section>
      <section aria-labelledby="trending"><h2 id="trending">Trending Topics</h2><p className="mt-1 text-xs text-muted-foreground">Increasing coverage over the last six hours compared with the preceding six hours.</p><div className="mt-4 flex flex-wrap gap-2">{data.topics.map(topic => <button key={topic.topic} aria-pressed={selectedTopic === topic.topic} onClick={() => chooseTopic(selectedTopic === topic.topic ? "" : topic.topic)} className={`rounded border px-3 py-2 text-left text-sm focus-visible:outline ${selectedTopic === topic.topic ? "border-primary text-primary" : "hover:bg-muted"}`}><span className="font-medium">{topic.topic}</span><span className="mt-1 block text-xs text-muted-foreground">{topic.story_count} stories · {topic.source_count} sources</span></button>)}</div>{!data.topics.length && <p className="py-4 text-sm text-muted-foreground">No topics with increasing coverage yet.</p>}</section>
      </>}
      <div>
        {view === "latest" && <section aria-labelledby="latest"><div className="flex items-center justify-between"><h2 id="latest">Latest News</h2>{selectedTopic && <button className="text-xs text-primary" onClick={() => chooseTopic("")}>Clear {selectedTopic} filter</button>}</div>{data.latest.map(article => <ArticleRow key={article.id} article={article}/>)}{!data.latest.length && <MascotState state="noMatches">No recent ingested news matches this view. Clear filters or check source updates; missing headlines do not mean no event occurred.</MascotState>}</section>}
        {view === "global" && <section aria-labelledby="global"><h2 id="global">Global Markets</h2><p className="mt-1 text-xs text-muted-foreground">Rates, currencies, commodities, trade and global business.</p>{data.global.map(article => <ArticleRow key={article.id} article={article}/>)}{!data.global.length && <MascotState state="noMatches">No recent global headlines match this view. Clear filters or check source updates.</MascotState>}</section>}
      </div>
    </>}
  </div>;
}
