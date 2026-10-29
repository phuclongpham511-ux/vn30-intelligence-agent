"use client";
import {useState} from 'react';
import {useLocale} from '@/lib/i18n';
import {actionConflict,actionStatus,actionUrl,trustedAction,actionDetailsIncomplete,actionDate,actionTerm,actionHistory,type ActionCategory,type ActionPage,type ActionObservation} from '@/lib/stock-detail';
import {useStockRead} from './useStockRead';
import {Button} from '../ui/button';

const labels={cash_dividend:'Cash dividend',stock_dividend:'Stock dividend',bonus_shares:'Bonus shares',rights_offering:'Rights offering',additional_issuance:'Additional issuance',other:'Other corporate action'} as const;
function SourceEvidence({row}:{row:ActionObservation}) {
  const {t,date}=useLocale();
  const urls=[...new Set([row.source_url,...row.supporting_urls].map(actionUrl).filter((url):url is string=>!!url))];
  return <details className="stock-action-evidence"><summary>{t('Source observation')} · <time dateTime={row.observed_at}>{date(row.observed_at,true)}</time> ICT · {row.source}</summary>
    <div className="space-y-2 pt-3 text-xs text-muted-foreground">
      {row.source_title&&<p className="font-medium text-foreground">{row.source_title}</p>}
      {row.evidence_text&&<p className="whitespace-pre-wrap">{row.evidence_text}</p>}
      {row.verification_note&&<p>{row.verification_note}</p>}
      <p>{t('Observed at')} <time dateTime={row.observed_at}>{date(row.observed_at,true)}</time> ICT · {t('Source revision')} {row.source_revision||'—'}</p>
      {row.source_updated_at&&<p>{t('Source updated at')} <time dateTime={row.source_updated_at}>{date(row.source_updated_at,true)}</time> ICT</p>}
      <p>{t('Recorded announcement / publication date')} {date(row.announced_at||row.announced_on,!!row.announced_at)}</p>
      {urls.length?urls.map((url,index)=><a key={url} className="mr-4 inline-block text-primary underline" href={url} target="_blank" rel="noopener noreferrer">{t(index?'Supporting document':'Recorded source link')}{index?' '+index:''} ↗</a>):<p>{t('Source link unavailable')}</p>}
    </div>
  </details>;
}
export function StockActionsView({ticker,data,error=false,retry,category}:{ticker:string;data:ActionPage|null;error?:boolean;retry:()=>void;category?:ActionCategory}) {
  const {t,ui,date,number}=useLocale();
  const [selection,setSelection]=useState<ActionCategory>('all');
  const selected=category??selection;
  const status=(row:ActionObservation)=>[ui(actionStatus(row)),...(row.is_fixture&&actionStatus(row)!=='Fixture observation'?[t('Fixture observation')]:[])].join(' · ');
  const matches=!!data&&data.ticker===ticker&&Array.isArray(data.items)&&data.items.every(row=>row.symbol===ticker);
  const rows=matches?actionHistory(data.items,selected):[];
  const amount=(value:number)=>value!==0&&value<1e-20?String(value):number(value,20);
  const terms=(row:ActionObservation)=>{
    const cash=actionTerm(row,'cash_vnd_per_share'),shares=actionTerm(row,'new_shares_per_old'),subscription=actionTerm(row,'subscription_price_vnd');
    return <dl className="action-terms">{row.action_type==='cash_dividend'&&<div><dt>{t('Cash per share')}</dt><dd>{cash===null?'—':amount(cash)+' VND'}</dd></div>}{['stock_dividend','bonus_shares','rights_offering','additional_issuance'].includes(row.action_type)&&<div><dt>{t('New shares / old share')}</dt><dd>{shares===null?'—':amount(shares)+' / 1'}</dd></div>}{['rights_offering','additional_issuance'].includes(row.action_type)&&<div><dt>{t('Subscription price')}</dt><dd>{subscription===null?'—':amount(subscription)+' VND'}</dd></div>}</dl>;
  };
  return <section className="panel p-4 sm:p-5" aria-label={t('Dividends & corporate actions')}>
    <div className="stock-action-heading"><div><p className="stock-eyebrow">{t('Stored source records')}</p><h2>{t('Dividends & corporate actions')}</h2></div><span className="stock-badge">{t('Incomplete coverage')}</span></div>
    <p className="stock-note">{t('Only recorded source observations are shown. Missing dates stay unavailable; absence does not establish that no corporate action occurred.')}</p>
    <details className="action-entitlement-guide"><summary>{t('Understanding your entitlements')}</summary><dl>
      <div><dt>{t('Ex-rights date')}</dt><dd>{t('Eligibility follows the official notice and settlement rules. The record date cannot establish a missing ex-rights date.')}</dd></div>
      <div><dt>{t('Record date')}</dt><dd>{t('Date used to establish the shareholder list in the notice; not the payment date.')}</dd></div>
      <div><dt>{t('Announced payment date')}</dt><dd>{t('The announced schedule may change. Payment completion is not verified.')}</dd></div>
      <div><dt>{t('Cash per share')}</dt><dd>{t('Source-declared amount per share; not your net receipt. Taxes, holdings and eligibility are not calculated.')}</dd></div>
      <div><dt>{t('New shares / old share')}</dt><dd>{t('Source-declared share ratio; not confirmation that shares have been credited or can be traded.')}</dd></div>
    </dl></details>
    {error?<p role="alert">{t('Corporate-action records are temporarily unavailable.')} <Button variant="outline" onClick={retry}>{t('Retry')}</Button></p>:!data?<p role="status">{t('Loading source records…')}</p>:!matches?<p role="alert">{t('Corporate-action records are temporarily unavailable.')}</p>:!data.items.length?<div className="stock-empty"><h3>{t('No recorded corporate actions for {ticker}',{ticker})}</h3><p>{t('Coverage is incomplete. No dividend dates or ratios are inferred.')}</p></div>:<>
      <div className="action-history-toolbar"><label>{t('Recorded history')}<select aria-label={t('Action history filter')} value={selected} onChange={event=>setSelection(event.target.value as ActionCategory)}><option value="all">{t('All records')}</option><option value="distributions">{t('Dividends & bonus shares')}</option><option value="other">{t('Rights & other actions')}</option></select></label><span role="status">{t('{shown} of {total} recorded observations',{shown:rows.length,total:data.items.length})}</span></div>
      <p className="stock-note action-history-note">{t('Latest source observations first. A payment date does not confirm payment.')}</p>
      <p className="stock-note">{t('Record-level verification does not establish original-publication verification of every fact. Source links may be secondary references.')}</p>
      {rows.length?<ol className="action-history" aria-label={t('Corporate-action dates and terms')}>{rows.map(row=><li key={row.observation_id} data-action-observation={row.observation_id}>
        <article className="action-record"><div className="action-record-heading"><div><h3>{ui(labels[row.action_type])}</h3><p>{row.source}</p></div><div className="action-record-status"><span className="stock-badge" data-action-status={trustedAction(row)?'source-verified':'unqualified'}>{status(row)}</span>{trustedAction(row)&&actionDetailsIncomplete(row)&&<span className="stock-badge">{t('Incomplete event details')}</span>}{row.is_fixture&&<strong className="action-demo">DEMO · {t('Synthetic source fixture')}</strong>}</div></div>
          <p className="action-announcement">{t('Recorded announcement / publication date')}: {date(row.announced_at||row.announced_on,!!row.announced_at)}</p>
          {row.withdrawn?<p className="action-revision-warning">{t('This notice was withdrawn; do not use it to establish an entitlement.')}</p>:actionConflict(row)?<p className="action-revision-warning">{t('A correction remains unresolved; dates and terms are withheld.')}</p>:null}
          {terms(row)}
          {!trustedAction(row)&&<p className="action-unqualified">{t('Event dates and terms are withheld until source verification; DEMO fixtures never become confirmed records.')}</p>}
          <dl className="action-dates">{(['effective_date','record_date','payment_date'] as const).map((key,index)=><div key={key}><dt>{t(index===0?'Ex-rights date':index===1?'Record date':'Announced payment date')}</dt><dd>{date(actionDate(row,key))}</dd></div>)}</dl>
          {row.action_type==='cash_dividend'&&<p className="stock-note">{t('Payment completion is not verified.')}</p>}
          <details className="action-version" data-action-version><summary>{t('Latest stored version')}</summary><p>{t('Earlier revisions are not included in this view.')}</p><dl><div><dt>{t('Source revision')}</dt><dd>{row.source_revision||'—'}</dd></div><div><dt>{t('Source observation')}</dt><dd>{row.observation_id}</dd></div></dl><p>{t('A revision identifier does not establish which terms changed. Check the source notice.')}</p></details>
          <SourceEvidence row={row}/>
        </article>
      </li>)}</ol>:<p className="stock-note" role="status">{t('No recorded observations in this category.')}</p>}
      {data.has_more&&<p className="stock-note">{t('Showing the latest 50 observations; older records are not included.')}</p>}
    </>}
    {matches&&<p className="stock-note">{t('Read at')} <time dateTime={data.as_of}>{date(data.as_of,true)}</time> ICT · {t('Stored evidence; no acquisition triggered.')}</p>}
  </section>;
}
export default function StockActions({ticker}:{ticker:string}) {
  const state=useStockRead<ActionPage>(`/api/stocks/${encodeURIComponent(ticker)}/corporate-actions?limit=50`);
  return <StockActionsView ticker={ticker} {...state}/>;
}
