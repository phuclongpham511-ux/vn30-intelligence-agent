"use client";
import {useEffect,useState} from 'react';
import {readRecentSearches, rememberSearch, recentSearchKey, removeRecentSearch} from '@/lib/universe';
export function useRecentSearches() {
  const [recent,setRecent]=useState<string[]>([]);
  useEffect(()=>{
    const restore=()=>{try{setRecent(readRecentSearches(localStorage.getItem(recentSearchKey)));}catch{setRecent([]);}};
    restore(); window.addEventListener('storage',restore); window.addEventListener('equity-search',restore);
    return ()=>{window.removeEventListener('storage',restore);window.removeEventListener('equity-search',restore);};
  },[]);
  const update=(change:(rows:string[])=>string[])=>{
    let rows=recent;
    try { rows=readRecentSearches(localStorage.getItem(recentSearchKey)); } catch { /* In-memory history remains usable. */ }
    const next=change(rows); setRecent(next);
    try { localStorage.setItem(recentSearchKey,JSON.stringify(next)); window.dispatchEvent(new Event('equity-search')); } catch { /* Browser storage can be disabled. */ }
  };
  return {recent,remember:(symbol:string)=>update(rows=>rememberSearch(rows,symbol)),
    remove:(symbol:string)=>update(rows=>removeRecentSearch(rows,symbol)),clear:()=>update(()=>[])};
}
