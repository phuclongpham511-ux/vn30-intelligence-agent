"use client";
import {useLocale} from "@/lib/i18n";
import Link from "next/link";
import { useEffect, useState } from "react";
import {newsViewQuery,emptyNewsFilters} from "@/lib/news";
import SourceCoverage from "../news/SourceCoverage";
import TopStory,{type TopStoryData} from "../news/TopStory";
import {LivePrices} from "./LivePrice";
import {newsSymbols} from "@/lib/newsPresentation";
import {cacheRefresh} from "@/lib/cacheRefresh";

type Story = TopStoryData & { story: TopStoryData["story"] & { last_updated_at?: string | null } };

export default function StockNews({ ticker, preview=false }: { ticker: string; preview?:boolean }) {
  const {t}=useLocale();
  const [items, setItems] = useState<Story[] | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [expanded, setExpanded] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setItems(null); setError(false); setExpanded(false);
    let busy=false;
    const load=()=>{if(busy)return;busy=true;
    fetch(`/api/news/feed?research_category=COMPANY&ranking=attention&ticker=${encodeURIComponent(ticker)}&limit=10`, { signal: controller.signal, cache: "no-store" })
      .then(async response => {
        if (!response.ok) throw new Error("Unavailable");
        const rows = await response.json();
        if (!controller.signal.aborted) {setItems(rows);setError(false);}
      }).catch(() => { if (!controller.signal.aborted) setError(true); }).finally(()=>{busy=false;});};
    load();const stop=cacheRefresh(load);
    return () => {controller.abort();stop();};
  }, [ticker, attempt]);
  const remaining=items?.slice(1)||[];
  const visible=preview?remaining.slice(0,2):expanded?remaining:remaining.slice(0,4);
  const allHref=`/news?${newsViewQuery({...emptyNewsFilters,ticker},"company")}`;
  return <section className="panel overflow-hidden" aria-label={t("Quick news · {ticker}",{ticker})}>
    <div className="flex items-center justify-between gap-3 border-b px-5 py-4">
      <div><h2>{t("Quick news · {ticker}",{ticker})}</h2></div>
      <Link href={allHref} className="shrink-0 text-xs text-primary hover:underline">{t("View all")}</Link>
    </div>
    <div className="px-5 py-4">
      <SourceCoverage/>
      {error ? <p role="alert" className="py-4 text-sm">{t("News is temporarily unavailable.")} <button className="text-primary underline" onClick={() => setAttempt(value => value + 1)}>{t("Retry")}</button></p>
        : items === null ? <p role="status" className="py-4 text-sm text-muted-foreground">{t("Loading quick news…")}</p>
        : items.length ? <>
          <LivePrices symbols={newsSymbols([items[0],...visible])} interval={30000}>
            <TopStory item={items[0]}/>
            {visible.map(item=><TopStory key={item.story.id} item={item} compact/>)}
          </LivePrices>
          {!preview&&remaining.length>4&&<button type="button" className="mt-3 text-xs text-primary hover:underline" aria-expanded={expanded} onClick={()=>setExpanded(value=>!value)}>{expanded?t("Show fewer headlines"):t("Show more headlines ({count})",{count:remaining.length-4})}</button>}
        </>
        : <p className="py-4 text-sm text-muted-foreground">{t("No recent ingested headlines matched {ticker}. News may be missing or untagged; this does not indicate no meaningful change.",{ticker})}</p>}
    </div>
  </section>;
}
