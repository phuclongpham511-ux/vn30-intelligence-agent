"use client";
import {useState} from 'react';
import Link from 'next/link';
import {useLocale} from '@/lib/i18n';
import HotTopics from './HotTopics';
import MarketFocus from './MarketFocus';

export default function MarketNewsContext(){
  const {t}=useLocale(),[view,setView]=useState<'hot'|'focus'>('hot');
  return <section className="market-news-context" aria-label={t('Publisher news context')}>
    <div className="market-news-heading">
      <div className="market-news-options" role="group" aria-label={t('Publisher news context')}>
        <button type="button" id="market-news-hot-option" aria-pressed={view==='hot'} aria-controls="market-news-hot-panel" onClick={()=>setView('hot')}>{t('Hot Topics')}</button>
        <button type="button" id="market-news-focus-option" aria-pressed={view==='focus'} aria-controls="market-news-focus-panel" onClick={()=>setView('focus')}>{t('Market Focus')}</button>
      </div>
      <Link href={view==='hot'?'/news':'/news?view=briefing'}>{t('All news ↗')}</Link>
    </div>
    <div id="market-news-hot-panel" aria-labelledby="market-news-hot-option" hidden={view!=='hot'}><HotTopics embedded active={view==='hot'}/></div>
    <div id="market-news-focus-panel" aria-labelledby="market-news-focus-option" hidden={view!=='focus'}><MarketFocus compact embedded active={view==='focus'}/></div>
  </section>;
}
