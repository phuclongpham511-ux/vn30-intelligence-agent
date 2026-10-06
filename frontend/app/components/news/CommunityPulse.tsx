"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { loadCommunity } from "@/lib/community";
import type { CommunityPulseData } from "@/lib/community";
import { CommunityDiscussions } from "../stock/StockCommunity";

export default function CommunityPulse({ ticker, topic, attempt }: { ticker: string; topic: string; attempt: number }) {
  const [data, setData] = useState<CommunityPulseData | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  const [draftTicker, setDraftTicker] = useState(ticker);
  const [selectedTicker, setSelectedTicker] = useState(ticker);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError(false);
    const load = () => loadCommunity(selectedTicker, "", controller.signal).then(rows => {
      if (!controller.signal.aborted) { setData(rows); setError(false); }
    }).catch(() => { if (!controller.signal.aborted) setError(true); });
    void load();
    const timer = setInterval(load, 15 * 60 * 1000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [selectedTicker, attempt, retry]);
  // News topics are publisher taxonomy, separate from Community extraction.
  void topic;
  return <section aria-labelledby="community-pulse">
    <h2 id="community-pulse">Community Daily Pulse</h2>
    <form className="mt-4 flex flex-wrap items-center gap-3" onSubmit={event => { event.preventDefault(); setSelectedTicker(draftTicker.trim().toUpperCase()); }}><label className="text-xs">Discussion ticker<input aria-label="Discussion ticker" value={draftTicker} onChange={event => setDraftTicker(event.target.value)} placeholder="Any ticker" maxLength={20} className="ml-3 h-9 rounded border bg-background px-2 text-sm"/></label><button className="text-sm text-primary" type="submit">Apply</button>{selectedTicker && <button type="button" className="text-xs text-primary" onClick={() => { setDraftTicker(""); setSelectedTicker(""); }}>Clear discussion filter</button>}</form>
    {data && !error && <div className="mt-4 flex flex-wrap gap-4 text-xs"><span className="text-muted-foreground">Active tickers · {data.window.label}, {new Date(data.window.start).toLocaleDateString("en-GB", { timeZone: "Asia/Ho_Chi_Minh" })}:</span>{data.active_tickers.slice(0,12).map(row => <span key={row.ticker}><button className="text-primary underline" onClick={() => { setDraftTicker(row.ticker); setSelectedTicker(row.ticker); }}>{row.ticker} ({row.item_count})</button> <Link aria-label={`Research ${row.ticker}`} href={`/stocks/${encodeURIComponent(row.ticker)}`} className="text-muted-foreground">Research ↗</Link></span>)}</div>}
    <div className="mt-5"><CommunityDiscussions key={selectedTicker} ticker={selectedTicker || "Market"} data={data} loading={!data && !error} error={error} retry={() => setRetry(value => value + 1)}/></div>
  </section>;
}
