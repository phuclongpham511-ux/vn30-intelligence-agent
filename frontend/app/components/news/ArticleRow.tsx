"use client";
import {useLocale} from "@/lib/i18n";
import Link from "next/link";
import type { NewsArticle,TickerAssociation } from "@/lib/news";
import {qualifiedAssociations} from '@/lib/newsPresentation';
import { safeExternalUrl } from "@/lib/presentation";
import NewsThumbnail from "./NewsThumbnail";

export default function ArticleRow({ article, requireImage=true, associations=[] }: { article: NewsArticle; requireImage?:boolean; associations?:TickerAssociation[] }) {
  const {t,date:localDate}=useLocale();
  const date = article.published_at || article.first_seen_at;
  const url = safeExternalUrl(article.url);
  const qualified=qualifiedAssociations(article,associations);
  return <NewsThumbnail required={requireImage} images={[article.thumbnail_url]} revision={article.last_seen_at}>{image=><article className="border-b py-4 last:border-0">
    <div className="flex items-start gap-4">{image}<div className="min-w-0 flex-1">
    <div className="mb-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
      <span>{article.source_name}</span>
      <span>{!article.published_at && t("First seen")+" "}<time dateTime={date}>{localDate(date,true)}</time></span>
    </div>
    <h3 className="text-sm font-medium leading-6">{article.title}</h3>
    <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted-foreground">
      {article.tickers.map(ticker => {const proof=qualified.find(a=>a.symbol===ticker);return proof?
        <Link key={ticker} href={`/stocks/${encodeURIComponent(ticker)}`} title={`${t('Issuer context')}: ${proof.matched_text}`} className="rounded border px-2 py-0.5 text-primary hover:underline">{ticker}</Link>:
        <span key={ticker} title={t('Stored tag; issuer association unverified.')} className="rounded border px-2 py-0.5">{ticker} · {t('Unverified')}</span>;})}
      {[...article.topics, ...article.sectors].filter((v, i, arr) => arr.indexOf(v) === i).map(tag => <span key={tag} className="rounded border px-2 py-0.5">{tag}</span>)}
    </div>
    {url && <a className="mt-3 inline-block text-xs text-primary underline-offset-4 hover:underline focus-visible:outline" href={url} target="_blank" rel="noopener noreferrer">{t("Read original ↗")}</a>}
    </div></div>
  </article>}</NewsThumbnail>;
}
