"use client";
import {useLocale} from '@/lib/i18n';
import {isUnread,type AttentionUpdate,type WatchlistState} from '@/lib/watchlist';
import type {FinancialPage,FinancialEvidence} from '@/lib/watchlist-financial';

export default function WatchlistFinancial({page,symbol,state,disabled,review}:{page:FinancialPage;symbol:string;state:WatchlistState;disabled:boolean;review:(items:AttentionUpdate[])=>void}){
 const {t,language}=useLocale();
 const expanded=page.profile==='qualified-v58';
 const metricLabel=(metric:string)=>t(({revenue:'Revenue',net_profit:'Net profit',customer_loans:'Customer loans'} as const)[metric as 'revenue'|'net_profit'|'customer_loans']);
 const number=(n:number)=>new Intl.NumberFormat(language==='vi'?'vi-VN':'en-US',{maximumFractionDigits:20}).format(n);
 const status={READY:'No eligible noteworthy annual revenue change.',MISSING_DATA:'Saved annual revenue evidence is missing.',
  INSUFFICIENT_COMPARISON:'Annual revenue periods are not sufficiently comparable.',UNAVAILABLE:'Private financial evidence is unavailable.',
  NOT_CHECKED:'Financial checks are limited to the first five followed stocks.'} as const;
 return <section className="rounded border p-3 text-sm" aria-label={t('Financial changes (private experiment)')}>
  <h3 className="font-medium">{t('Financial changes (private experiment)')}</h3>
  <p className="mt-1 text-xs text-muted-foreground">{t(expanded?'Saved annual comparisons. Historical evidence, not new filings, causal explanations or investment recommendations.':'Saved annual revenue only. Not a new publication, causal explanation or investment recommendation.')}</p>
  {!page.items.length&&<p className="mt-2">{t(expanded&&page.status==='READY'?'No eligible noteworthy change in the selected saved metrics.':expanded&&page.status==='MISSING_DATA'?'Selected saved metric observations are missing.':expanded&&page.status==='INSUFFICIENT_COMPARISON'?'Selected saved periods are not sufficiently comparable.':status[page.status])}</p>}
  {page.items.map(item=>{const e=item.evidence as FinancialEvidence,i=e.insight;return <div key={item.id} className="mt-3 space-y-2" data-financial-update={item.id}>
   <p>{metricLabel(i.metric)} · {i.current_period} / {i.comparison_period} · {e.source}</p>
   <p>{number(i.current_value)} / {number(i.comparison_value)} {i.unit}</p>
   <p>{t('Absolute change')}: {number(i.absolute_change)} {i.unit} · {t('Percentage change')}: {i.percentage_change===null?'—':new Intl.NumberFormat(language==='vi'?'vi-VN':'en-US',{style:'percent',maximumFractionDigits:12}).format(i.percentage_change)}</p>
   <p className="text-xs">{t('Attention rule')}: {i.attention_reason.criteria.join(', ')} · financial-attention-v1</p>
   {i.attention_reason.criteria.includes('RELATIVE_MOVEMENT')&&<p className="text-xs">{t('Attention threshold')}: {new Intl.NumberFormat(language==='vi'?'vi-VN':'en-US',{style:'percent',maximumFractionDigits:12}).format(i.attention_reason.thresholds.relative_movement)}</p>}
   <p className="text-xs text-muted-foreground">{t('Missing information')}: {i.missing_information.join(', ')||'—'}</p>
   <button data-review-financial={item.id} disabled={disabled||!isUnread(state,symbol,item)} className="text-xs text-primary underline disabled:text-muted-foreground" onClick={()=>review([item])}>{t(isUnread(state,symbol,item)?'Mark reviewed':'Reviewed')}</button>
   <details className="text-xs"><summary className="cursor-pointer">{t('View source evidence')}</summary><pre className="mt-2 whitespace-pre-wrap break-all rounded bg-muted/40 p-3">{JSON.stringify(e,null,2)}</pre></details>
  </div>;})}
  {expanded&&!!page.checks?.length&&<details className="mt-2 text-xs"><summary>{t('Saved metric checks')}</summary><ul>{page.checks.map(check=><li key={check.metric}>{metricLabel(check.metric)} · {check.current_period||'—'} / {check.comparison_period||'—'} · {t(check.status==='READY'?check.noteworthy?'Meets the existing attention rule':'Comparable, below the existing attention rule':check.status==='MISSING_DATA'?'Selected saved metric observations are missing.':'Selected saved periods are not sufficiently comparable.')}<p>{check.reasons.join(', ')}</p></li>)}</ul></details>}
  {!page.items.length&&page.reasons.length>0&&<details className="mt-2 text-xs"><summary>{t('Missing information')}</summary><ul>{page.reasons.map(reason=><li key={reason}>{reason}</li>)}</ul></details>}
 </section>;
}
