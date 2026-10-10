"use client";
import {useLocale} from "@/lib/i18n";
import { useEffect, useState } from "react";
import type { CommunityPulseData } from "@/lib/community";
import { communityEvidence, communitySourceMessage, loadCommunity } from "@/lib/community";
import { collectionLabels } from "@/lib/collectionStatus";
import { unreviewedThreads } from "@/lib/watchlist";

export function CommunityDiscussions({ ticker, data, loading, error, retry, seen, review, storageError = false, showHeading = true, compact=false }:
  { ticker: string; data: CommunityPulseData | null; loading: boolean; error: boolean;
    retry: () => void; seen?: string[]; review?: () => void; storageError?: boolean; showHeading?: boolean; compact?: boolean }) {
  const {t,ui,date:localDate,number:localNumber}=useLocale();
  const fresh = data ? unreviewedThreads(data.items, seen) : [];
  const sourceName = (id: string) => data?.sources.find(source => source.source_id === id)?.name || id;
  const originalDiscussion = (theme: CommunityPulseData['themes'][number]) => {
    const row=data?.items.find(item=>item.id===theme.representative_id)||data?.items.find(item=>theme.evidence_ids.includes(item.id));
    return row?communityEvidence(row).url:null;
  };
  const renderEvidence = (ids: string[]) => <ul className="mt-2 space-y-4">{ids.map(id => {
              const row = data?.items.find(item => item.id === id);
              if (!row) return null;
              const evidence = communityEvidence(row);
              return <li key={id} className="break-words"><p className="text-muted-foreground">{sourceName(row.source_id)} · {row.tickers.join(", ")} · {ui(evidence.timeLabel)} <time dateTime={evidence.time}>{localDate(evidence.time,true)}</time>{review && fresh.includes(id) ? " · "+t("Unreviewed") : ""}{row.is_fixture ? " · "+t("Fixture") : ""}</p>
                {row.title && <p className="mt-1 font-medium">{row.title}</p>}<p className="mt-1 leading-5">{row.excerpt}</p>
                <p className="mt-1 text-muted-foreground">{row.replies==null?t("Replies unavailable"):t("{count} replies",{count:localNumber(row.replies,0)})} · {row.views==null?t("Views unavailable"):t("{count} views",{count:localNumber(row.views,0)})}</p>
                {evidence.url && <a href={evidence.url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-block text-primary">{t("Original discussion ↗")}</a>}
              </li>;
            })}</ul>;
  return <section aria-label={t("{ticker} community discussions",{ticker:ticker==="Market"?t("Market"):ticker})}>
    <div className="flex flex-wrap items-center justify-between gap-2">
      {showHeading&&<h2 className="text-sm">{t("Community")} {ui(data?.window.label || "Today")}</h2>}
      {review && !loading && !error && fresh.length > 0 && <button
        aria-label={t("Mark {ticker} Community reviewed",{ticker})} disabled={storageError}
        className="text-xs text-primary underline disabled:opacity-50" onClick={review}>{t(fresh.length===1?"Mark {count} discussion reviewed":"Mark {count} discussions reviewed",{count:fresh.length})}</button>}
    </div>
    <p className="mt-1 text-xs text-muted-foreground">{t("Investor discussion · unverified · Vietnam time")}</p>
    {loading ? <p role="status" className="mt-3 text-sm text-muted-foreground">{t("Loading Community discussions…")}</p>
      : error ? <p role="alert" className="mt-3 text-sm">{t("Community discussions are temporarily unavailable. Counts are unknown.")} <button className="text-primary underline" onClick={retry}>{t("Retry Community")}</button></p>
      : data && <>
        <p className="mt-3 text-xs text-muted-foreground">{t(data.unique_items===1?"{count} unique discussion in this bounded sample":"{count} unique discussions in this bounded sample",{count:data.unique_items})} · {ui(data.window.label)} · {localDate(data.window.start)}</p>
        {compact&&<><p className="mt-1 text-xs text-muted-foreground">{t('Discussion activity, not sentiment.')}</p><p className="mt-1 text-xs text-muted-foreground">{t('Sample evaluated')} · {localDate(data.as_of,true)} · {t('Vietnam time')}</p>{data.sources.some(source=>source.enabled&&source.status!=='healthy')&&<p role="status" className="mt-2 text-xs text-amber-700 dark:text-amber-300">{t('Sources need a fresh worker check; coverage is incomplete.')}</p>}</>}
        {review && data.items.length > 0 && <p className="mt-2 text-xs">{seen ? t("{count} new since your Community review",{count:fresh.length}) : t("{count} unreviewed · Not reviewed yet",{count:fresh.length})}</p>}
        <details className="mt-3 text-xs text-muted-foreground"><summary className="cursor-pointer">{t("Source coverage")} · {t("{healthy}/{total} active sources healthy",{healthy:data.sources.filter(source=>source.enabled&&source.status==="healthy").length,total:data.sources.filter(source=>source.enabled).length})}{data.coverage_partial ? " · "+t("partial coverage") : " · "+t("bounded sample")}</summary>
          <ul className="mt-2 space-y-2">{data.sources.map(source => <li key={source.source_id}>{source.name} · {ui(collectionLabels[source.status])} · {t("every {count} min",{count:source.poll_interval_minutes})}<br/>{t("Last attempt")}: {localDate(source.last_attempt_at,true)} · {t("Last successful fetch")}: {localDate(source.last_success_at,true)} · {t("Items")}: {source.items_received ?? t("Unavailable")}<br/>{source.reason || ui(communitySourceMessage(source.status))}</li>)}</ul>
        </details>
        {!data.items.length && <p className="mt-4 text-sm text-muted-foreground">{t("No {window} discussions matched {ticker}.",{window:ui(data.window.kind==="last24h"?"last-24-hour":"same-day"),ticker:ticker==="Market"?t("this view"):ticker})} {ui(data.coverage_partial ? "Sources need a fresh worker check; coverage is incomplete." : "No matching published items were acquired for this window.")} {t("This does not mean no discussion occurred.")}</p>}
        <div className="mt-4 divide-y">{data.themes.slice(0,compact?3:undefined).map(theme => <article key={theme.id} className="py-4 first:pt-0">
          <h3 className="text-sm font-medium">{theme.label === 'Discussion phrasing' || theme.label === 'Recurring discussion phrase' ? (data.items.find(row => theme.evidence_ids.includes(row.id))?.title || theme.summary).slice(0, 100) : theme.label}</h3>
          <p className="mt-1 line-clamp-2 break-words text-sm leading-6">{theme.summary}</p>
          <p className="mt-2 text-xs text-muted-foreground">{t(theme.item_count===1?"{count} discussion":"{count} discussions",{count:theme.item_count})} · {t(theme.source_count===1?"{count} source":"{count} sources",{count:theme.source_count})} · {t("Latest")} <time dateTime={theme.latest_at}>{localDate(theme.latest_at,true)}</time></p>
          {compact&&<p className="mt-2 text-xs text-muted-foreground">{theme.source_ids.map(sourceName).join(' · ')}{originalDiscussion(theme)&&<a href={originalDiscussion(theme)!} target="_blank" rel="noopener noreferrer" className="ml-3 text-primary hover:underline">{t('Original discussion ↗')}</a>}</p>}
          <details className="mt-3 text-xs"><summary className="cursor-pointer text-primary">{t("View discussions")+" ("+t(theme.evidence_ids.length===1?"{count} original item":"{count} original items",{count:theme.evidence_ids.length})+")"}</summary>
            {theme.keywords.length > 0 && <p className="mt-3 text-muted-foreground">{t("Discussion terms:")} {theme.keywords.join(" · ")}</p>}
            <p className="mt-2 text-muted-foreground">{t("Sources:")} {theme.source_ids.map(sourceName).join(', ')}</p>
            {renderEvidence(theme.evidence_ids)}
          </details>
        </article>)}</div>
        {!compact&&data.items.length > 0 && <details className="mt-3 text-xs"><summary className="cursor-pointer text-primary">{t("All evidence")} · {ui(data.window.label)} ({t(data.items.length===1?"{count} original item":"{count} original items",{count:data.items.length})})</summary>{renderEvidence(data.items.map(row => row.id))}</details>}
        {data.truncated && <p className="mt-2 text-xs text-muted-foreground">{t("Analysis is limited to the latest 300 items in this window; sample coverage is incomplete.")}</p>}
        {data.items.length > 0 && <p className="mt-3 text-xs text-muted-foreground">{t("Themes can overlap. Reposts count once; source breadth describes discussion, not corroboration.")}</p>}
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
