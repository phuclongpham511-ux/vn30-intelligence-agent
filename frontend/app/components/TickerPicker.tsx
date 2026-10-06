"use client";
import Link from "next/link";
import {useRouter} from "next/navigation";
import StockSearch from "./stock/StockSearch";
import { useState } from "react";
import { ArrowUpRight } from "lucide-react";
import { useStocks } from "./stock/StockUniverse";
import { englishCompanyName } from "@/lib/presentation";
import { browseSecurities } from "@/lib/universe";
import { Button } from "./ui/button";
import { useRecentSearches } from "./stock/useRecentSearches";
import { MascotState } from "./mascot/Mascot";
export default function TickerPicker() {
  const router=useRouter();
  const { stocks, loading, error, refresh, status, lastSynced, groups } = useStocks();
  const [query, setQuery] = useState('');
  const [exchange, setExchange] = useState('');
  const {remember}=useRecentSearches();
  const [group,setGroup]=useState('');
  const [page, setPage] = useState(0);
  const result = browseSecurities(stocks, query, exchange, page, 10, group ? groups?.groups[group] || [] : undefined);
  return <section aria-labelledby="explore-title">
    <div className="mb-4 flex flex-wrap items-center justify-between gap-2"><h2 id="explore-title">Explore stocks <span className="ml-2 text-xs font-normal text-muted-foreground">{stocks.length || (!loading && !error && status === 'healthy') ? `${stocks.length.toLocaleString('en-GB')} Vietnam equities` : 'Universe count unavailable'}</span></h2><span className="text-xs text-muted-foreground">SSI metadata{lastSynced ? ` · Synced ${new Date(lastSynced).toLocaleString('en-GB')}` : ''}</span></div>
    <div className="mb-4 flex flex-wrap gap-3"><div className="min-w-0 w-full text-xs sm:w-auto sm:flex-1"><span className="mb-1 block">Ticker or company</span><StockSearch stocks={stocks} label="Explore ticker or company" disabled={loading} onQueryChange={value=>{setQuery(value);setPage(0);}} onSelect={symbol=>router.push(`/stocks/${encodeURIComponent(symbol)}`)}/></div>
      <label className="text-xs">Exchange<select aria-label="Exchange" className="mt-1 block h-10 rounded border bg-background px-3 text-sm" value={exchange} onChange={e=>{setExchange(e.target.value);setPage(0);}}><option value="">All exchanges</option>{['HOSE','HNX','UPCOM'].map(e=><option key={e}>{e}</option>)}</select></label><label className="text-xs">Index group<select aria-label="Index group" className="mt-1 block h-10 rounded border bg-background px-3 text-sm" value={group} onChange={e=>{setGroup(e.target.value);setPage(0);}}><option value="">All equities</option>{['VN30','VN100','HNX30'].map(code=><option key={code} disabled={!groups?.groups[code]?.length}>{code}{!groups?.groups[code]?.length?' (unavailable)':''}</option>)}</select></label></div>

    {group && <p className="mb-3 text-xs text-muted-foreground">{group} membership · {groups?.source}{groups?.last_synced_at ? ` · Synced ${new Date(groups.last_synced_at).toLocaleString('en-GB')}`:''}{groups?.status!=='healthy'?' · cached / incomplete coverage':''}</p>}
    {loading ? <MascotState state="loading" role="status">Loading equity metadata…</MascotState> : error ? <p role="alert">{error} <button className="text-primary underline" onClick={refresh}>Retry</button></p> : <>
      {status !== 'healthy' && <p role="status" className="mb-3 text-xs text-muted-foreground">{stocks.length ? 'Showing cached metadata; the latest refresh is unavailable or stale.' : 'Equity metadata has not been acquired yet.'}</p>}
      {!result.total ? <MascotState state="dataUnavailable">No matching equities in the cached universe.</MascotState> : <div className="panel divide-y">{result.items.map(stock=><Link key={stock.symbol} onClick={()=>remember(stock.symbol)} href={`/stocks/${stock.symbol}`} className="flex items-center gap-3 px-4 py-3 hover:bg-muted">
        <span className="w-16 shrink-0 text-sm font-semibold">{stock.symbol}</span><span className="min-w-0 flex-1 truncate text-xs text-muted-foreground">{englishCompanyName(stock) || `${stock.symbol} · ${stock.exchange}`}</span><span className="text-xs text-muted-foreground">{stock.exchange}</span><ArrowUpRight size={14}/></Link>)}</div>}
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground"><span>{result.total ? page * 10 + 1 : 0}–{Math.min((page+1)*10,result.total)} of {result.total.toLocaleString('en-GB')} results</span><div className="flex gap-2"><Button variant="outline" disabled={!page} onClick={()=>setPage(page-1)}>Previous</Button><Button variant="outline" disabled={(page+1)*10>=result.total} onClick={()=>setPage(page+1)}>Next</Button></div></div>
    </>}
  </section>;
}
