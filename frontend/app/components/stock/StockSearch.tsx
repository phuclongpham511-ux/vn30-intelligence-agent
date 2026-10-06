"use client";
import {useId,useState} from 'react';
import type {Security} from '@/lib/types';
import {stockSuggestions} from '@/lib/universe';
import {englishCompanyName} from '@/lib/presentation';
import {useRecentSearches} from './useRecentSearches';
export default function StockSearch({stocks,label,onSelect,disabled=false,placeholder='Search ticker or company'}:{stocks:Security[];label:string;onSelect:(symbol:string)=>void;disabled?:boolean;placeholder?:string}) {
  const [query,setQuery]=useState(''); const [open,setOpen]=useState(false); const [active,setActive]=useState(-1);
  const {recent,remember}=useRecentSearches(); const id=useId();
  const matches=stockSuggestions(stocks,query,recent); const expanded=open && (query.trim().length>0 || matches.length>0);
  const choose=(index:number)=>{const stock=matches[index];if(stock){remember(stock.symbol);setQuery('');setOpen(false);setActive(-1);onSelect(stock.symbol);}};
  return <div className="relative w-full min-w-0" onBlur={e=>{if(!e.currentTarget.contains(e.relatedTarget))setOpen(false);}}>
    <input role="combobox" aria-label={label} aria-expanded={expanded} aria-controls={id} aria-autocomplete="list" aria-activedescendant={expanded&&active>=0?id+'-'+active:undefined}
      className="h-10 w-full min-w-0 rounded border bg-background px-3 text-sm" placeholder={placeholder} autoComplete="off" disabled={disabled} value={query} maxLength={120}
      onFocus={()=>setOpen(true)} onChange={e=>{setQuery(e.target.value);setOpen(true);setActive(-1);}}
      onKeyDown={e=>{if(e.key==='Escape'){setOpen(false);setActive(-1);}if(e.key==='ArrowDown'){e.preventDefault();setOpen(true);setActive(v=>Math.min(v+1,matches.length-1));}if(e.key==='ArrowUp'){e.preventDefault();setActive(v=>Math.max(v-1,0));}if(e.key==='Enter'){e.preventDefault();choose(active>=0?active:Math.max(0,matches.findIndex(s=>s.symbol===query.trim().toUpperCase())));}}}/>
    {expanded && <div className="absolute top-full z-50 mt-1 w-full overflow-hidden rounded border bg-popover shadow-lg">
      <p className="px-3 py-2 text-[10px] text-muted-foreground">{query.trim()?'Matching equities':'Recent searches'}</p>
      <ul id={id} role="listbox" aria-label={label+' results'}>{matches.map((stock,index)=><li key={stock.symbol} id={id+'-'+index} role="option" aria-selected={active===index}>
        <button type="button" onMouseDown={e=>e.preventDefault()} onClick={()=>choose(index)} className={`flex w-full items-center gap-2 px-3 py-2 text-left text-xs hover:bg-muted ${active===index?'bg-muted':''}`}><strong className="w-12 shrink-0">{stock.symbol}</strong><span className="min-w-0 flex-1 truncate text-muted-foreground">{englishCompanyName(stock)||stock.exchange}</span><span>{stock.exchange}</span></button></li>)}</ul>
      {!matches.length && <p className="px-3 pb-3 text-xs text-muted-foreground">No matching listed equities.</p>}
    </div>}
  </div>;
}
