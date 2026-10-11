"use client";
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {useLocale} from '@/lib/i18n';
import {cacheRefresh} from '@/lib/cacheRefresh';
import {marketFocusItems} from '@/lib/marketFocus';
import {newsSymbols} from '@/lib/newsPresentation';
import {LivePrices} from '../stock/LivePrice';
import TopStory,{type TopStoryData} from './TopStory';

export default function MarketFocus(){
  const {t}=useLocale();const [rows,setRows]=useState<TopStoryData[]|null>(null);const [error,setError]=useState(false);const [attempt,setAttempt]=useState(0);
  useEffect(()=>{
    const controller=new AbortController();let busy=false;
    const load=async()=>{if(busy)return;busy=true;try{
      const groups=await Promise.all(['MARKET_BRIEF','COMPANY'].map(async category=>{const response=await fetch('/api/news/feed?research_category='+category+'&limit=6',{cache:'no-store',signal:controller.signal});if(!response.ok)throw Error();return await response.json() as TopStoryData[];}));
      if(!controller.signal.aborted){setRows(marketFocusItems(groups.flat()));setError(false);}
    }catch{if(!controller.signal.aborted)setError(true);}finally{busy=false;}};
    void load();const stop=cacheRefresh(()=>{void load();});return()=>{controller.abort();stop();};
  },[attempt]);
  return <section aria-labelledby="market-focus" className="min-w-0 border-t pt-5 xl:border-l xl:border-t-0 xl:pl-8 xl:pt-0">
    <div className="mb-3 flex items-center justify-between gap-3"><h2 id="market-focus" className="scroll-mt-32">{t('Market Focus')}</h2><Link href="/news?view=briefing" className="text-xs text-primary hover:underline">{t('All news ↗')}</Link></div>
    {error&&<p role="alert" className="text-sm text-muted-foreground">{t('Market Focus is temporarily unavailable.')} <button className="text-primary underline" onClick={()=>setAttempt(n=>n+1)}>{t('Retry')}</button></p>}
    {!rows&&!error&&<p role="status" className="text-sm text-muted-foreground">{t('Loading publisher reporting…')}</p>}
    {rows&&!rows.length&&!error&&<p className="text-sm text-muted-foreground">{t('No qualified recent market highlights.')}</p>}
    {error&&!!rows?.length&&<p className="mt-2 text-xs text-muted-foreground">{t('Previously loaded headlines are shown below.')}</p>}
    <LivePrices symbols={newsSymbols(rows||[])} interval={30000}>{rows?.map(item=><TopStory key={item.story.id} item={item} compact/>)}</LivePrices>
    <details className="mt-3 text-[11px] text-muted-foreground"><summary className="cursor-pointer">{t('About these highlights')}</summary><p className="mt-2">{t('Recent Vietnam market reporting and companies identified in publisher evidence. Ordered by publication; coverage is partial. No sentiment or investment-quality score.')}</p><Link href="/news?view=community" className="mt-2 inline-block text-primary hover:underline">{t('All discussions ↗')}</Link></details>
  </section>;
}
