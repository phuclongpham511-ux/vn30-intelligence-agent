"use client";
import {useLocale} from '@/lib/i18n';
import type {ReactNode} from 'react';
import Link from 'next/link';
import type {NewsArticle,TickerAssociation} from '@/lib/news';
import {storyImages} from '@/lib/storyImages';
import {safeExternalUrl} from '@/lib/presentation';
import {relatedTickers,allRelatedTickers} from '@/lib/newsPresentation';
import {TickerMovement} from '../stock/LivePrice';
import NewsThumbnail from './NewsThumbnail';

export type TopStoryData={story:{id:string;representative_title:string;source_count:number;article_count?:number};representative_article:NewsArticle;articles:NewsArticle[];thumbnail_url?:string|null;thumbnail_article_id?:string|null;research_category?:'COMPANY'|'INDUSTRY'|'MARKET_BRIEF'|null;ticker_associations?:TickerAssociation[]};

export default function TopStory({item,compact=false,textOnly=false,showThumbnail=!textOnly,featured=false,reserveThumbnailSpace=false}:{item:TopStoryData;requireImage?:boolean;compact?:boolean;textOnly?:boolean;showThumbnail?:boolean;featured?:boolean;reserveThumbnailSpace?:boolean}) {
  const {t,date}=useLocale();const article=item.representative_article;
  const url=safeExternalUrl(article.url);const published=article.published_at||article.first_seen_at;
  const symbols=relatedTickers(item);
  const content=(image:ReactNode)=><article className={`news-card${featured?' news-card-featured':''}`} data-story-id={item.story.id}>
    <div className={featured?'news-featured-layout':'flex items-start gap-3 sm:gap-4'}>{image}<div className="min-w-0 flex-1">
      <h3 className={featured?'news-featured-title':compact?'text-sm font-semibold leading-5':'text-base font-semibold leading-6'}>{url?<a href={url} target="_blank" rel="noopener noreferrer" className="rounded-sm hover:text-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">{article.title}</a>:article.title}</h3>
      <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-muted-foreground"><span>{article.source_name}</span><span aria-hidden="true">·</span><time dateTime={published}>{!article.published_at&&t('First seen')+' '}{date(published,true)}</time>
      </div>
      {symbols.length>0&&<div className="mt-3 flex flex-wrap gap-1.5" aria-label={t('Mentioned stocks')} title={t('Publisher evidence association; price movement does not establish news impact.')}>
        {symbols.map(symbol=><Link key={symbol} href={`/stocks/${encodeURIComponent(symbol)}`} className="ticker-chip"><strong className="text-foreground">{symbol}</strong>{!textOnly&&<TickerMovement symbol={symbol}/>}</Link>)}
        {allRelatedTickers(item).length>symbols.length&&<details className="self-center text-[11px]"><summary className="cursor-pointer text-muted-foreground">{t('More stocks ({count})',{count:allRelatedTickers(item).length-symbols.length})}</summary><div className="mt-2 flex flex-wrap gap-1.5">{allRelatedTickers(item).slice(symbols.length).map(symbol=><Link key={symbol} href={`/stocks/${encodeURIComponent(symbol)}`} className="ticker-chip">{symbol}</Link>)}</div></details>}
      </div>}
    </div></div>
  </article>;
  // Homepage thumbnails reuse existing same-Story metadata; text-only ticker
  // context still avoids another live-price consumer.
  return showThumbnail?<NewsThumbnail required={false} reserveSpace={reserveThumbnailSpace||textOnly} wide={featured} images={storyImages(item)} compact={compact} revision={item.articles.map(a=>a.last_seen_at||'').join('|')}>{content}</NewsThumbnail>:content(null);
}
