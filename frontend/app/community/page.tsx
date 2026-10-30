"use client";
import {useEffect,useState} from 'react';
import {useLocale} from '@/lib/i18n';
import {communityHref,readCommunityWindow} from '@/lib/community';
import CommunityPulse from '../components/news/CommunityPulse';
import {Button} from '../components/ui/button';

export default function CommunityPage() {
  const {t}=useLocale();
  const [ticker,setTicker]=useState('');
  const [windowKind,setWindowKind]=useState<'today'|'last24h'>('today');
  const [ready,setReady]=useState(false);
  const [attempt,setAttempt]=useState(0);
  useEffect(()=>{
    const sync=()=>{
      setTicker((new URLSearchParams(window.location.search).get('ticker')||'').trim().toUpperCase());
      setWindowKind(readCommunityWindow(window.location.search));setReady(true);
    };
    sync();window.addEventListener('popstate',sync);
    return()=>window.removeEventListener('popstate',sync);
  },[]);
  useEffect(()=>{if(ready)window.history.replaceState(null,'',communityHref(ticker,windowKind));},[ticker,windowKind,ready]);
  return <div className="page-stack">
    <header className="news-page-header"><div><h1>{t('Community Pulse')}</h1><p>{t('Unverified discussion sample; no market sentiment is inferred.')}</p></div><Button variant="outline" onClick={()=>setAttempt(value=>value+1)}>{t('Refresh')}</Button></header>
    {ready&&<CommunityPulse key={ticker} ticker={ticker} topic="" attempt={attempt} initialWindow={windowKind} onWindowChange={setWindowKind} onTickerChange={setTicker}/>}
  </div>;
}
