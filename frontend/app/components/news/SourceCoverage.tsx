"use client";
import {useLocale} from "@/lib/i18n";
import { useEffect, useState } from "react";
import type { NewsSource } from "@/lib/news";
import type { CommunitySource } from "@/lib/community";
import { collectionLabels, newsFreshness } from "@/lib/collectionStatus";

export default function SourceCoverage({ attempt = 0 }: { attempt?: number }) {
  const {t,ui,date:localDate}=useLocale();
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
    <summary className="cursor-pointer leading-6"><span>{t("News")}: {error?t("status unavailable"):summary?t("{healthy}/{total} enabled feeds healthy",{healthy:summary.healthy,total:summary.enabled}):t("checking sources…")}</span><span className="ml-3 text-muted-foreground">{t("Last successful fetch")}: {localDate(error?null:summary?.lastSuccess,true)}</span><span className="block text-muted-foreground">{t("Community")}: {communityError?t("status unavailable"):community?t("{healthy}/{total} active sources healthy",{healthy:community.filter(source=>source.enabled&&source.status==="healthy").length,total:community.filter(source=>source.enabled).length}):t("checking sources…")}</span></summary>
    {(error || communityError) && <p className="mt-2 text-muted-foreground">{t("Some source status is unavailable.")} <button className="text-primary underline" onClick={() => setRetry(value => value + 1)}>{t("Retry status")}</button></p>}
    <p className="mt-2 text-muted-foreground">{t("Healthy means a successful fetch within two source polling intervals. Feed status does not guarantee complete news coverage. Missing headlines do not mean no event occurred.")}</p>
    <ul className="mt-3 space-y-2">{!error && sources?.map(source => <li key={source.source_id} className="flex flex-wrap justify-between gap-2 border-b pb-2 last:border-0">
      <span>{source.name} · {ui(collectionLabels[source.status])} · {t("every {count} min",{count:source.poll_interval_minutes})}</span><span className="text-muted-foreground">{t("Last successful fetch")}: {localDate(source.last_success_at,true)} · {t("Last attempt")}: {localDate(source.last_attempt_at,true)}</span>
    </li>)}</ul>
    {!communityError && community?.map(source => <p key={source.source_id} className="mt-3 text-muted-foreground">{source.name} · {ui(collectionLabels[source.status])} · {t("every {count} min",{count:source.poll_interval_minutes})} · {t("Last attempt")}: {localDate(source.last_attempt_at,true)} · {t("Items received in last successful acquisition")}: {source.items_received ?? t("Unavailable")} · {source.reason || t("Bounded public sample")}</p>)}
  </details>;
}
