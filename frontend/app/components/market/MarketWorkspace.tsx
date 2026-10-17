"use client";
import {useEffect,useState} from 'react';
import {useLocale} from '@/lib/i18n';
import {useEquityPage} from '@/lib/useEquityPage';
import {boardPageSize,boardDefaultGroup,type BoardSort} from '@/lib/quoteMap';
import {useRecentSearches} from '../stock/useRecentSearches';
import {LivePrices} from '../stock/LivePrice';
import QuoteMap from '../stock/QuoteMap';
import {useMarketSearch} from './MarketSearch';
import WorkspaceNav,{workspaceView,type WorkspaceView} from './WorkspaceNav';
import MarketContext from './MarketContext';
import MarketOverview from './MarketOverview';
import FutureData from './FutureData';

export default function MarketWorkspace(){
  const {t,date,number}=useLocale(),{query}=useMarketSearch(),{remember}=useRecentSearches();
  const [view,setView]=useState<WorkspaceView>('overview');
  const [exchange,setExchange]=useState(''),[group,setGroup]=useState<string>(boardDefaultGroup),[page,setPage]=useState(0);
  const [sorting,setSorting]=useState<BoardSort>('change'),[organization,setOrganization]=useState<'ordinary'|'movement'>('ordinary');
  const effectiveGroup=query?'':group;
  const result=useEquityPage({query,exchange,group:effectiveGroup,page,size:boardPageSize},true,query?200:0);
  const data=result.data;
  useEffect(()=>{const sync=()=>setView(workspaceView(window.location.hash));sync();window.addEventListener('hashchange',sync);return()=>window.removeEventListener('hashchange',sync);},[]);
  useEffect(()=>{setPage(0);},[query]);
  const filters=<><label>{t('Index group')}<select aria-label={t('Index group')} value={effectiveGroup} disabled={!!query} onChange={e=>{setGroup(e.target.value);setPage(0);}}><option value="">{t('All equities')}</option>{['VN30','VN100','HNX30'].map(code=><option key={code} value={code} disabled={!data?.index_groups?.groups[code]?.length}>{code}{!data?.index_groups?.groups[code]?.length?' '+t('(unavailable)'):''}</option>)}</select></label><label>{t('Exchange')}<select aria-label={t('Exchange')} value={exchange} onChange={e=>{setExchange(e.target.value);setPage(0);}}><option value="">{t('All exchanges')}</option>{['HOSE','HNX','UPCOM'].map(code=><option key={code}>{code}</option>)}</select></label></>;
  return <div className="market-workspace"><WorkspaceNav view={view}/><MarketContext/><div className="market-title"><h1>{t(view==='overview'?'Market overview':view==='board'?'Market board':'Stock heatmap')}</h1><span>{t('Market workspace')}</span></div>
    {query&&<p className="market-metadata">{t('Search results')} · {query} · {t('All equities')}</p>}
    {result.loading?<section className="quote-panel market-loading" aria-busy="true" role="status"><p>{t('Loading equities…')}</p><div aria-hidden="true" className="h-40 motion-safe:animate-pulse bg-muted"/></section>:result.error?<section className="quote-panel quote-warning" role="alert">{t('Equity metadata could not be loaded.')} <button onClick={result.refresh}>{t('Retry')}</button></section>:data&&<>
      <LivePrices symbols={data.items.map(stock=>stock.symbol)} interval={30000}>
        <p className="market-metadata">{effectiveGroup?effectiveGroup+' '+t('membership'):t('Loaded results')} · {effectiveGroup?data.index_groups?.source:data.items[0]?.source||t('SSI metadata')}{(effectiveGroup?data.index_groups?.last_synced_at:data.last_synced_at)?' · '+date(effectiveGroup?data.index_groups?.last_synced_at:data.last_synced_at,true):''}{data.status!=='healthy'||(effectiveGroup&&data.index_groups?.status!=='healthy')?' · '+t('cached / incomplete coverage'):''}</p>
        {view==='overview'&&(data.items.length?<MarketOverview stocks={data.items} scopeLabel={effectiveGroup||t('Loaded results')} controls={filters}/>:<><div className="quote-toolbar">{filters}</div><p role="status" className="quote-panel quote-empty">{t('No matching equities in the cached universe.')}</p></>)}
        <div hidden={view==='overview'}>{data.items.length?<QuoteMap stocks={data.items} scope="page" scopeLabel={effectiveGroup||t('Loaded results')} mode={view==='heatmap'?'heatmap':'board'} onSelect={remember} controls={filters} sorting={sorting} onSortingChange={setSorting} organization={organization} onOrganizationChange={setOrganization}/>:<><div className="quote-toolbar">{filters}</div><p role="status" className="quote-panel quote-empty">{t('No matching equities in the cached universe.')}</p></>}
          <div className="market-pagination"><span role="status">{t('{from}–{to} of {total} results',{from:data.total?data.offset+1:0,to:Math.min(data.offset+data.items.length,data.total),total:number(data.total,0)})}</span><nav aria-label={t('Stock pages')}><button disabled={!page} onClick={()=>setPage(n=>n-1)}>{t('Previous')}</button><button disabled={data.offset+data.items.length>=data.total} onClick={()=>setPage(n=>n+1)}>{t('Next')}</button></nav></div><FutureData/>
        </div>
      </LivePrices>
    </>}
  </div>;
}
