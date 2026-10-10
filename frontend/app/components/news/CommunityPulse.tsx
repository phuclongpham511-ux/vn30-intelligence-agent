"use client";
import {useLocale} from "@/lib/i18n";
import { useEffect, useState } from "react";
import Link from "next/link";
import { loadCommunity } from "@/lib/community";
import type { CommunityPulseData } from "@/lib/community";
import { CommunityDiscussions } from "../stock/StockCommunity";

export default function CommunityPulse({ ticker, topic, attempt, compact=false }: { ticker: string; topic: string; attempt: number; compact?: boolean }) {
  const {t,ui,date:localDate}=useLocale();
  const [window,setWindow]=useState<"today"|"last24h">("today");
  const [data, setData] = useState<CommunityPulseData | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  const [draftTicker, setDraftTicker] = useState(ticker);
  const [selectedTicker, setSelectedTicker] = useState(ticker);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError(false);
    const load = () => loadCommunity(selectedTicker, "", controller.signal,window).then(rows => {
      if (!controller.signal.aborted) { setData(rows); setError(false); }
    }).catch(() => { if (!controller.signal.aborted) setError(true); });
    void load();
    const timer = setInterval(load, 15 * 60 * 1000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [selectedTicker, attempt, retry, window]);
  // News topics are publisher taxonomy, separate from Community extraction.
  void topic;
  return <section aria-label={t("Community Pulse")}>
    <div className="flex flex-wrap items-center justify-between gap-3"><label className="text-xs">{t("Discussion window")}<select aria-label={t("Discussion window")} value={window} onChange={e=>setWindow(e.target.value as "today"|"last24h")} className="ml-2 h-9 rounded border bg-background px-2"><option value="today">{t("Today")}</option><option value="last24h">{t("Last 24 hours")}</option></select></label></div>
    {!compact&&<form className="mt-4 flex flex-wrap items-center gap-3" onSubmit={event => { event.preventDefault(); setSelectedTicker(draftTicker.trim().toUpperCase()); }}><label className="text-xs">{t("Discussion ticker")}<input aria-label={t("Discussion ticker")} value={draftTicker} onChange={event => setDraftTicker(event.target.value)} placeholder={t("Any ticker")} maxLength={20} className="ml-3 h-9 rounded border bg-background px-2 text-sm"/></label><button className="text-sm text-primary" type="submit">{t("Apply")}</button>{selectedTicker && <button type="button" className="text-xs text-primary" onClick={() => { setDraftTicker(""); setSelectedTicker(""); }}>{t("Clear discussion filter")}</button>}</form>}
    {compact&&selectedTicker&&<button type="button" className="mt-3 text-xs text-primary underline" onClick={()=>{setDraftTicker('');setSelectedTicker('');}}>{t('Clear discussion filter')} · {selectedTicker}</button>}
    {data && !error && <div className="mt-4 flex flex-wrap gap-4 text-xs"><span className="text-muted-foreground">{t("Active tickers ·")} {ui(data.window.label)}, {localDate(data.window.start)}:</span>{data.active_tickers.slice(0,compact?6:12).map(row => <span key={row.ticker}><button className="text-primary underline" onClick={() => { setDraftTicker(row.ticker); setSelectedTicker(row.ticker); }}>{row.ticker} ({row.item_count})</button> <Link aria-label={t("Research {ticker}",{ticker:row.ticker})} href={`/stocks/${encodeURIComponent(row.ticker)}`} className="text-muted-foreground">{t("Research ↗")}</Link></span>)}</div>}
    <div className="mt-5"><CommunityDiscussions key={selectedTicker} ticker={selectedTicker || "Market"} showHeading={false} compact={compact} data={data} loading={!data && !error} error={error} retry={() => setRetry(value => value + 1)}/></div>
  </section>;
}
