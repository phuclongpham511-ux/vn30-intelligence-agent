"use client";
import {useLocale} from "@/lib/i18n";
import {useId,useState} from 'react';
import {X} from 'lucide-react';
import type {Security} from '@/lib/types';
import {stockSuggestions} from '@/lib/universe';
import {englishCompanyName} from '@/lib/presentation';
import {useRecentSearches} from './useRecentSearches';
import {useEquityPage} from '@/lib/useEquityPage';
type Props={stocks?:Security[];label:string;onSelect:(symbol:string)=>void;onQueryChange?:(query:string)=>void;disabled?:boolean;placeholder?:string};
export default function StockSearch({stocks,label,onSelect,onQueryChange,disabled=false,placeholder='Search ticker or company'}:Props) {
  const {t,ui}=useLocale();
  const [query,setQuery]=useState(''); const [open,setOpen]=useState(false); const [active,setActive]=useState(-1);
  const {recent,remember,remove,clear}=useRecentSearches(); const id=useId();
  const history=!query.trim();
  const remote=useEquityPage(history?{symbols:recent,size:8}:{query,size:6},stocks===undefined&&open&&!disabled&&(!history||recent.length>0),history?0:200);
  const rows=stocks||remote.data?.items||[];
  const matches=stocks?stockSuggestions(rows,query,recent):history?recent.flatMap(symbol=>rows.filter(row=>row.symbol===symbol)):rows;
  const unavailableRecent=history&&stocks===undefined&&remote.data?recent.filter(symbol=>!rows.some(row=>row.symbol===symbol)):[];
  const expanded=open && (!history || recent.length>0);
  const choose=(index:number)=>{const stock=matches[index];if(stock){remember(stock.symbol);setQuery('');onQueryChange?.('');setOpen(false);setActive(-1);onSelect(stock.symbol);}};
  return <div className="relative w-full min-w-0" onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget))setOpen(false);}}>
    <input role="combobox" aria-label={ui(label)} aria-expanded={expanded} aria-controls={expanded?id:undefined} aria-autocomplete="list" aria-activedescendant={expanded&&active>=0&&active<matches.length?id+'-'+active:undefined}
      className="h-10 w-full min-w-0 rounded border bg-background pl-3 pr-10 text-sm" placeholder={ui(placeholder)} autoComplete="off" disabled={disabled} value={query} maxLength={120}
      onFocus={()=>setOpen(true)} onChange={e=>{setQuery(e.target.value);onQueryChange?.(e.target.value);setOpen(true);setActive(-1);}}
      onKeyDown={e=>{if(e.key==='Escape'){setOpen(false);setActive(-1);}if(e.key==='ArrowDown'){e.preventDefault();setOpen(true);setActive(v=>Math.min(v+1,matches.length-1));}if(e.key==='ArrowUp'){e.preventDefault();setActive(v=>Math.max(v-1,0));}if(e.key==='Enter'&&open){e.preventDefault();choose(active>=0?active:Math.max(0,matches.findIndex(s=>s.symbol===query.trim().toUpperCase())));}}}/>
    {query&&<button type="button" aria-label={t('Clear search')} onMouseDown={e=>e.preventDefault()} onClick={()=>{setQuery('');onQueryChange?.('');setActive(-1);setOpen(true);}} className="absolute right-0 top-0 flex size-10 items-center justify-center text-muted-foreground"><X size={16}/></button>}
    {expanded && <div className="absolute top-full z-50 mt-1 w-full overflow-hidden rounded border bg-popover shadow-lg">
      <div className="flex items-center justify-between px-3 py-2 text-[10px] text-muted-foreground"><span>{ui(history?'Recent searches':'Matching equities')}</span>{history&&recent.length>0&&<button type="button" onMouseDown={e=>e.preventDefault()} onClick={()=>{clear();setActive(-1);setOpen(false);}} className="text-primary hover:underline">{t("Clear history")}</button>}</div>
      <ul id={id} role="listbox" aria-busy={remote.loading} aria-label={t('{label} results',{label:ui(label)})} className="max-h-[min(16rem,40dvh)] overflow-y-auto">{matches.map((stock,index)=><li key={stock.symbol} id={id+'-'+index} role="option" aria-selected={active===index} className="flex items-center">
        <button type="button" onMouseDown={e=>e.preventDefault()} onClick={()=>choose(index)} className={`flex min-w-0 flex-1 items-center gap-2 px-3 py-2 text-left text-xs hover:bg-muted ${active===index?'bg-muted':''}`}><strong className="w-12 shrink-0">{stock.symbol}</strong><span className="min-w-0 flex-1 truncate text-muted-foreground">{englishCompanyName(stock)||stock.exchange}</span><span>{stock.exchange}</span></button>
        {history&&<button type="button" aria-label={t('Remove {ticker} from search history',{ticker:stock.symbol})} onMouseDown={e=>e.preventDefault()} onClick={()=>{remove(stock.symbol);setActive(-1);}} className="flex h-9 w-9 shrink-0 items-center justify-center text-muted-foreground hover:bg-muted hover:text-foreground"><X size={14}/></button>}</li>)}</ul>
      {unavailableRecent.length>0&&<ul aria-label={t('Unavailable recent searches')}>{unavailableRecent.map(symbol=><li key={symbol} className="flex items-center gap-2 pl-3 text-xs text-muted-foreground"><span className="min-w-0 flex-1">{symbol} · {t('Equity metadata unavailable')}</span><button type="button" aria-label={t('Remove {ticker} from search history',{ticker:symbol})} onMouseDown={e=>e.preventDefault()} onClick={()=>remove(symbol)} className="flex size-9 shrink-0 items-center justify-center hover:bg-muted"><X size={14}/></button></li>)}</ul>}
      {remote.loading?<p role="status" className="px-3 pb-3 text-xs text-muted-foreground">{t('Searching equities…')}</p>:remote.error?<p role="alert" className="px-3 pb-3 text-xs">{t('Equity search unavailable')} <button type="button" onClick={remote.refresh} className="text-primary underline">{t('Retry')}</button></p>:!matches.length&&<p className="px-3 pb-3 text-xs text-muted-foreground">{t(history?'Recent tickers are no longer in the cached universe.':'No matching listed equities.')}</p>}
    </div>}
  </div>;
}
