"use client";
import {useLocale} from '@/lib/i18n';
import Link from 'next/link';
import type {NewsArticle} from '@/lib/news';
import {storyImages} from '@/lib/storyImages';
import {safeExternalUrl} from '@/lib/presentation';
import {relatedTickers} from '@/lib/newsPresentation';
import {TickerMovement} from '../stock/LivePrice';
import NewsThumbnail from './NewsThumbnail';

export type TopStoryData={story:{id:string;representative_title:string;source_count:number;article_count?:number};representative_article:NewsArticle;articles:NewsArticle[];thumbnail_url?:string|null;thumbnail_article_id?:string|null;research_category?:'COMPANY'|'INDUSTRY'|'MARKET_BRIEF'|null};

export default function TopStory({item,compact=false}:{item:TopStoryData;requireImage?:boolean;compact?:boolean}) {
  const {t,date}=useLocale();const article=item.representative_article;
  const url=safeExternalUrl(article.url);const published=article.published_at||article.first_seen_at;
  const symbols=relatedTickers(item);
  return <NewsThumbnail images={storyImages(item)} compact={compact} revision={item.articles.map(a=>a.last_seen_at||'').join('|')}>{image=><article className="news-card" data-story-id={item.story.id}>
    <div className="flex items-start gap-3 sm:gap-4">{image}<div className="min-w-0 flex-1">
      <h3 className={compact?'text-sm font-semibold leading-5':'text-base font-semibold leading-6'}>{url?<a href={url} target="_blank" rel="noopener noreferrer" className="hover:text-primary">{article.title}</a>:article.title}</h3>
      <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-muted-foreground"><span>{article.source_name}</span><span aria-hidden="true">·</span><time dateTime={published}>{!article.published_at&&t('First seen')+' '}{date(published,true)}</time>
        <Link href={`/news/stories/${encodeURIComponent(item.story.id)}`} className="ml-auto text-primary hover:underline">{t('Evidence')}</Link>
      </div>
      {symbols.length>0&&<div className="mt-3 flex flex-wrap gap-1.5" aria-label={t('Mentioned stocks')} title={t('Headline association; price movement does not establish news impact.')}>
        {symbols.map(symbol=><Link key={symbol} href={`/stocks/${encodeURIComponent(symbol)}`} className="ticker-chip"><strong className="text-foreground">{symbol}</strong><TickerMovement symbol={symbol}/></Link>)}
        {article.tickers.length>symbols.length&&<Link href={`/news/stories/${encodeURIComponent(item.story.id)}`} className="self-center text-[11px] text-muted-foreground">+{article.tickers.length-symbols.length}</Link>}
      </div>}
    </div></div>
  </article>}</NewsThumbnail>;
}
