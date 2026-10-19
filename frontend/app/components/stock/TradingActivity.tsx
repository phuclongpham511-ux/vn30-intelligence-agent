"use client";
import type {LiveSnapshot,LiveStatus} from '@/lib/live-market';
import {activityValue,activityNumber} from '@/lib/tradingActivity';
import {useLocale} from '@/lib/i18n';

/** Read the shared quote only. No provider request, derived traded value or lease. */
export default function TradingActivity({row,status,now=new Date()}:{row:LiveSnapshot;status:string;now?:Date}) {
  const {t,date,language}=useLocale(),a=row.trading_activity;
  return <section className="trading-activity-detail"><h3>{t('Matched session activity')}</h3><p>{t('KL / GT target: cumulative regular matched trades; put-through excluded.')}</p>{a&&<p>{t(a.scope==='regular_matched'?'Regular matched trades':'Trade scope not qualified')} · {t(a.cumulative?'Cumulative':'Interval / unknown')} · {t(a.includes_negotiated_trades===false?'Put-through excluded':a.includes_negotiated_trades===true?'Includes put-through':'Put-through scope unknown')}</p>}<dl>{(['volume','value'] as const).map(key=>{const value=activityValue(row,key,status,now),m=a?.[key];return <div key={key}><dt>{t(key==='volume'?'Trading volume':'Trading value')}</dt><dd>{activityNumber(value,key,language)}{value!==null?' '+(key==='volume'?t('shares'):'VND'): ' · '+t(status==='stale'?'Stale':'Not qualified / unavailable')}</dd>{m&&<dd className="trading-provenance">{t('Original field')}: {m.field||'—'} · {t('Original unit')}: {m.unit||t('Unknown')}{m.raw_value!==null&&<> · {t('Original value')}: {String(m.raw_value)}</>}</dd>}</div>;})}</dl>{a?<p className="trading-provenance">{a.source} · {a.symbol} · {date(a.trading_date)} · {t('Trading day')} · <time dateTime={a.observed_at}>{date(a.observed_at,true)}</time> ICT</p>:<p>{t('No qualified cumulative session evidence. Interval volume is not KL; price × volume is not GT.')}</p>}</section>;
}
