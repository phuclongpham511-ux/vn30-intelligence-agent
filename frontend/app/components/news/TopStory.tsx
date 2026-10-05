"use client";
import { useState } from "react";
import Link from "next/link";
import type { NewsArticle } from "@/lib/news";
import { safeExternalUrl } from "@/lib/presentation";

export type TopStoryData = { story: { id: string; representative_title: string; source_count: number }; representative_article: NewsArticle; articles: NewsArticle[] };

export default function TopStory({ item }: { item: TopStoryData }) {
  const article = item.representative_article;
  const [failedImage, setFailedImage] = useState<string | null>(null);
  const image = safeExternalUrl(article.thumbnail_url || null);
  const url = safeExternalUrl(article.url);
  const date = article.published_at || article.first_seen_at;
  const others = item.articles.filter(row => row.id !== article.id);
  return <article className="py-4">
    <div className="flex items-start gap-4">
      <div className="min-w-0 flex-1">
        <h3 className="text-base font-medium leading-6">{url ? <a href={url} target="_blank" rel="noopener noreferrer" className="hover:text-primary">{item.story.representative_title}</a> : item.story.representative_title}</h3>
        <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground"><span>{article.source_name}</span><time dateTime={date}>{!article.published_at && "First seen "}{new Date(date).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })}</time><span>{item.story.source_count} independent {item.story.source_count === 1 ? "source" : "sources"}</span></div>
        <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs">{article.tickers.map(ticker => <Link key={ticker} href={`/stocks/${encodeURIComponent(ticker)}`} className="text-primary">{ticker}</Link>)}{article.topics.slice(0, 3).map(topic => <span key={topic} className="text-muted-foreground">{topic}</span>)}</div>
      </div>
      {image && failedImage !== image && <img src={image} alt="" loading="lazy" referrerPolicy="no-referrer" onError={() => setFailedImage(image)} width={112} height={75} className="h-[75px] w-24 shrink-0 rounded object-cover sm:w-28"/>}
    </div>
    {others.length > 0 && <details className="mt-3 text-xs"><summary className="cursor-pointer text-primary">View other reporting ({others.length})</summary><ul className="mt-2 space-y-2 text-muted-foreground">{others.map(row => <li key={row.id}>{safeExternalUrl(row.url) && <a href={safeExternalUrl(row.url)!} target="_blank" rel="noopener noreferrer" className="hover:text-primary">{row.source_name} · {row.title} ↗</a>}</li>)}</ul></details>}
  </article>;
}
