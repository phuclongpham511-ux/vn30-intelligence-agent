"use client";
import {useLocale} from "@/lib/i18n";
import { useState } from "react";
import Link from "next/link";
import type { NewsArticle } from "@/lib/news";
import {storyImages} from "@/lib/storyImages";
import { safeExternalUrl } from "@/lib/presentation";

export type TopStoryData = { story: { id: string; representative_title: string; source_count: number }; representative_article: NewsArticle; articles: NewsArticle[]; thumbnail_url?:string|null; thumbnail_article_id?:string|null; research_category?: "COMPANY" | "INDUSTRY" | "MARKET_BRIEF" | null };

export default function TopStory({ item,requireImage=false,onImageUnavailable }: { item: TopStoryData; requireImage?:boolean; onImageUnavailable?:()=>void }) {
  const {t,ui,date:localDate}=useLocale();
  const article = item.representative_article;
  const [failedImages, setFailedImages] = useState<string[]>([]);
  const candidates = storyImages(item);
  const image = candidates.find(url=>!failedImages.includes(url));
  const url = safeExternalUrl(article.url);
  const date = article.published_at || article.first_seen_at;
  const others = item.articles.filter(row => row.id !== article.id);
  if(requireImage&&!image)return null;
  return <article className="py-4">
    <div className={requireImage?"flex flex-col-reverse gap-3":"flex items-start gap-4"}>
      <div className="min-w-0 flex-1">
        <h3 className="text-base font-medium leading-6">{url ? <a href={url} target="_blank" rel="noopener noreferrer" className="hover:text-primary">{article.title}</a> : article.title}</h3>
        <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">{item.research_category && <span>{ui({COMPANY:"Company",INDUSTRY:"Industry",MARKET_BRIEF:"Market"}[item.research_category])}</span>}<span>{article.source_name}</span><time dateTime={date}>{!article.published_at && t("First seen")+" "}{localDate(date,true)}</time><span>{t(item.story.source_count===1?"{count} independent source":"{count} independent sources",{count:item.story.source_count})}</span></div>
        <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs">{article.tickers.map(ticker => <Link key={ticker} href={`/stocks/${encodeURIComponent(ticker)}`} className="text-primary">{ticker}</Link>)}{article.topics.slice(0, 3).map(topic => <span key={topic} className="text-muted-foreground">{topic}</span>)}</div>
      </div>
      {image && <img src={image} alt="" loading="lazy" referrerPolicy="no-referrer" onError={() => {const failed=[...failedImages,image];setFailedImages(failed);if(requireImage&&candidates.every(url=>failed.includes(url)))onImageUnavailable?.();}} width={112} height={75} className={requireImage?"h-40 w-full rounded border bg-muted/30 object-contain":"h-[75px] w-24 shrink-0 rounded border bg-muted/30 object-contain sm:w-28"}/>}
    </div>
    {others.length > 0 && <details className="mt-3 text-xs"><summary className="cursor-pointer text-primary">{t("View other reporting")} ({others.length})</summary><ul className="mt-2 space-y-2 text-muted-foreground">{others.map(row => <li key={row.id}>{safeExternalUrl(row.url) && <a href={safeExternalUrl(row.url)!} target="_blank" rel="noopener noreferrer" className="hover:text-primary">{row.source_name} · {row.title} ↗</a>}</li>)}</ul></details>}
  </article>;
}
