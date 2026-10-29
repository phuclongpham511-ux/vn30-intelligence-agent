"use client";
import {useEffect,useRef,useState} from 'react';
import {useLocale} from '@/lib/i18n';
import {stockSection,stockSections,stockIdentity,type StockSection} from '@/lib/stock-detail';
import type {Security,Market,TechnicalBar} from '@/lib/types';
import StockHeader from './stock/StockHeader';
import TechnicalChart from './stock/TechnicalChart';
import MarketSnapshot from './stock/MarketSnapshot';
import FundamentalTrends from './stock/FundamentalTrends';
import TechnicalInsights from './stock/TechnicalInsights';
import RawDataTable from './stock/RawDataTable';
import StockIntelligence from './stock/StockIntelligence';
import StockActions from './stock/StockActions';
import CompanyOverview from './stock/CompanyOverview';
import {useStockRead} from './stock/useStockRead';
import {StockError} from './stock/StockStates';
import {Skeleton} from './ui/skeleton';
import {Button} from './ui/button';
import WorkspaceNav from './market/WorkspaceNav';

const labels={overview:'Overview',fundamentals:'Fundamental analysis',technical:'Technical analysis',actions:'Dividends & corporate actions',news:'Company news'} as const;

function DailyContext({ticker}:{ticker:string}) {
  const {t}=useLocale();
  const {data,error,retry}=useStockRead<Market>(`/api/stocks/${encodeURIComponent(ticker)}/market`);
  return data&&data.ticker===ticker?<MarketSnapshot market={data} compact/>:<section className="panel p-5"><h2>{t('Market context')}</h2>{error?<p className="stock-note" role="alert">{t('Daily analytics unavailable. The latest quote is shown separately.')} <Button size="sm" variant="outline" onClick={retry}>{t('Retry')}</Button></p>:<Skeleton className="mt-4 h-40"/>}</section>;
}

export default function Explore({ticker}:{ticker:string}) {
  const {t}=useLocale();
  const identity=useStockRead<{items:Security[];last_synced_at:string|null}>(`/api/stocks/universe?symbols=${encodeURIComponent(ticker)}&limit=1`);
  let security:Security|null=null;
  try {if(identity.data)security=stockIdentity(identity.data.items,ticker);}catch{/* No unsupported identity fallback. */}
  const [tab,setTab]=useState<StockSection>('overview');
  const [visited,setVisited]=useState<Set<StockSection>>(()=>new Set());
  const [technicalRows,setTechnicalRows]=useState<TechnicalBar[]>([]);
  const buttons=useRef<Partial<Record<StockSection,HTMLButtonElement|null>>>({});
  const select=(next:StockSection)=>{setTab(next);setVisited(current=>new Set([...current,next]));};
  useEffect(()=>{
    const restore=()=>{const next=stockSection(window.location.hash);setTab(next);setVisited(current=>new Set([...current,next]));};
    restore();window.addEventListener('hashchange',restore);window.addEventListener('popstate',restore);
    return()=>{window.removeEventListener('hashchange',restore);window.removeEventListener('popstate',restore);};
  },[]);
  const navigate=(next:StockSection)=>{select(next);window.history.pushState(null,'',`#stock-${next}`);};
  if(identity.error||(identity.data&&!security))return <StockError ticker={ticker} message="Stock identity unavailable. Find an available listed equity in Explore." retry={identity.retry}/>;
  return <div className="page-stack stock-detail">
    <WorkspaceNav research/>
    <StockHeader available={!!security} stock={{symbol:ticker,company_name:security?.company_name||null,display_name_en:security?.display_name_en,exchange:security?.exchange||null}}/>
    <div className="stock-tabs" role="tablist" aria-label={t('Stock sections')}>
      {stockSections.map((section,index)=><button key={section} ref={node=>{buttons.current[section]=node;}} type="button" role="tab" id={`stock-tab-${section}`} aria-controls={section==='overview'||section==='technical'?'stock-panel-price':`stock-panel-${section}`} aria-selected={tab===section} tabIndex={tab===section?0:-1} onClick={()=>navigate(section)} onKeyDown={event=>{
        const next=event.key==='ArrowRight'?stockSections[(index+1)%stockSections.length]:event.key==='ArrowLeft'?stockSections[(index+stockSections.length-1)%stockSections.length]:event.key==='Home'?stockSections[0]:event.key==='End'?stockSections.at(-1):null;
        if(next){event.preventDefault();navigate(next);buttons.current[next]?.focus();}
      }}>{t(labels[section])}</button>)}
    </div>
    {!security?<div aria-busy="true" role="status"><p className="stock-note">{t('Loading stock identity…')}</p><Skeleton className="h-96"/></div>:<>
      <div role={tab==='fundamentals'?'tabpanel':undefined} id="stock-panel-fundamentals" aria-labelledby={tab==='fundamentals'?'stock-tab-fundamentals':undefined} tabIndex={tab==='fundamentals'?0:undefined} hidden={tab!=='overview'&&tab!=='fundamentals'}>{(visited.has('overview')||visited.has('fundamentals'))&&<FundamentalTrends ticker={ticker} visible={tab==='overview'||tab==='fundamentals'} summary={tab!=='fundamentals'} onOpen={()=>navigate('fundamentals')}/>}</div>
      <div className="stock-chart-layout" hidden={tab!=='overview'&&tab!=='technical'}>
        <div className="stock-chart-main" role="tabpanel" id="stock-panel-price" aria-labelledby={`stock-tab-${tab==='technical'?'technical':'overview'}`} tabIndex={0}>
          {tab==='technical'&&<><p className="stock-note">{t('Chart indicators describe completed observations. Accepted Technical evidence has separate assurance; no trading recommendation.')}</p><TechnicalInsights ticker={ticker}/></>}
          {(visited.has('overview')||visited.has('technical'))&&<TechnicalChart ticker={ticker} priceOnly={tab!=='technical'} onRows={setTechnicalRows}/>}
          {tab==='technical'&&<RawDataTable bars={technicalRows}/>}
        </div>
        <aside className="stock-research-sidebar" hidden={tab!=='overview'} aria-label={t('Company overview')}>
          <CompanyOverview security={security} syncedAt={identity.data?.last_synced_at??null}/>
          {visited.has('overview')&&<DailyContext ticker={ticker}/>}
        </aside>
      </div>
      <div role="tabpanel" id="stock-panel-actions" aria-labelledby="stock-tab-actions" tabIndex={0} hidden={tab!=='actions'}>{visited.has('actions')&&<StockActions ticker={ticker}/>}</div>
      <div role={tab==='news'?'tabpanel':undefined} id="stock-panel-news" aria-labelledby={tab==='news'?'stock-tab-news':undefined} tabIndex={tab==='news'?0:undefined} hidden={tab!=='news'&&tab!=='overview'}>{(visited.has('overview')||visited.has('news'))&&<StockIntelligence key={ticker} ticker={ticker} preview={tab!=='news'}/>}</div>
    </>}
  </div>;
}
