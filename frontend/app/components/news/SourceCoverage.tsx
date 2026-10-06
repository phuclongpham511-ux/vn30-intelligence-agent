"use client";
import { useEffect, useState } from "react";
import type { NewsSource } from "@/lib/news";
import type { CommunitySource } from "@/lib/community";
import { collectionLabels, fetchTime, newsFreshness } from "@/lib/collectionStatus";

export default function SourceCoverage({ attempt = 0 }: { attempt?: number }) {
  const [sources, setSources] = useState<NewsSource[] | null>(null);
  const [community, setCommunity] = useState<CommunitySource[] | null>(null);
  const [communityError, setCommunityError] = useState(false);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      try {
        const response = await fetch("/api/news/sources", { signal: controller.signal, cache: "no-store" });
        if (!response.ok) throw new Error("Unavailable");
        const rows = await response.json();
        if (!controller.signal.aborted) { setSources(rows); setError(false); }
      } catch { if (!controller.signal.aborted) setError(true); }
    };
    const loadCommunity = async () => {
      try {
        const response = await fetch("/api/community/sources", { signal: controller.signal, cache: "no-store" });
        if (!response.ok) throw new Error("Unavailable");
        const rows = await response.json();
        if (!controller.signal.aborted) { setCommunity(rows); setCommunityError(false); }
      } catch { if (!controller.signal.aborted) setCommunityError(true); }
    };
    const refresh = () => { void load(); void loadCommunity(); };
    refresh();
    const timer = setInterval(refresh, 60 * 1000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [attempt, retry]);
  const summary = sources ? newsFreshness(sources) : null;
  return <details className="rounded border p-3 text-xs">
    <summary className="cursor-pointer leading-6"><span>News: {error ? "status unavailable" : summary ? `${summary.healthy}/${summary.enabled} enabled feeds healthy` : "checking sources…"}</span><span className="ml-3 text-muted-foreground">Last successful fetch: {fetchTime(error ? null : summary?.lastSuccess || null)}</span><span className="block text-muted-foreground">Community: {communityError ? "status unavailable" : community ? `${community.filter(source => source.enabled && source.status === "healthy").length}/${community.filter(source => source.enabled).length} active sources healthy` : "checking sources…"}</span></summary>
    {(error || communityError) && <p className="mt-2 text-muted-foreground">Some source status is unavailable. <button className="text-primary underline" onClick={() => setRetry(value => value + 1)}>Retry status</button></p>}
    <p className="mt-2 text-muted-foreground">Healthy means a successful fetch within two source polling intervals. Feed status does not guarantee complete news coverage. Missing headlines do not mean no event occurred.</p>
    <ul className="mt-3 space-y-2">{!error && sources?.map(source => <li key={source.source_id} className="flex flex-wrap justify-between gap-2 border-b pb-2 last:border-0">
      <span>{source.name} · {collectionLabels[source.status]} · every {source.poll_interval_minutes} min</span><span className="text-muted-foreground">Last successful fetch: {fetchTime(source.last_success_at)} · Last attempt: {fetchTime(source.last_attempt_at)}</span>
    </li>)}</ul>
    {!communityError && community?.map(source => <p key={source.source_id} className="mt-3 text-muted-foreground">{source.name} · {collectionLabels[source.status]} · every {source.poll_interval_minutes} min · Last attempt: {fetchTime(source.last_attempt_at)} · Items received in last successful acquisition: {source.items_received ?? "Unavailable"} · {source.reason || "Bounded public sample"}</p>)}
  </details>;
}
