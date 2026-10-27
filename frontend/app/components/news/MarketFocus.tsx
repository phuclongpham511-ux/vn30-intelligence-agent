"use client";
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {useLocale} from '@/lib/i18n';
import {cacheRefresh} from '@/lib/cacheRefresh';
import {marketFocusItems} from '@/lib/marketFocus';
import {safeExternalUrl} from '@/lib/presentation';
import {newsSymbols} from '@/lib/newsPresentation';
import {LivePrices} from '../stock/LivePrice';
import TopStory,{type TopStoryData} from './TopStory';

export default function MarketFocus({compact=false,embedded=false,active=true}:{compact?:boolean;embedded?:boolean;active?:boolean}){
  const {t,date}=useLocale();const [rows,setRows]=useState<TopStoryData[]|null>(null);const [error,setError]=useState(false);const [attempt,setAttempt]=useState(0);
  useEffect(()=>{
    if(!active)return;
    const controller=new AbortController();let busy=false;
    const load=async()=>{if(busy)return;busy=true;try{
      const groups=await Promise.all(['MARKET_BRIEF','COMPANY'].map(async category=>{const response=await fetch('/api/news/feed?research_category='+category+'&limit=6',{cache:'no-store',signal:controller.signal});if(!response.ok)throw Error();return await response.json() as TopStoryData[];}));
      if(!controller.signal.aborted){const now=Date.now();setRows(marketFocusItems(groups.flat().filter(item=>!compact||(now-Date.parse(item.representative_article.published_at||item.representative_article.first_seen_at)>=0&&now-Date.parse(item.representative_article.published_at||item.representative_article.first_seen_at)<=86400000))));setError(false);}
    }catch{if(!controller.signal.aborted)setError(true);}finally{busy=false;}};
    void load();const stop=cacheRefresh(()=>{void load();});return()=>{controller.abort();stop();};
  },[attempt,compact,active]);
  return <section aria-label={embedded?t('Market Focus'):undefined} aria-labelledby={embedded?undefined:'market-focus'} className={embedded?'market-focus-embedded':compact?'market-focus-compact quote-panel':'min-w-0 border-t pt-5 xl:border-l xl:border-t-0 xl:pl-8 xl:pt-0'}>
    {!embedded&&<div className="mb-3 flex items-center justify-between gap-3"><h2 id="market-focus" className="scroll-mt-32">{t('Market Focus')}</h2><Link href="/news?view=briefing" className="text-xs text-primary hover:underline">{t('All news ↗')}</Link></div>}
    {error&&<p role="alert" className="text-sm text-muted-foreground">{t('Market Focus is temporarily unavailable.')} <button className="text-primary underline" onClick={()=>setAttempt(n=>n+1)}>{t('Retry')}</button></p>}
    {!rows&&!error&&<p role="status" className="text-sm text-muted-foreground">{t('Loading publisher reporting…')}</p>}
    {rows&&!rows.length&&!error&&<p className="text-sm text-muted-foreground">{t('No qualified recent market highlights.')}</p>}
    {error&&!!rows?.length&&<p className="mt-2 text-xs text-muted-foreground">{t('Previously loaded headlines are shown below.')}</p>}
    {compact?<div className="market-focus-stories">{rows?.map(item=>{const article=item.representative_article,url=safeExternalUrl(article.url),published=article.published_at||article.first_seen_at;return <article key={item.story.id} data-story-id={item.story.id}><h3>{url?<a href={url} target="_blank" rel="noopener noreferrer">{article.title} ↗</a>:article.title}</h3><p>{article.source_name} · {!article.published_at&&t('First seen')+' '}<time dateTime={published}>{date(published,true)}</time> · {t(item.research_category==='MARKET_BRIEF'?'Market':'Company')}</p></article>;})}</div>:<LivePrices symbols={newsSymbols(rows||[])} interval={30000}>{rows?.map(item=><TopStory key={item.story.id} item={item} compact/>)}</LivePrices>}
    <details className="mt-3 text-[11px] text-muted-foreground"><summary className="cursor-pointer">{t('About these highlights')}</summary><p className="mt-2">{t('Recent Vietnam market reporting and companies identified in publisher evidence. Ordered by publication; coverage is partial. No sentiment or investment-quality score.')}</p>{compact&&<p>{t('Last 24 hours · publisher evidence, not a cause of price movement.')}</p>}<Link href="/community" className="mt-2 inline-block text-primary hover:underline">{t('All discussions ↗')}</Link></details>
  </section>;
}
