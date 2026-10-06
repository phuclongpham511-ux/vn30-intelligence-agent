"use client";
import {useLocale} from "@/lib/i18n";
import Link from "next/link";
import { useEffect, useState } from "react";
import {newsViewQuery,emptyNewsFilters,type NewsArticle} from "@/lib/news";
import ArticleRow from "../news/ArticleRow";
import SourceCoverage from "../news/SourceCoverage";

export default function StockNews({ ticker }: { ticker: string }) {
  const {t}=useLocale();
  const [items, setItems] = useState<NewsArticle[] | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setItems(null); setError(false);
    fetch(`/api/news/latest?ticker=${encodeURIComponent(ticker)}&limit=6`, { signal: controller.signal, cache: "no-store" })
      .then(async response => {
        if (!response.ok) throw new Error("Unavailable");
        const rows = await response.json();
        if (!controller.signal.aborted) setItems(rows);
      }).catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, [ticker, attempt]);
  return <section className="panel overflow-hidden" aria-label={t("{ticker} news",{ticker})}>
    <div className="flex items-center justify-between gap-3 border-b px-5 py-4">
      <div><h2>{t("News mentioning {ticker}",{ticker})}</h2><p className="mt-1 text-xs text-muted-foreground">{t("Recent ingested headlines matched by ticker or company name.")}</p></div>
      <Link href={`/news?${newsViewQuery({...emptyNewsFilters,ticker},"company")}`} className="text-xs text-primary hover:underline">{t("View all")}</Link>
    </div>
    <div className="px-5 py-4">
      <SourceCoverage/>
      {error ? <p role="alert" className="py-4 text-sm">{t("News is temporarily unavailable.")} <button className="text-primary underline" onClick={() => setAttempt(value => value + 1)}>{t("Retry")}</button></p>
        : items === null ? <p role="status" className="py-4 text-sm text-muted-foreground">{t("Loading headlines…")}</p>
        : items.length ? items.map(item => <ArticleRow key={item.id} article={item}/>)
        : <p className="py-4 text-sm text-muted-foreground">{t("No recent ingested headlines matched {ticker}. News may be missing or untagged; this does not indicate no meaningful change.",{ticker})}</p>}
    </div>
  </section>;
}
