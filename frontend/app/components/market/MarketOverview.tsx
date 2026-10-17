"use client";
import Link from 'next/link';
import {useLocale} from '@/lib/i18n';
import {boardRows,movementGroups,type BoardIdentity} from '@/lib/quoteMap';
import {useLivePrices} from '../stock/LivePrice';
import MarketFocus from '../news/MarketFocus';
import FutureData from './FutureData';
export default function MarketOverview({stocks}:{stocks:BoardIdentity[]}){
  const {t,number,date}=useLocale();const {data,failed}=useLivePrices();
  const rows=boardRows(stocks,data,failed),groups=movementGroups(rows),known=!!data&&!failed;
  const selected=[...groups.advancing.slice(0,4),...groups.declining.slice(-3)];
  return <div className="market-overview"><div className="market-stack"><section className="quote-panel"><div className="market-panel-heading"><h2>{t('What moved in this selection?')}</h2><a href="/#market-board">{t('Compare stocks')} ↗</a></div><div className="market-counts">{(['advancing','unchanged','declining','unqualified'] as const).map(key=><div key={key}><strong className={key==='advancing'?'positive':key==='declining'?'negative':key==='unchanged'?'unchanged':''}>{known?groups[key].length:'—'}</strong><span>{t(key==='advancing'?'Up':key==='declining'?'Down':key==='unchanged'?'Unchanged':'Stale / Missing')}</span></div>)}</div><p className="market-selection-note">{t('Current observations in this selection only')} · {stocks.length} {t('stocks')}. {t('Not whole-market breadth.')}</p>
    {!data?<p className="quote-empty" role={failed?'alert':'status'}>{t(failed?'Quote coverage unavailable':'Loading observed quotes…')}</p>:selected.length?<table className="quote-table"><thead><tr><th>{t('Ticker')}</th><th>{t('Price')} · VND</th><th>Δ %</th><th>{t('Source time')}</th></tr></thead><tbody>{selected.map(row=><tr key={row.stock.symbol}><th scope="row"><Link href={'/stocks/'+encodeURIComponent(row.stock.symbol)}>{row.stock.symbol} ↗</Link></th><td>{number(row.row?.last_price)}</td><td className={row.row!.change_percent!>0?'positive':'negative'}>{row.row!.change_percent!>0?'+':''}{number(row.row?.change_percent)}%</td><td><time dateTime={row.row!.updated_at}>{date(row.row!.updated_at,true)}</time></td></tr>)}</tbody></table>:<p className="quote-empty">{t('No current directional observations. Inspect the board for stale, missing or unchanged quotes.')}</p>}</section><FutureData/></div>
    <div className="market-stack"><section className="quote-panel"><div className="market-panel-heading"><h2>{t('Choose your next question')}</h2></div><div className="market-next"><a href="/#market-board">{t('Compare prices')} ↗</a><a href="/#market-heatmap">{t('See movements')} ↗</a></div><p className="market-selection-note">{t('Open any ticker to inspect company research and original evidence.')}</p></section><MarketFocus/><Link className="market-news-link" href="/news">{t('All news ↗')}</Link></div>
  </div>;
}
