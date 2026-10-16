"use client";
import Link from 'next/link';
import {ArrowUpRight} from 'lucide-react';
import {useLocale} from '@/lib/i18n';
import {movement,type LiveBatch} from '@/lib/live-market';
import {quoteMapCell} from '@/lib/quoteMap';
import {useLivePrices} from './LivePrice';

type Identity={symbol:string;company_name?:string|null;display_name_en?:string|null;exchange?:string|null};
const backgrounds={up:'border-emerald-600/35 bg-emerald-500/10',down:'border-red-600/35 bg-red-500/10',
  unchanged:'border-yellow-600/35 bg-yellow-500/10',neutral:'border-border bg-muted/20'};

export function QuoteMapView({stocks,data,failed=false,now=new Date(),scope,onSelect}: {
  stocks:Identity[];data:LiveBatch|null;failed?:boolean;now?:Date;scope:'page'|'watchlist';onSelect?:(symbol:string)=>void
}) {
  const {t,ui,number,date,language}=useLocale();
  return <section aria-label={t(scope==='page'?'Price map · this page':'Price map · followed stocks')}>
    <div className="mb-3 space-y-1 text-xs text-muted-foreground">
      <p>{t(scope==='page'?'Only the equities on this loaded page. Filters and pagination still apply.':'Only your followed stocks. This is not a market-wide view.')}</p>
      <p>{t('Equal-sized tiles. Color shows observed price direction, not market value, money flow or strength.')}</p>
      <p>{t('Changes use each source reference price. Stale or missing quotes have a neutral background; inspect each timestamp and session.')}</p>
    </div>
    <div className="grid grid-cols-1 gap-2 min-[360px]:grid-cols-2 md:grid-cols-3 xl:grid-cols-5">
      {stocks.map(stock=>{
        const {row,status,tone}=quoteMapCell(stock.symbol,data?.items[stock.symbol],failed,now);
        const direction=movement(row?.change);
        return <article key={stock.symbol} data-quote-tile={stock.symbol} data-tone={tone} data-status={status}
          className={`min-w-0 rounded-md border p-3 ${backgrounds[tone]}`}>
          <Link href={'/stocks/'+encodeURIComponent(stock.symbol)} onClick={()=>onSelect?.(stock.symbol)}
            className="flex min-h-6 items-center justify-between gap-2 rounded font-semibold hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring"
            aria-label={t('Research {ticker}',{ticker:stock.symbol})}>{stock.symbol}<ArrowUpRight size={13} aria-hidden="true"/></Link>
          <p className="mt-1 truncate text-[10px] leading-4 text-muted-foreground" title={(language==='vi'?stock.company_name:stock.display_name_en)||stock.company_name||stock.symbol}>
            {(language==='vi'?stock.company_name:stock.display_name_en)||stock.company_name||stock.symbol}
          </p>
          <p className="mt-3 financial text-lg font-semibold leading-6 tabular-nums">{row?number(row.last_price):t('Unavailable')} {row&&<span className="text-[10px] font-normal text-muted-foreground">VND</span>}</p>
          <p className={`mt-1 flex flex-wrap gap-x-1 text-xs tabular-nums ${direction.color}`}>
            <span>{row?.change!=null&&Number.isFinite(row.change)?row.change>0?'↑':row.change<0?'↓':'=':'—'} {ui(direction.label)}</span>
            {row?.change_percent!=null&&Number.isFinite(row.change_percent)&&<span>{row.change_percent>0?'+':''}{number(row.change_percent)}%</span>}
          </p>
          <p className="mt-3 text-[10px] leading-4 text-muted-foreground">{ui(status==='fresh'?'Current market':status==='stale'?'Stale market data':'Market data unavailable')}</p>
          {row&&<>
            <time dateTime={row.updated_at} className="block text-[10px] leading-4 text-muted-foreground">{date(row.updated_at,true)}</time>
            <p className="text-[10px] leading-4 text-muted-foreground">{stock.exchange?stock.exchange+' · ':''}{ui(row.session==='active'?'Active trading session':row.session==='break'?'Midday break':row.session==='closed'?'Market closed':'Session unconfirmed')}</p>
            <details className="mt-2 border-t border-current/10 pt-2 text-[10px] leading-4 text-muted-foreground">
              <summary className="cursor-pointer">{t('Source & session')}</summary>
              <p className="mt-1 break-all">{row.source}</p>
              <p>{t('Trading date ·')} {date(row.trading_date)}</p>
              <p>{t('Reference price')} {number(row.reference_price)} VND</p>
              <p>{t('Price change')} {row.change!=null&&Number.isFinite(row.change)?(row.change>0?'+':'')+number(row.change):t('Unavailable')} VND</p>
            </details>
          </>}
        </article>;
      })}
    </div>
  </section>;
}

export default function QuoteMap(props:{stocks:Identity[];scope:'page'|'watchlist';onSelect?:(symbol:string)=>void}) {
  const {data,failed}=useLivePrices();
  return <QuoteMapView {...props} data={data} failed={failed}/>;
}
