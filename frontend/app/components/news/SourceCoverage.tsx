"use client";
import { useEffect, useState } from "react";
import type { NewsSource } from "@/lib/news";
import { formatDate } from "@/lib/presentation";

const labels = { healthy: "Updated", stale: "Update overdue", error: "Last attempt failed", not_attempted: "Not ingested yet", disabled: "Disabled" };
export default function SourceCoverage() {
  const [sources, setSources] = useState<NewsSource[] | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
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
    void load();
    const timer = setInterval(() => void load(), 15 * 60 * 1000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [attempt]);
  if (error) return <p className="text-xs text-muted-foreground">Source update status is unavailable. <button className="text-primary underline" onClick={() => setAttempt(value => value + 1)}>Retry status</button></p>;
  if (!sources) return <p className="text-xs text-muted-foreground">Checking source updates…</p>;
  const enabled = sources.filter(source => source.enabled);
  const healthy = enabled.filter(source => source.status === "healthy").length;
  return <details className="rounded border p-3 text-xs">
    <summary className="cursor-pointer">Source updates: {healthy}/{enabled.length} active feeds updated within two polling intervals</summary>
    <p className="mt-2 text-muted-foreground">Feed status does not guarantee complete news coverage. Missing headlines do not mean no event occurred.</p>
    <ul className="mt-3 space-y-2">{sources.map(source => <li key={source.source_id} className="flex flex-wrap justify-between gap-2 border-b pb-2 last:border-0">
      <span>{source.name} · {labels[source.status]}</span><span className="text-muted-foreground">Last successful fetch: {source.last_success_at ? new Date(source.last_success_at).toLocaleString("en-GB") : formatDate(null)}</span>
    </li>)}</ul>
  </details>;
}
