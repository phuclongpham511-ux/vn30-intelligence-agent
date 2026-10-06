"use client";
import {createContext,createElement,useContext,useEffect,useMemo,useState,type ReactNode} from 'react';
import {vietnamese,translate,readLanguage,languageStorageKey,type Language,type TranslationKey} from './translations.ts';

export function localeTools(language:Language) {
  const locale=language==='vi'?'vi-VN':'en-GB';
  const t=(key:TranslationKey,params?:Record<string,string|number>)=>translate(language,key,params);
  // Only call ui for known product labels or UI errors, never source evidence.
  const ui=(value:string)=>Object.hasOwn(vietnamese,value)?t(value as TranslationKey):value;
  const date=(value:string|null|undefined,withTime=false)=>{
    if(!value||!Number.isFinite(Date.parse(value)))return t('Unavailable');
    return new Intl.DateTimeFormat(locale,{timeZone:'Asia/Ho_Chi_Minh',...(language==='vi'?{day:'2-digit',month:'2-digit',year:'numeric'}:{dateStyle:'medium'}),...(withTime?(language==='vi'?{hour:'2-digit',minute:'2-digit'}:{timeStyle:'short'}):{})}).format(new Date(value));
  };
  const number=(value:unknown,decimals=2)=>typeof value==='number'&&Number.isFinite(value)?new Intl.NumberFormat(locale,{maximumFractionDigits:decimals}).format(value):'—';
  const percent=(value:unknown,signed=false)=>typeof value==='number'&&Number.isFinite(value)?new Intl.NumberFormat(locale,{style:'percent',maximumFractionDigits:2,signDisplay:signed?'exceptZero':'auto'}).format(value):'—';
  const compact=(value:unknown)=>typeof value==='number'&&Number.isFinite(value)?new Intl.NumberFormat(locale,{notation:'compact',maximumFractionDigits:1}).format(value):'—';
  return {language,locale,t,ui,date,number,percent,compact};
}
const fallback={...localeTools('en'),setLanguage:(_language:Language)=>{}};
export const LanguageContext=createContext(fallback);
export function LanguageProvider({children}: {children:ReactNode}) {
  const [language,setLanguageState]=useState<Language>('en');
  const [ready,setReady]=useState(false);
  useEffect(()=>{
    const restore=()=>{let raw:null|string=null;try{raw=localStorage.getItem(languageStorageKey);}catch{/* Storage may be disabled. */}setLanguageState(readLanguage(raw,navigator.language));};
    restore();setReady(true);window.addEventListener('storage',restore);
    return()=>window.removeEventListener('storage',restore);
  },[]);
  useEffect(()=>{if(ready)document.documentElement.lang=language;},[language,ready]);
  const value=useMemo(()=>({...localeTools(language),setLanguage:(next:Language)=>{setLanguageState(next);try{localStorage.setItem(languageStorageKey,next);}catch{/* Language remains usable in this session. */}}}),[language]);
  return createElement(LanguageContext.Provider,{value},children);
}
export function useLocale(){return useContext(LanguageContext);}
