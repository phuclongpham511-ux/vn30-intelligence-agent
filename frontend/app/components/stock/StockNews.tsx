"use client";
import {useLocale} from "@/lib/i18n";
import Link from "next/link";
import { useEffect, useState } from "react";
import {newsViewQuery,emptyNewsFilters} from "@/lib/news";
import SourceCoverage from "../news/SourceCoverage";
import TopStory,{type TopStoryData} from "../news/TopStory";
import {safeExternalUrl} from "@/lib/presentation";

type Story = TopStoryData & { story: TopStoryData["story"] & { last_updated_at?: string | null } };

export default function StockNews({ ticker }: { ticker: string }) {
  const {t,date:localDate}=useLocale();
  const [items, setItems] = useState<Story[] | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [expanded, setExpanded] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setItems(null); setError(false); setExpanded(false);
    let busy=false;
    const load=()=>{if(busy)return;busy=true;
    fetch(`/api/news/feed?research_category=COMPANY&ticker=${encodeURIComponent(ticker)}&limit=10`, { signal: controller.signal, cache: "no-store" })
      .then(async response => {
        if (!response.ok) throw new Error("Unavailable");
        const rows = await response.json();
        if (!controller.signal.aborted) setItems(rows);setError(false);
      }).catch(() => { if (!controller.signal.aborted) setError(true); }).finally(()=>{busy=false;});};
    load();const timer=setInterval(load,60_000);
    return () => {controller.abort();clearInterval(timer);};
  }, [ticker, attempt]);
  const remaining=items?.slice(1)||[];
  const visible=expanded?remaining:remaining.slice(0,4);
  const allHref=`/news?${newsViewQuery({...emptyNewsFilters,ticker},"company")}`;
  return <section className="panel overflow-hidden" aria-label={t("Quick news Â· {ticker}",{ticker})}>
    <div className="flex items-center justify-between gap-3 border-b px-5 py-4">
      <div><h2>{t("Quick news Â· {ticker}",{ticker})}</h2><p className="mt-1 text-xs text-muted-foreground">{t("Company stories ranked by independent coverage and recency.")}</p></div>
      <Link href={allHref} className="shrink-0 text-xs text-primary hover:underline">{t("View all")}</Link>
    </div>
    <div className="px-5 py-4">
      <SourceCoverage/>
      {error ? <p role="alert" className="py-4 text-sm">{t("News is temporarily unavailable.")} <button className="text-primary underline" onClick={() => setAttempt(value => value + 1)}>{t("Retry")}</button></p>
        : items === null ? <p role="status" className="py-4 text-sm text-muted-foreground">{t("Loading quick newsâ€¦")}</p>
        : items.length ? <>
          <TopStory item={items[0]}/>
          {remaining.length>0&&<div className="divide-y border-t">
            {visible.map(item=>{
              const article=item.representative_article;
              const url=safeExternalUrl(article.url);
              const date=article.published_at||article.first_seen_at;
              return <article key={item.story.id} className="py-3">
                <h3 className="text-sm font-medium leading-5">{url?<a href={url} target="_blank" rel="noopener noreferrer" className="hover:text-primary">{article.title}</a>:article.title}</h3>
                <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground"><span>{article.source_name}</span><time dateTime={date}>{!article.published_at&&t("First seen")+" "}{localDate(date,true)}</time><span>{t(item.story.source_count===1?"{count} independent source":"{count} independent sources",{count:item.story.source_count})}</span></div>
              </article>;
            })}
          </div>}
          {remaining.length>4&&<button type="button" className="mt-3 text-xs text-primary hover:underline" aria-expanded={expanded} onClick={()=>setExpanded(value=>!value)}>{expanded?t("Show fewer headlines"):t("Show more headlines ({count})",{count:remaining.length-4})}</button>}
        </>
        : <p className="py-4 text-sm text-muted-foreground">{t("No recent ingested headlines matched {ticker}. News may be missing or untagged; this does not indicate no meaningful change.",{ticker})}</p>}
    </div>
  </section>;
}
