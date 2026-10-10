"use client";
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {useRouter} from 'next/navigation';
import {ArrowUpRight} from 'lucide-react';
import {useLocale} from '@/lib/i18n';
import {useEquityPage} from '@/lib/useEquityPage';
import type {IndexGroups} from '@/lib/universe';
import {englishCompanyName} from '@/lib/presentation';
import StockSearch from './stock/StockSearch';
import {useRecentSearches} from './stock/useRecentSearches';
import {LivePrices,LivePrice} from './stock/LivePrice';
import {Button} from './ui/button';

export default function TickerPicker() {
  const {t,language,date,number}=useLocale();
  const router=useRouter();
  const {remember}=useRecentSearches();
  const [query,setQuery]=useState('');
  const [exchange,setExchange]=useState('');
  const [group,setGroup]=useState('');
  const [page,setPage]=useState(0);
  const {data,loading,error,refresh}=useEquityPage({query,exchange,group,page,size:10},true,query?200:0);
  const [metadata,setMetadata]=useState<{count?:number;groups?:IndexGroups}|null>(null);
  useEffect(()=>{
    if(data){
      setMetadata({count:data.status==='healthy'||data.total_universe>0?data.total_universe:undefined,groups:data.index_groups});
      if(data.total>0&&page*10>=data.total)setPage(Math.ceil(data.total/10)-1);
    }
  },[data,page]);
  const groups=data?.index_groups||metadata?.groups;
  const count=data?(data.status==='healthy'||data.total_universe>0?data.total_universe:undefined):metadata?.count;
  return <LivePrices symbols={data?.items.map(stock=>stock.symbol)||[]} interval={30000}>
    <section aria-labelledby="explore-title" aria-busy={loading}>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
        <div><h2 id="explore-title">{t('Explore stocks')}</h2><p className="mt-1 text-xs text-muted-foreground">{count===undefined?t('Universe count unavailable'):t('{count} Vietnam equities',{count:number(count,0)})}</p></div>
        <p className="text-xs text-muted-foreground">{t('SSI metadata')}{data?.last_synced_at?' · '+t('Synced {date}',{date:date(data.last_synced_at,true)}):''}</p>
      </div>
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="w-full min-w-0 sm:w-auto sm:flex-1"><p className="mb-1 text-xs">{t('Ticker or company')}</p><StockSearch label="Explore ticker or company" onQueryChange={value=>{setQuery(value);setPage(0);}} onSelect={symbol=>router.push('/stocks/'+encodeURIComponent(symbol))}/></div>
        <label className="flex-1 text-xs sm:flex-none">{t('Exchange')}<select aria-label={t('Exchange')} className="mt-1 block h-10 w-full rounded border bg-background px-3 text-sm" value={exchange} onChange={event=>{setExchange(event.target.value);setPage(0);}}><option value="">{t('All exchanges')}</option>{['HOSE','HNX','UPCOM'].map(code=><option key={code}>{code}</option>)}</select></label>
        <label className="flex-1 text-xs sm:flex-none">{t('Index group')}<select aria-label={t('Index group')} className="mt-1 block h-10 w-full rounded border bg-background px-3 text-sm" value={group} onChange={event=>{setGroup(event.target.value);setPage(0);}}><option value="">{t('All equities')}</option>{['VN30','VN100','HNX30'].map(code=><option key={code} value={code} disabled={!groups?.groups[code]?.length}>{code}{!groups?.groups[code]?.length?' '+t('(unavailable)'):''}</option>)}</select></label>
      </div>
      {group&&<p className="mb-3 text-xs text-muted-foreground">{group} {t('membership')} · {groups?.source}{groups?.last_synced_at?' · '+t('Synced {date}',{date:date(groups.last_synced_at,true)}):''}{groups?.status!=='healthy'?' · '+t('cached / incomplete coverage'):''}</p>}
      {loading?<div role="status" className="rounded border p-4"><p className="text-sm text-muted-foreground">{t('Loading equities…')}</p><div aria-hidden="true" className="mt-3 space-y-3">{Array.from({length:5},(_,n)=><div key={n} className="h-10 rounded bg-muted motion-safe:animate-pulse"/>)}</div></div>:error?<p role="alert" className="rounded border p-4 text-sm">{t('Equity metadata could not be loaded.')} <button onClick={refresh} className="text-primary underline">{t('Retry')}</button></p>:data&&<>
        {data.status!=='healthy'&&<p role="status" className="mb-3 text-xs text-muted-foreground">{t(data.total_universe?'Showing cached metadata; the latest refresh is unavailable or stale.':'Equity metadata has not been acquired yet.')}</p>}
        {!data.items.length?<p role="status" className="rounded border p-5 text-sm text-muted-foreground">{t('No matching equities in the cached universe.')}</p>:<div className="panel divide-y">{data.items.map(stock=><Link key={stock.symbol} onClick={()=>remember(stock.symbol)} href={'/stocks/'+encodeURIComponent(stock.symbol)} className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-2 px-4 py-3 hover:bg-muted sm:grid-cols-[4rem_minmax(0,1fr)_auto_1rem]" aria-label={t('Research {ticker}',{ticker:stock.symbol})}>
          <div className="min-w-0"><strong className="text-sm">{stock.symbol}</strong><p className="mt-1 text-[10px] text-muted-foreground">{stock.exchange}</p></div>
          <span className="order-3 col-span-2 min-w-0 truncate text-xs text-muted-foreground sm:order-none sm:col-span-1">{(language==='vi'?stock.company_name:null)||englishCompanyName(stock)||stock.symbol}</span>
          <div className="text-right"><LivePrice symbol={stock.symbol}/></div><ArrowUpRight size={14} className="hidden self-center text-muted-foreground sm:block"/>
        </Link>)}</div>}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground"><span role="status" aria-live="polite">{count===undefined?t('Universe count unavailable'):t('{from}–{to} of {total} results',{from:data.total?data.offset+1:0,to:Math.min(data.offset+data.items.length,data.total),total:number(data.total,0)})}</span><nav aria-label={t('Stock pages')} className="flex gap-2"><Button variant="outline" disabled={!page} onClick={()=>setPage(value=>value-1)}>{t('Previous')}</Button><Button variant="outline" disabled={data.offset+data.items.length>=data.total} onClick={()=>setPage(value=>value+1)}>{t('Next')}</Button></nav></div>
      </>}
    </section>
  </LivePrices>;
}
