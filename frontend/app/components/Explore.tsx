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
import StockNews from './stock/StockNews';
import StockCommunity from './stock/StockCommunity';
import StockActions from './stock/StockActions';
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
  const {t,language,date}=useLocale();
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
  const name=security&&(language==='en'?security.display_name_en||security.company_name:security.company_name);
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
      <div className="stock-chart-layout" hidden={tab!=='overview'&&tab!=='technical'}>
        <div className="stock-chart-main" role="tabpanel" id="stock-panel-price" aria-labelledby={`stock-tab-${tab==='technical'?'technical':'overview'}`} tabIndex={0}>
          {tab==='technical'&&<><p className="stock-note">{t('Chart indicators describe completed observations. Accepted Technical evidence has separate assurance; no trading recommendation.')}</p><TechnicalInsights ticker={ticker}/></>}
          {(visited.has('overview')||visited.has('technical'))&&<TechnicalChart ticker={ticker} priceOnly={tab!=='technical'} onRows={setTechnicalRows}/>}
          {tab==='technical'&&<RawDataTable bars={technicalRows}/>}
        </div>
        <aside className="stock-research-sidebar" hidden={tab!=='overview'} aria-label={t('Company overview')}>
          <section className="panel p-5"><p className="stock-eyebrow">{t('Company profile')}</p><h2 className="mt-2">{name||ticker}</h2><dl className="stock-profile"><div><dt>{t('Ticker')}</dt><dd>{ticker}</dd></div><div><dt>{t('Exchange')}</dt><dd>{security.exchange}</dd></div><div><dt>{t('Instrument')}</dt><dd>{t('Listed equity')}</dd></div></dl><p className="stock-note">{t('Metadata source')} · {security.source||t('Unavailable')} · {date(identity.data?.last_synced_at,true)}</p><p className="stock-note">{t('Business description, ownership and valuation data are not available in this dataset.')}</p></section>
          {visited.has('overview')&&<DailyContext ticker={ticker}/>}
        </aside>
      </div>
      <div role="tabpanel" id="stock-panel-fundamentals" aria-labelledby="stock-tab-fundamentals" tabIndex={0} hidden={tab!=='fundamentals'}>{visited.has('fundamentals')&&<FundamentalTrends ticker={ticker} visible={tab==='fundamentals'}/>}</div>
      <div role="tabpanel" id="stock-panel-actions" aria-labelledby="stock-tab-actions" tabIndex={0} hidden={tab!=='actions'}>{visited.has('actions')&&<StockActions ticker={ticker}/>}</div>
      <div role="tabpanel" id="stock-panel-news" aria-labelledby="stock-tab-news" tabIndex={0} hidden={tab!=='news'}>{tab==='news'&&<div className="page-stack"><StockNews ticker={ticker}/><StockCommunity ticker={ticker}/></div>}</div>
      {tab==='overview'&&<StockNews ticker={ticker} preview/>}
    </>}
  </div>;
}
