"use client";
import Link from 'next/link';
import {useLocale} from '@/lib/i18n';
import {dailyBriefing, type BriefingItem} from '@/lib/dailyBriefing';
import type {Intelligence, WatchlistState} from '@/lib/watchlist';
import {collectionLabels} from '@/lib/collectionStatus';

export default function WatchlistBriefing({data,state,storageError,review}: {
  data:Intelligence; state:WatchlistState; storageError:boolean; review:(entry:BriefingItem)=>void;
}) {
  const {t,ui,date}=useLocale();
  const brief=dailyBriefing(data,state);
  return <section aria-labelledby="read-first-heading" className="panel p-4 sm:p-5" data-daily-briefing>
    <div className="flex flex-wrap items-baseline justify-between gap-2">
      <h2 id="read-first-heading" className="text-base">{t('Read first')}</h2>
      <a href="#watched-stocks" className="text-xs text-primary hover:underline">{t('All stock updates')}</a>
    </div>
    <p className="mt-1 text-xs text-muted-foreground">{t('Unreviewed reporting and discussion for followed stocks, newest publication first. Up to three from this page; not an importance score.')}</p>
    {storageError?<p role="status" className="mt-3 text-sm text-muted-foreground">{t('Review state unavailable. Unread counts are unknown.')}</p>:<>
      {brief.items.length?<ol className="mt-3 divide-y">{brief.items.map(entry=><li key={entry.id} data-briefing-item={entry.id} className="py-3 first:pt-0 last:pb-0">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-muted-foreground">
          <span>{t(entry.item.kind==='news'?'News':'Community')}{entry.item.kind==='community'?' · '+t('Unverified'):''}</span>
          <span>· {entry.source}</span>
          <span>· {t(entry.published?'Published':'First observed')} <time dateTime={entry.time}>{date(entry.time,true)}</time></span>
          {entry.fixture&&<span>{t('Fixture')}</span>}
        </div>
        <h3 className="mt-1 break-words text-sm font-medium leading-5"><a href={entry.url} target="_blank" rel="noopener noreferrer" className="hover:text-primary focus-visible:outline focus-visible:outline-2">{entry.item.title}</a></h3>
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <div className="min-w-0"><p className="text-[11px] text-muted-foreground">{t(entry.corrected?'Updated since review':'Unreviewed')} · {t('In your Watchlist')}</p>
            <div className="mt-1 flex flex-wrap gap-2">{entry.symbols.map(symbol=><Link key={symbol} className="rounded border px-2 py-1 text-xs font-medium text-primary hover:bg-muted focus-visible:outline focus-visible:outline-2" href={'/stocks/'+encodeURIComponent(symbol)}>{symbol}</Link>)}</div>
          </div>
          <button type="button" aria-label={t('Review update: {title}',{title:entry.item.title})} onClick={()=>review(entry)} className="rounded px-2 py-2 text-xs text-primary underline focus-visible:outline focus-visible:outline-2">{t('Mark this update reviewed')}</button>
        </div>
        <details className="mt-2 text-xs text-muted-foreground"><summary className="cursor-pointer">{t('Source & review details')}</summary>
          <p className="mt-2">{t('Source checked')}: {date(entry.sourceCheckedAt,true)} · {ui(entry.sourceStatus==='unknown'?'Unavailable':collectionLabels[entry.sourceStatus])}</p>
          <p className="mt-1">{t('This action reviews only this displayed item for the stocks listed above. Opening the publisher or stock never marks it reviewed.')}</p>
          <a className="mt-1 inline-block text-primary hover:underline" href={'#watchlist-evidence-'+encodeURIComponent(entry.symbols[0])}>{t('Review & evidence')}</a>
        </details>
        {entry.sourceStatus!=='healthy'&&<p className="mt-2 text-xs text-amber-700 dark:text-amber-300">{t('Source coverage is incomplete. This is persisted evidence, not a fresh source check.')}</p>}
      </li>)}</ol>:<p className="mt-3 text-sm">{t('No unreviewed reporting or discussion in the loaded page.')}</p>}
      {brief.total>brief.items.length&&<p className="mt-3 text-xs text-muted-foreground">{t('{count} more unreviewed items remain in the stock list below.',{count:brief.total-brief.items.length})}</p>}
    </>}
    {brief.incomplete&&<p className="mt-3 text-xs text-amber-700 dark:text-amber-300">{t('Coverage incomplete; this brief is not a complete account of market activity.')}</p>}
    <p className="mt-3 text-[11px] text-muted-foreground">{t('Technical evidence and its assurance labels remain in each stock below.')}</p>
  </section>;
}
