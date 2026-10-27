"use client";
import {useEffect,useState} from 'react';
import {Check,Plus} from 'lucide-react';
import {readWatchlist,followStock,unfollowStock,watchlistStorageKey,watchlistChangedEvent,type WatchlistState} from '@/lib/watchlist';
import {useLocale} from '@/lib/i18n';
import {Button} from '../ui/button';

export default function FollowStock({ticker,available}:{ticker:string;available:boolean}) {
  const {t}=useLocale();
  const [state,setState]=useState<WatchlistState|null>(null);
  const [failed,setFailed]=useState(false);
  useEffect(()=>{
    const restore=()=>{try {setState(readWatchlist(localStorage.getItem(watchlistStorageKey)));setFailed(false);}catch{setState(null);setFailed(true);}};
    restore();window.addEventListener('storage',restore);window.addEventListener('focus',restore);window.addEventListener(watchlistChangedEvent,restore);
    return()=>{window.removeEventListener('storage',restore);window.removeEventListener('focus',restore);window.removeEventListener(watchlistChangedEvent,restore);};
  },[ticker]);
  const following=state?.symbols.includes(ticker)===true;
  const full=!!state&&!following&&state.symbols.length>=50;
  const toggle=()=>{
    try {
      const current=readWatchlist(localStorage.getItem(watchlistStorageKey));
      // Removal is browser-local; a missing issuer must not trap membership.
      // Re-read membership first so a stale button cannot re-follow it offline.
      if(!available&&!current.symbols.includes(ticker))return;
      const next=current.symbols.includes(ticker)?unfollowStock(current,ticker):followStock(current,ticker);
      localStorage.setItem(watchlistStorageKey,JSON.stringify(next));setState(next);setFailed(false);window.dispatchEvent(new Event(watchlistChangedEvent));
    }catch{setFailed(true);setState(null);}
  };
  return <div className="stock-follow">
    <Button variant={following?'secondary':'outline'} disabled={(!available&&!following)||!state||full} aria-pressed={following} onClick={toggle}>{following?<Check size={14}/>:<Plus size={14}/>} {t(following?'Following':'Follow stock')}</Button>
    <p className="mt-1 text-[10px] text-muted-foreground" role={failed?'alert':undefined}>{t(failed?'Saved Watchlist is unavailable. No changes made.':full?'Watchlist is full (50 stocks).':'Saved in this browser')}</p>
  </div>;
}
