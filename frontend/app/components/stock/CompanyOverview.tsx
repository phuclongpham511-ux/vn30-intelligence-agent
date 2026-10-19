"use client";
import Link from 'next/link';
import {useLocale} from '@/lib/i18n';
import type {Security} from '@/lib/types';

/** Existing cached identity only. Financial analysis remains in its lazy-loaded tab. */
export default function CompanyOverview({security,syncedAt}:{security:Security;syncedAt:string|null}) {
  const {t,date}=useLocale();
  const sync=security.last_synced_at||syncedAt;
  const validSync=!!sync&&Number.isFinite(Date.parse(sync));
  return <section className="panel company-overview" aria-label={t('Company overview')}>
    <div className="company-overview-heading"><h2>{t('Company overview')}</h2><span className="stock-badge">{t('Cached identity')}</span></div>
    <dl className="stock-profile company-facts"><div><dt>{t('Ticker')}</dt><dd>{security.symbol}</dd></div><div><dt>{t('Exchange')}</dt><dd>{security.exchange||t('Unavailable')}</dd></div><div><dt>{t('Instrument')}</dt><dd>{t('Listed equity')}</dd></div></dl>
    <div className="company-description"><h3>{t('Business description')}</h3><p>{t('Not supplied by the current company-data contract.')}</p></div>
    <dl className="company-classification"><div><dt>{t('Industry / sector')}</dt><dd>{t('Not qualified for display')}</dd></div></dl>
    <details className="company-source"><summary>{t('Company source & freshness')}</summary><p>{t('Metadata source')}: {security.source||t('Unavailable')}</p><p>{t('Metadata cache synchronized')}: {validSync?<><time dateTime={sync}>{date(sync,true)}</time> ICT</>:t('Unavailable')}</p><p>{t('Synchronization time is not an issuer publication date. Industry names require qualified mapping and display rights.')}</p></details>
    <div className="company-financials"><h3>{t('Financial information')}</h3><p>{t('Reported statements and ratios, when available. Missing financial values stay unavailable.')}</p><Link href="#stock-fundamentals">{t('View financial statements')} ↗</Link></div>
  </section>;
}
