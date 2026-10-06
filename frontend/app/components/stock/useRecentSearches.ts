"use client";
import {useEffect,useState} from 'react';
import {readRecentSearches, rememberSearch, recentSearchKey} from '@/lib/universe';
export function useRecentSearches() {
  const [recent,setRecent]=useState<string[]>([]);
  useEffect(()=>{
    const restore=()=>{try{setRecent(readRecentSearches(localStorage.getItem(recentSearchKey)));}catch{setRecent([]);}};
    restore(); window.addEventListener('storage',restore); window.addEventListener('equity-search',restore);
    return ()=>{window.removeEventListener('storage',restore);window.removeEventListener('equity-search',restore);};
  },[]);
  const remember=(symbol:string)=>{try{localStorage.setItem(recentSearchKey,JSON.stringify(rememberSearch(readRecentSearches(localStorage.getItem(recentSearchKey)),symbol)));window.dispatchEvent(new Event('equity-search'));}catch{/* Search remains usable without browser storage. */}};
  return {recent,remember};
}
