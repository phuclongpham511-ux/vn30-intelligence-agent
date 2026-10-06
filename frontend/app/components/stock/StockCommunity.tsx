"use client";
import { useEffect, useState } from "react";
import type { CommunityPulseData } from "@/lib/community";
import { communityEvidence, communitySourceMessage, loadCommunity } from "@/lib/community";
import { safeExternalUrl } from "@/lib/presentation";
import { collectionLabels, fetchTime } from "@/lib/collectionStatus";
import { unreviewedThreads } from "@/lib/watchlist";

export function CommunityDiscussions({ ticker, data, loading, error, retry, seen, review, storageError = false }:
  { ticker: string; data: CommunityPulseData | null; loading: boolean; error: boolean;
    retry: () => void; seen?: string[]; review?: () => void; storageError?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const fresh = data ? unreviewedThreads(data.threads, seen) : [];
  const sourceUrl = data ? safeExternalUrl(data.source.url) : null;
  return <section aria-label={`${ticker} community discussions`}>
    <div className="flex flex-wrap items-center justify-between gap-2">
      <h2 className="text-sm">Community discussions</h2>
      {review && !loading && !error && fresh.length > 0 && <button
        aria-label={`Mark ${ticker} Community reviewed`} disabled={storageError}
        className="text-xs text-primary underline disabled:opacity-50" onClick={review}>Mark {fresh.length} {fresh.length === 1 ? "discussion" : "discussions"} reviewed</button>}
    </div>
    <p className="mt-1 text-xs text-muted-foreground">Public discussion evidence · opinions and unverified claims.</p>
    {loading ? <p role="status" className="mt-3 text-sm text-muted-foreground">Loading Community discussions…</p>
      : error ? <p role="alert" className="mt-3 text-sm">Community discussions are temporarily unavailable. Counts are unknown. <button className="text-primary underline" onClick={retry}>Retry Community</button></p>
      : data && <>
        <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
          {sourceUrl ? <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="text-primary">{data.source.name} ↗</a> : <span>{data.source.name}</span>}
          <span>{collectionLabels[data.source.status]}</span>
          <span>Last successful fetch: {fetchTime(data.source.last_success_at)}</span>
        </div>
        <p role="status" className="mt-2 text-xs text-muted-foreground">{communitySourceMessage(data.source.status)}</p>
        {review && data.threads.length > 0 && <p className="mt-2 text-xs">{data.threads.length} observed {data.threads.length === 1 ? "discussion" : "discussions"} · {seen ? `${fresh.length} new since your Community review` : `${fresh.length} unreviewed · Not reviewed yet`}{data.source.status !== "healthy" && <span className="text-muted-foreground"> · current coverage unknown</span>}</p>}
        {!data.threads.length && <p className="mt-3 text-sm text-muted-foreground">{data.source.status === "healthy"
          ? `No discussions matched ${ticker} in the recent stored sample. This does not mean no discussion occurred.`
          : `No stored discussions matched ${ticker}. Current Community coverage is unavailable.`}</p>}
        <ul className="mt-3 divide-y">{data.threads.slice(0, expanded ? 20 : 3).map(thread => {
          const evidence = communityEvidence(thread);
          return <li key={thread.id} className="py-3 first:pt-0">
            <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
              <span>{data.source.name}</span>
              <span>{evidence.timeLabel} <time dateTime={evidence.time}>{fetchTime(evidence.time)}</time></span>
              {review && fresh.includes(thread.id) && <span className="text-primary">{seen ? "New" : "Unreviewed"}</span>}
            </div>
            <h3 className="mt-1 break-words text-sm leading-6">{evidence.url
              ? <a href={evidence.url} target="_blank" rel="noopener noreferrer" className="hover:text-primary">{thread.title} ↗</a>
              : thread.title}</h3>
            <p className="mt-1 text-xs text-muted-foreground">{evidence.replies} · {evidence.views} · Lifetime counts</p>
          </li>;
        })}</ul>
        {data.threads.length > 3 && <button className="text-xs text-primary underline" aria-expanded={expanded}
          onClick={() => setExpanded(value => !value)}>{expanded ? "Show fewer discussions" : `Show ${data.threads.length - 3} more ${data.threads.length === 4 ? "discussion" : "discussions"}`}</button>}
        {data.sampled_threads > data.threads.length && <p className="mt-2 text-xs text-muted-foreground">Showing up to 20 stored discussions from this sample.</p>}
      </>}
  </section>;
}

export default function StockCommunity({ ticker }: { ticker: string }) {
  const [data, setData] = useState<CommunityPulseData | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError(false);
    const load = () => loadCommunity(ticker, "", controller.signal)
      .then(result => { if (!controller.signal.aborted) { setData(result); setError(false); } })
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    void load();
    const timer = setInterval(load, 15 * 60 * 1000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [ticker, attempt]);
  return <div className="panel p-5"><CommunityDiscussions key={ticker} ticker={ticker} data={data} loading={!data && !error}
    error={error} retry={() => setAttempt(value => value + 1)}/></div>;
}
