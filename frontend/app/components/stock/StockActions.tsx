"use client";
import {useLocale} from '@/lib/i18n';
import {actionStatus,actionUrl,trustedAction,type ActionPage,type ActionObservation} from '@/lib/stock-detail';
import {useStockRead} from './useStockRead';
import {Button} from '../ui/button';

const labels={cash_dividend:'Cash dividend',stock_dividend:'Stock dividend',bonus_shares:'Bonus shares',rights_offering:'Rights offering',additional_issuance:'Additional issuance',other:'Other corporate action'} as const;
function SourceEvidence({row}:{row:ActionObservation}) {
  const {t,date}=useLocale();
  const urls=[...new Set([row.source_url,...row.supporting_urls].map(actionUrl).filter((url):url is string=>!!url))];
  return <details className="stock-action-evidence"><summary>{t('Source observation')} · {date(row.observed_at,true)} · {row.source}</summary>
    <div className="space-y-2 pt-3 text-xs text-muted-foreground">
      {row.source_title&&<p className="font-medium text-foreground">{row.source_title}</p>}
      {row.evidence_text&&<p className="whitespace-pre-wrap">{row.evidence_text}</p>}
      {row.verification_note&&<p>{row.verification_note}</p>}
      <p>{t('Observed at')} {date(row.observed_at,true)} · {t('Source revision')} {row.source_revision||'—'}</p>
      {row.source_updated_at&&<p>{t('Source updated at')} {date(row.source_updated_at,true)}</p>}
      <p>{t('Announcement date')} {date(row.announced_at||row.announced_on,!!row.announced_at)}</p>
      {urls.length?urls.map((url,index)=><a key={url} className="mr-4 inline-block text-primary underline" href={url} target="_blank" rel="noopener noreferrer">{t(index?'Supporting document':'Original source document')}{index?' '+index:''} ↗</a>):<p>{t('Original document unavailable')}</p>}
    </div>
  </details>;
}
export default function StockActions({ticker}:{ticker:string}) {
  const {t,ui,date,number}=useLocale();
  const status=(row:ActionObservation)=>[ui(actionStatus(row)),...(row.is_fixture&&actionStatus(row)!=='Fixture observation'?[t('Fixture observation')]:[])].join(' · ');
  const {data,error,retry}=useStockRead<ActionPage>(`/api/stocks/${encodeURIComponent(ticker)}/corporate-actions?limit=50`);
  return <section className="panel p-4 sm:p-5" aria-label={t('Dividends & corporate actions')}>
    <div className="stock-action-heading"><div><p className="stock-eyebrow">VSDC · {t('Source records')}</p><h2>{t('Dividends & corporate actions')}</h2></div><span className="stock-badge">{t('Incomplete coverage')}</span></div>
    <p className="stock-note">{t('Only recorded source observations are shown. Missing dates stay unavailable; absence does not establish that no corporate action occurred.')}</p>
    {error?<p role="alert">{t('Corporate-action records are temporarily unavailable.')} <Button variant="outline" onClick={retry}>{t('Retry')}</Button></p>:!data?<p role="status">{t('Loading source records…')}</p>:data.ticker!==ticker?<p role="alert">{t('Corporate-action records are temporarily unavailable.')}</p>:!data.items.length?<div className="stock-empty"><h3>{t('No recorded corporate actions for {ticker}',{ticker})}</h3><p>{t('Coverage is incomplete. No dividend dates or ratios are inferred.')}</p></div>:<>
      <div className="table-scroll stock-action-table" tabIndex={0} role="region" aria-label={t('Corporate-action dates and terms')}><table><thead><tr>{['Event type','Ex-rights date','Record date','Payment date','Cash per share','New shares / old share','Subscription price','Verification'].map(label=><th key={label} scope="col">{ui(label)}</th>)}</tr></thead><tbody>{data.items.map(row=>{
        const trusted=trustedAction(row);
        return <tr key={row.observation_id}><th scope="row">{ui(labels[row.action_type])}</th><td>{trusted?date(row.effective_date):'—'}</td><td>{trusted?date(row.record_date):'—'}</td><td>{trusted?date(row.payment_date):'—'}</td><td>{trusted&&row.terms?.cash_vnd_per_share!=null?number(row.terms.cash_vnd_per_share)+' VND':'—'}</td><td>{trusted&&row.terms?.new_shares_per_old!=null?number(row.terms.new_shares_per_old,6)+' / 1':'—'}</td><td>{trusted&&row.terms?.subscription_price_vnd!=null?number(row.terms.subscription_price_vnd)+' VND':'—'}</td><td>{status(row)}</td></tr>;
      })}</tbody></table></div>
      <div className="stock-action-timeline mt-4 space-y-3" role="list" aria-label={t('Source observation timeline')}>{data.items.map(row=><div role="listitem" key={row.observation_id}><p className="mb-1 text-xs font-medium">{ui(labels[row.action_type])} · {status(row)}</p><SourceEvidence row={row}/></div>)}</div>
      {data.has_more&&<p className="stock-note">{t('Showing the latest 50 observations; older records are not included.')}</p>}
    </>}
    {data&&<p className="stock-note">{t('Read at')} {date(data.as_of,true)} · {t('Stored evidence; no acquisition triggered.')}</p>}
  </section>;
}
