"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { loadCommunity } from "@/lib/community";
import type { CommunityPulseData } from "@/lib/community";
import { safeExternalUrl } from "@/lib/presentation";
import { collectionLabels, fetchTime } from "@/lib/collectionStatus";
import { MascotState } from "../mascot/Mascot";

export default function CommunityPulse({ ticker, topic, attempt }: { ticker: string; topic: string; attempt: number }) {
  const [data, setData] = useState<CommunityPulseData | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  const [draftTicker, setDraftTicker] = useState(ticker);
  const [selectedTicker, setSelectedTicker] = useState(ticker);
  const [expanded, setExpanded] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError(false); setExpanded(false);
    const load = () => loadCommunity(selectedTicker, topic, controller.signal).then(rows => { if (!controller.signal.aborted) { setData(rows); setError(false); } }).catch(() => { if (!controller.signal.aborted) setError(true); });
    void load();
    const timer = setInterval(load, 15 * 60 * 1000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [selectedTicker, topic, attempt, retry]);
  return <section aria-labelledby="community-pulse">
    <h2 id="community-pulse">Community Pulse</h2><p className="mt-2 text-sm text-muted-foreground">Public investor discussion · opinions and unverified claims, separate from publisher reporting.</p>
    <form className="mt-4 flex flex-wrap items-center gap-3" onSubmit={event => { event.preventDefault(); setSelectedTicker(draftTicker); }}><label className="text-xs">Discussion ticker<input aria-label="Discussion ticker" value={draftTicker} onChange={event => setDraftTicker(event.target.value)} placeholder="Any ticker" maxLength={20} className="ml-3 h-9 rounded border bg-background px-2 text-sm"/></label><button className="text-sm text-primary" type="submit">Apply</button>{selectedTicker && <button type="button" className="text-xs text-primary" onClick={() => { setDraftTicker(""); setSelectedTicker(""); }}>Clear discussion filter</button>}</form>
    {error && <MascotState state="dataUnavailable" role="alert">Community discussion is temporarily unavailable. Activity counts are unknown. <button onClick={() => setRetry(value => value + 1)} className="text-primary underline">Retry</button></MascotState>}
    {!data && !error && <MascotState state="loading">Loading public discussions…</MascotState>}
    {data && <>
      <div className="mt-4 text-xs text-muted-foreground"><a href={safeExternalUrl(data.source.url) || undefined} target="_blank" rel="noopener noreferrer" className="text-primary">{data.source.name} ↗</a> · {collectionLabels[data.source.status]} · {data.sampled_threads} observed threads · Last successful fetch: {fetchTime(data.source.last_success_at)}</div>
      {data.source.status !== "healthy" && <p role="status" className="mt-2 text-sm text-muted-foreground">{data.source.status === "not_attempted" ? "This source has not been checked yet." : data.source.status === "error" ? "The latest source check failed. Previously observed threads may be shown; activity is incomplete." : "The source has not been checked recently. Displayed activity may be stale."}</p>}
      <p className="mt-2 text-xs text-muted-foreground">A bounded sample from the public listing, observed in the last 72 hours. Counts reflect this sample, not the whole community. Replies and views are lifetime totals; ranking uses replies, then last public activity.</p>
      <div className="mt-5 flex flex-wrap gap-x-6 gap-y-3">{data.most_discussed.slice(0, 8).map(row => <div key={row.ticker} className="text-sm"><Link href={`/stocks/${encodeURIComponent(row.ticker)}`} className="font-medium text-primary">{row.ticker}</Link><span className="ml-2 text-xs text-muted-foreground">{row.thread_count} {row.thread_count === 1 ? "thread" : "threads"}</span></div>)}</div>
      {!data.most_discussed.length && data.threads.length > 0 && <p className="mt-3 text-xs text-muted-foreground">No tickers were confidently matched in this sample. Matching requires an available company name or an explicit ticker marker; bare uppercase words are excluded.</p>}
      {data.topics.length > 0 && <p className="mt-3 text-xs text-muted-foreground">Discussion topics: {data.topics.slice(0, 5).map(row => `${row.topic} (${row.thread_count})`).join(" · ")}</p>}
      {!data.threads.length && <MascotState state="noMatches">No public discussion threads are available for this view. Missing coverage does not mean no discussion occurred.</MascotState>}
      <div className="mt-4 divide-y">{data.threads.slice(0, expanded ? 20 : 6).map(thread => <article key={thread.id} className="py-4"><h3 className="text-sm font-medium leading-6"><a href={safeExternalUrl(thread.url) || undefined} target="_blank" rel="noopener noreferrer" className="hover:text-primary">{thread.title} ↗</a></h3><div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground"><span>{thread.author || "Public discussion"}</span><span>{thread.replies === null ? "Replies unavailable" : `${thread.replies.toLocaleString("en-GB")} replies`}</span><span>{thread.views === null ? "Views unavailable" : `${thread.views.toLocaleString("en-GB")} views`}</span><span>{thread.activity_at ? "Last activity " : "Observed "}<time dateTime={thread.activity_at || thread.last_seen_at}>{new Date(thread.activity_at || thread.last_seen_at).toLocaleString("en-GB", {dateStyle:"medium", timeStyle:"short"})}</time></span>{thread.tickers.map(ticker => <span key={ticker} className="text-primary">{ticker}</span>)}</div></article>)}</div>
      {data.threads.length > 6 && <button className="mt-3 text-xs text-primary" aria-expanded={expanded} onClick={() => setExpanded(value => !value)}>{expanded ? "Show fewer discussions" : `Show ${data.threads.length - 6} more discussions`}</button>}
    </>}
  </section>;
}
