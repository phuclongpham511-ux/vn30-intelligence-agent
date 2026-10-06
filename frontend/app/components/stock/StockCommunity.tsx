"use client";
import { useEffect, useState } from "react";
import type { CommunityPulseData } from "@/lib/community";
import { communityEvidence, communitySourceMessage, loadCommunity, communityTime as fetchTime } from "@/lib/community";
import { collectionLabels } from "@/lib/collectionStatus";
import { unreviewedThreads } from "@/lib/watchlist";

export function CommunityDiscussions({ ticker, data, loading, error, retry, seen, review, storageError = false }:
  { ticker: string; data: CommunityPulseData | null; loading: boolean; error: boolean;
    retry: () => void; seen?: string[]; review?: () => void; storageError?: boolean }) {
  const fresh = data ? unreviewedThreads(data.items, seen) : [];
  const sourceName = (id: string) => data?.sources.find(source => source.source_id === id)?.name || id;
  const renderEvidence = (ids: string[]) => <ul className="mt-2 space-y-4">{ids.map(id => {
              const row = data?.items.find(item => item.id === id);
              if (!row) return null;
              const evidence = communityEvidence(row);
              return <li key={id} className="break-words"><p className="text-muted-foreground">{sourceName(row.source_id)} · {row.tickers.join(", ")} · {evidence.timeLabel} <time dateTime={evidence.time}>{fetchTime(evidence.time)}</time>{review && fresh.includes(id) ? " · Unreviewed" : ""}{row.is_fixture ? " · Fixture" : ""}</p>
                {row.title && <p className="mt-1 font-medium">{row.title}</p>}<p className="mt-1 leading-5">{row.excerpt}</p>
                <p className="mt-1 text-muted-foreground">{evidence.replies} · {evidence.views}</p>
                {evidence.url && <a href={evidence.url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-block text-primary">Original discussion ↗</a>}
              </li>;
            })}</ul>;
  return <section aria-label={`${ticker} community discussions`}>
    <div className="flex flex-wrap items-center justify-between gap-2">
      <h2 className="text-sm">Community {data?.window.label || "Today"}</h2>
      {review && !loading && !error && fresh.length > 0 && <button
        aria-label={`Mark ${ticker} Community reviewed`} disabled={storageError}
        className="text-xs text-primary underline disabled:opacity-50" onClick={review}>Mark {fresh.length} {fresh.length === 1 ? "discussion" : "discussions"} reviewed</button>}
    </div>
    <p className="mt-1 text-xs text-muted-foreground">What investors are discussing · opinions and unverified claims · Vietnam time.</p>
    {loading ? <p role="status" className="mt-3 text-sm text-muted-foreground">Loading Community discussions…</p>
      : error ? <p role="alert" className="mt-3 text-sm">Community discussions are temporarily unavailable. Counts are unknown. <button className="text-primary underline" onClick={retry}>Retry Community</button></p>
      : data && <>
        <p className="mt-3 text-xs text-muted-foreground">{data.unique_items} unique {data.unique_items === 1 ? "discussion" : "discussions"} in this bounded sample · {data.window.label} · {new Date(data.window.start).toLocaleDateString("en-GB", { timeZone: "Asia/Ho_Chi_Minh" })}</p>
        {review && data.items.length > 0 && <p className="mt-2 text-xs">{seen ? `${fresh.length} new since your Community review` : `${fresh.length} unreviewed · Not reviewed yet`}</p>}
        <details className="mt-3 text-xs text-muted-foreground"><summary className="cursor-pointer">Source coverage · {data.sources.filter(source => source.enabled && source.status === "healthy").length}/{data.sources.filter(source => source.enabled).length} active sources healthy{data.coverage_partial ? " · partial coverage" : " · bounded sample"}</summary>
          <ul className="mt-2 space-y-2">{data.sources.map(source => <li key={source.source_id}>{source.name} · {collectionLabels[source.status]} · every {source.poll_interval_minutes} min<br/>Last attempt: {fetchTime(source.last_attempt_at)} · Last successful fetch: {fetchTime(source.last_success_at)} · Items: {source.items_received ?? "Unavailable"}<br/>{source.reason || communitySourceMessage(source.status)}</li>)}</ul>
        </details>
        {!data.items.length && <p className="mt-4 text-sm text-muted-foreground">No same-day discussions matched {ticker === "Market" ? "this view" : ticker}. Coverage is incomplete; this does not mean no discussion occurred.</p>}
        <div className="mt-4 divide-y">{data.themes.map(theme => <article key={theme.id} className="py-4 first:pt-0">
          <h3 className="text-sm font-medium">{theme.label}</h3>
          {theme.keywords.length > 0 && <p className="mt-1 text-xs text-muted-foreground">Discussion terms: {theme.keywords.join(" · ")}</p>}
          <p className="mt-2 text-xs text-muted-foreground">Representative discussion excerpt</p>
          <blockquote className="mt-1 break-words border-l-2 pl-3 text-sm leading-6">{theme.summary}</blockquote>
          <p className="mt-2 text-xs text-muted-foreground">{theme.item_count} unique {theme.item_count === 1 ? "discussion" : "discussions"} · {theme.source_count} {theme.source_count === 1 ? "source" : "sources"}: {theme.source_ids.map(sourceName).join(", ")} · Latest <time dateTime={theme.latest_at}>{fetchTime(theme.latest_at)}</time></p>
          <details className="mt-3 text-xs"><summary className="cursor-pointer text-primary">View discussions ({theme.evidence_ids.length} original {theme.evidence_ids.length === 1 ? "item" : "items"})</summary>
            {renderEvidence(theme.evidence_ids)}
          </details>
        </article>)}</div>
        {data.items.length > 0 && <details className="mt-3 text-xs"><summary className="cursor-pointer text-primary">All same-day evidence ({data.items.length} original {data.items.length === 1 ? "item" : "items"})</summary>{renderEvidence(data.items.map(row => row.id))}</details>}
        {data.truncated && <p className="mt-2 text-xs text-muted-foreground">Analysis is limited to the latest 300 same-day items; sample coverage is incomplete.</p>}
        {data.items.length > 0 && <p className="mt-3 text-xs text-muted-foreground">Themes can overlap. Reposts count once; source breadth describes discussion, not corroboration.</p>}
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
