"use client";
import {useLocale} from '@/lib/i18n';
import {provisionalFreshness,type ProvisionalMarket} from '@/lib/provisionalMarket';

/** Separately dated evidence, never converted into a qualified tick/activity DTO. */
export default function ProvisionalEvidence({packet:p,now}:{packet:ProvisionalMarket;now:Date}) {
  const {t,date,number}=useLocale();
  const status=provisionalFreshness(p,now);
  return <section className="min-w-0 space-y-2 rounded border p-3 text-xs" data-provisional-market={p.key.symbol}>
    <h3 className="font-semibold">{p.key.symbol} · {p.key.exchange} · {p.key.trading_date} · PROVISIONAL_INTERNAL</h3>
    <p>{t('Saved daily evidence, not a live quote.')} · {t(status==='stale'?'Stale':status==='fresh'?'Source time within internal age limit':'Source freshness unverified')} · {t('Evaluated at')} {date(now.toISOString(),true)} ICT</p>
    <p>{t('Daily matched totals under internal conventions; exact trade inclusion is unverified.')}</p>
    <dl className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {(['floor','reference','ceiling'] as const).map(key=><div key={key}><dt>{t(key==='floor'?'Floor':key==='reference'?'Reference price':'Ceiling')}</dt><dd className="break-words tabular-nums" data-provisional-band={key}>{number(p.bands[key].value)} VND/share</dd></div>)}
      <div><dt>{t('Vol')}</dt><dd className="break-words tabular-nums">{number(p.matched.volume.value)} {t('shares')}</dd></div>
      <div><dt>{t('Value')}</dt><dd className="break-words tabular-nums">{number(p.matched.value.value)} VND</dd></div>
    </dl>
    <p>{t('Source time')}: {p.matched.source_timestamp?date(p.matched.source_timestamp,true)+' ICT':t('Unavailable')} · {t('Fetched at')}: {date(p.matched.fetched_at,true)} ICT</p>
    <details><summary>{t('Provisional source receipts')}</summary><p>{t('Units use owner-approved conventions, multiplier 1. These receipts do not grant public rights.')}</p>
      <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-all">{JSON.stringify(p,null,2)}</pre>
    </details>
  </section>;
}
