"use client";
import Link from 'next/link';
import type {ReactNode} from 'react';
import {useLocale} from '@/lib/i18n';
import {sampleObservations,type BoardIdentity,type BoardRow} from '@/lib/quoteMap';
import {useLivePrices} from '../stock/LivePrice';
import MarketNewsContext from '../news/MarketNewsContext';
import FutureData from './FutureData';
import {resolvePriceState,priceStateClass} from '@/lib/priceState';
export default function MarketOverview({stocks,scopeLabel,controls,showObservations=true}:{stocks:BoardIdentity[];scopeLabel:string;controls?:ReactNode;showObservations?:boolean}){
  const {t,number,date,ui}=useLocale(),{data,failed}=useLivePrices();
  const sample=sampleObservations(stocks,data,failed),{groups,comparable}=sample;
  const session=ui(data?.session==='active'?'Active trading session':data?.session==='break'?'Midday break':data?.session==='closed'?'Market closed':'Session unconfirmed');
  const table=(entries:BoardRow[],heading:'Largest advances'|'Largest declines')=><section className="quote-panel market-movers"><div className="market-panel-heading"><h2>{t(heading)}</h2><span>{t('Comparable observations')}</span></div>{entries.length?<table className="quote-table"><thead><tr><th>{t('Ticker')}</th><th>{t('Price')} · VND</th><th>Δ %</th><th>{t('Source time')}</th></tr></thead><tbody>{entries.map(row=><tr key={row.stock.symbol} data-observation={row.stock.symbol} className={'quote-movement-row '+priceStateClass(resolvePriceState(row.stock.symbol,row.row,row.status))} data-movement-state={resolvePriceState(row.stock.symbol,row.row,row.status)}><th scope="row"><Link href={'/stocks/'+encodeURIComponent(row.stock.symbol)}>{row.stock.symbol} ↗</Link></th><td>{number(row.row!.last_price)}</td><td className="quote-movement-cell" data-movement-state={resolvePriceState(row.stock.symbol,row.row,row.status)}>{row.row!.change_percent!>0?'+':''}{number(row.row!.change_percent)}%</td><td><time dateTime={row.row!.updated_at} title={row.row!.source+' · '+date(row.row!.updated_at,true)}>{date(row.row!.updated_at,true)}</time></td></tr>)}</tbody></table>:<p className="quote-empty">{t(!data&&!failed?'Loading observed quotes…':failed?'Quote coverage unavailable':!comparable?'Not enough session-aligned observations.':'No stocks in this category')}</p>}</section>;
  return <div className="market-overview market-overview-refined">
    {showObservations&&<section className="market-sample quote-panel"><div className="quote-toolbar"><details className="market-overview-filters"><summary>{t('Change selection')}</summary><div>{controls}</div></details><span className="quote-coverage" role="status"><strong>{scopeLabel}</strong> · {t('Loaded sample')}: {sample.available===null?t(failed?'Quote coverage unavailable':'Loading observed quotes…'):t('{available}/{total} quotes',{available:sample.available,total:stocks.length})}</span></div>
      <div className="market-counts">{(['advancing','unchanged','declining'] as const).map(key=><div key={key}><strong className={key==='advancing'?'positive':key==='declining'?'negative':'unchanged'}>{comparable?groups[key].length:'—'}</strong><span>{t(key==='advancing'?'Up':key==='declining'?'Down':'Unchanged')}</span></div>)}<div><strong>{sample.available===null?'—':sample.stale}</strong><span>{t('Stale')}</span></div><div><strong>{sample.available===null?'—':sample.missing}</strong><span>{t('Missing')}</span></div></div>
      {comparable&&<div className="market-distribution" aria-label={t('Selected-sample movement distribution')}>{(['advancing','unchanged','declining'] as const).map(key=><span key={key} className={'distribution-'+key} style={{flexGrow:groups[key].length}} title={t(key==='advancing'?'Up':key==='declining'?'Down':'Unchanged')+': '+groups[key].length}/>)}</div>}
      <p className="market-selection-note">{comparable?t('{count} comparable of {total} loaded',{count:sample.compared,total:stocks.length}):t('Not enough session-aligned observations.')} · {t('Not whole-market breadth.')}<br/>{session}{data&&<> · <time dateTime={data.as_of}>{date(data.as_of,true)}</time> · ICT</>}</p>
    </section>}
    <MarketNewsContext/>
    {showObservations&&<><div className="market-mover-grid">{table(sample.gainers,'Largest advances')}{table(sample.decliners,'Largest declines')}</div>
    <nav className="market-next market-next-inline" aria-label={t('Continue research')}><a href="/#market-board">{t('Compare prices')} ↗</a><a href="/#market-heatmap">{t('See movements')} ↗</a><span>{t('Open any ticker to inspect company research and original evidence.')}</span></nav>
    <FutureData/></>}
  </div>;
}
