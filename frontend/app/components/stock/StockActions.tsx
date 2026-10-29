"use client";
import {useState} from 'react';
import {useLocale} from '@/lib/i18n';
import {actionConflict,trustedAction,actionDetailsIncomplete,actionDate,actionTerm,actionHistory,type ActionCategory,type ActionPage,type ActionObservation} from '@/lib/stock-detail';
import {useStockRead} from './useStockRead';
import {Button} from '../ui/button';
const labels={cash_dividend:'Cash dividend',stock_dividend:'Stock dividend',bonus_shares:'Bonus shares',rights_offering:'Rights offering',additional_issuance:'Additional issuance',other:'Other corporate action'} as const;
export function StockActionsView({ticker,data,error=false,retry,category,compact=false,allowPersonal=false}:{ticker:string;data:ActionPage|null;error?:boolean;retry:()=>void;category?:ActionCategory;compact?:boolean;allowPersonal?:boolean}) {
  const {t,ui,date,number}=useLocale();
  const [selection,setSelection]=useState<ActionCategory>('all');
  const selected=category??selection;
  const matches=!!data&&data.ticker===ticker&&Array.isArray(data.items)&&data.items.every(row=>row.symbol===ticker)&&(data.display_scope!=='personal_research'||allowPersonal&&data.public_display_eligible===false);
  const rows=matches?actionHistory(data.items,selected):[];
  const amount=(value:number)=>value!==0&&value<1e-20?String(value):number(value,20);
  const terms=(row:ActionObservation)=>{
    const cash=actionTerm(row,'cash_vnd_per_share'),shares=actionTerm(row,'new_shares_per_old'),subscription=actionTerm(row,'subscription_price_vnd');
    return <dl className="action-terms">{row.action_type==='cash_dividend'&&<div><dt>{t('Cash per share')}</dt><dd>{cash===null?'—':amount(cash)+' VND'}</dd></div>}{['stock_dividend','bonus_shares','rights_offering','additional_issuance'].includes(row.action_type)&&<div><dt>{t('New shares / old share')}</dt><dd>{shares===null?'—':amount(shares)+' / 1'}</dd></div>}{['rights_offering','additional_issuance'].includes(row.action_type)&&<div><dt>{t('Subscription price')}</dt><dd>{subscription===null?'—':amount(subscription)+' VND'}</dd></div>}</dl>;
  };
  return <div className={compact?'min-w-0':'panel p-4 sm:p-5'} aria-label={compact?undefined:t('Dividends & corporate actions')}>
    {!compact&&<div className="stock-action-heading"><h2>{t('Dividends & corporate actions')}</h2></div>}
    {!compact&&<details className="action-entitlement-guide"><summary>{t('Understanding your entitlements')}</summary>
      <p className="stock-note">{t('Cash amounts are per share, before taxes. Your entitlement depends on your holdings and eligibility.')}</p>
      <p className="stock-note">{t('Missing ex-dates are not inferred from record dates.')}</p>
      <p className="stock-note">{t('Payment dates are announced schedules, not confirmation of payment or shares credited.')}</p>
    </details>}
    {error||data&&!matches?<p role="alert">{t('Events are temporarily unavailable.')} <Button variant="outline" onClick={retry}>{t('Retry')}</Button></p>:!data?<p role="status">{t('Loading events…')}</p>:!data.items.length?<div className="stock-empty"><h3>{t('No event information for {ticker}',{ticker})}</h3><p>{t('No information does not mean no entitlement.')}</p></div>:<>
      <div className="action-history-toolbar"><label>{t('Event type')}<select aria-label={t('Filter events')} value={selected} onChange={event=>setSelection(event.target.value as ActionCategory)}><option value="all">{t('All events')}</option><option value="distributions">{t('Dividends & bonus shares')}</option><option value="other">{t('Rights & other actions')}</option></select></label></div>
      {rows.length?<ol className="action-history" aria-label={t('Corporate-action dates and terms')}>{rows.map(row=><li key={row.observation_id}>
        <article className="action-record"><div className="action-record-heading"><h3>{ui(labels[row.action_type])}</h3><div className="action-record-status">
          {row.withdrawn?<span className="stock-badge">{t('Cancelled')}</span>:actionConflict(row)?<span className="stock-badge">{t('Under revision')}</span>:(!trustedAction(row)||actionDetailsIncomplete(row))&&<span className="stock-badge">{t('Incomplete event details')}</span>}
          {row.is_fixture&&<strong className="action-demo">DEMO</strong>}
        </div></div>
          {terms(row)}
          {!trustedAction(row)&&<p className="action-unqualified">{t(row.withdrawn?'This event was cancelled; do not rely on these terms.':actionConflict(row)?'Dates and terms are being clarified.':'Dates and terms are not yet available.')}</p>}
          <dl className="action-dates">{(['effective_date','record_date','payment_date'] as const).map((key,index)=><div key={key}><dt>{t(index===0?'Ex-rights date':index===1?'Record date':'Announced payment date')}</dt><dd>{date(actionDate(row,key))}</dd></div>)}</dl>
        </article>
      </li>)}</ol>:<p className="stock-note" role="status">{t('No events in this category.')}</p>}
      {data.has_more&&<p className="stock-note">{t('Showing up to 50 events.')}</p>}
    </>}
  </div>;
}
export default function StockActions({ticker,compact=false}:{ticker:string;compact?:boolean}) {
  const state=useStockRead<ActionPage>(`/api/stocks/${encodeURIComponent(ticker)}/corporate-actions?limit=50`);
  return <StockActionsView ticker={ticker} {...state} compact={compact}/>;
}
