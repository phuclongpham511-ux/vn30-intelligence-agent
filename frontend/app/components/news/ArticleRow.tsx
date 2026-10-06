"use client";
import {useLocale} from "@/lib/i18n";
import Link from "next/link";
import type { NewsArticle } from "@/lib/news";
import { safeExternalUrl } from "@/lib/presentation";

export default function ArticleRow({ article }: { article: NewsArticle }) {
  const {t,date:localDate}=useLocale();
  const date = article.published_at || article.first_seen_at;
  const url = safeExternalUrl(article.url);
  return <article className="border-b py-4 last:border-0">
    <div className="mb-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
      <span>{article.source_name}</span>
      <span>{!article.published_at && t("First seen")+" "}<time dateTime={date}>{localDate(date,true)}</time></span>
    </div>
    <h3 className="text-sm font-medium leading-6">{article.title}</h3>
    <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
      {article.tickers.map(ticker => <Link key={ticker} href={`/stocks/${encodeURIComponent(ticker)}`} className="rounded border px-2 py-0.5 text-primary hover:underline">{ticker}</Link>)}
      {[...article.topics, ...article.sectors].filter((v, i, arr) => arr.indexOf(v) === i).map(tag => <span key={tag} className="rounded border px-2 py-0.5">{tag}</span>)}
    </div>
    {url && <a className="mt-3 inline-block text-xs text-primary underline-offset-4 hover:underline focus-visible:outline" href={url} target="_blank" rel="noopener noreferrer">{t("Read original ↗")}</a>}
  </article>;
}
