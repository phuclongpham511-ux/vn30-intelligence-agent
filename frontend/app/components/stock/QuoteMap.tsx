"use client";
import {useId,useState} from 'react';
import Link from 'next/link';
import {ArrowUpRight,X} from 'lucide-react';
import {useLocale} from '@/lib/i18n';
import {movement,type LiveBatch} from '@/lib/live-market';
import {boardRows,boardColumns,type BoardIdentity,type BoardSort} from '@/lib/quoteMap';
import {useLivePrices} from './LivePrice';

const backgrounds={up:'border-emerald-600/30 bg-emerald-500/15 hover:bg-emerald-500/25',
  down:'border-red-600/30 bg-red-500/15 hover:bg-red-500/25',
  unchanged:'border-yellow-600/30 bg-yellow-500/15 hover:bg-yellow-500/25',
  neutral:'border-border bg-muted/25 hover:bg-muted/50'};
type Props={stocks:BoardIdentity[];scope:'page'|'watchlist';scopeLabel?:string;onSelect?:(symbol:string)=>void;mode?:'board'|'heatmap'};

export function QuoteMapView({stocks,data,failed=false,now=new Date(),scope,scopeLabel,mode='board',onSelect}:Props&{
  data:LiveBatch|null;failed?:boolean;now?:Date
}) {
  const {t,ui,number,date,language,locale}=useLocale();
  const id=useId();
  const [sort,setSort]=useState<BoardSort>('change');
  const [selected,setSelected]=useState<string|null>(null);
  const rows=boardRows(stocks,data,failed,now,sort),columns=boardColumns(rows);
  const loading=!data&&!failed;
  const fresh=rows.filter(r=>r.status==='fresh').length,stale=rows.filter(r=>r.status==='stale').length;
  const missing=rows.filter(r=>r.status==='unavailable').length;
  const label=scopeLabel||t(scope==='watchlist'?'Followed stocks':'Loaded results');
  const signed=(value:number|null|undefined)=>value!=null&&Number.isFinite(value)?(value>0?'+':'')+number(value):'—';
  const clock=(value:string)=>Number.isFinite(Date.parse(value))?new Intl.DateTimeFormat(locale,{timeZone:'Asia/Ho_Chi_Minh',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(value)):'—';
  const statusText=(status:string)=>t(status==='fresh'?'Current source observation':status==='stale'?'Stale market data':'Market data unavailable');
  const sessionText=(session:string)=>ui(session==='active'?'Active trading session':session==='break'?'Midday break':session==='closed'?'Market closed':'Session unconfirmed');
  const counts=['up','down','unchanged'].map(tone=>rows.filter(r=>r.tone===tone).length);
  const sourceControl=(entry:typeof rows[number])=><button type="button" aria-label={t('Quote source for {ticker}',{ticker:entry.stock.symbol})}
    aria-expanded={selected===entry.stock.symbol} aria-controls={selected===entry.stock.symbol?id+'-'+entry.stock.symbol:undefined}
    title={statusText(entry.status)+(entry.row?' · '+date(entry.row.updated_at,true):'')}
    onClick={()=>setSelected(selected===entry.stock.symbol?null:entry.stock.symbol)}
    className="flex min-h-9 min-w-11 items-center justify-end gap-1 rounded px-1 text-[10px] tabular-nums text-muted-foreground hover:bg-background/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring">
      <span aria-hidden="true" className={`h-1.5 w-1.5 shrink-0 rounded-full ${entry.status==='fresh'?'bg-foreground/45':entry.status==='stale'?'bg-amber-500':'bg-muted-foreground/35'}`}/>
      {entry.row?<time dateTime={entry.row.updated_at}>{clock(entry.row.updated_at)}</time>:loading?'…':'—'}
  </button>;
  const sourceDetail=(entry:typeof rows[number])=>selected===entry.stock.symbol?<div id={id+'-'+entry.stock.symbol} className="col-span-full my-1 min-w-0 rounded border bg-background/90 p-3 text-xs">
      <div className="flex items-center justify-between gap-2"><strong>{entry.stock.symbol} · {(language==='vi'?entry.stock.company_name:entry.stock.display_name_en)||entry.stock.company_name||entry.stock.symbol}</strong>
        <button type="button" aria-label={t('Close quote source')} onClick={()=>setSelected(null)} className="rounded p-2 hover:bg-muted"><X size={14}/></button></div>
      <p className="mt-1 text-muted-foreground">{statusText(entry.status)}{entry.row?' · '+date(entry.row.updated_at,true):''} · {entry.stock.exchange}</p>
      {entry.row&&<div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-muted-foreground">
        <span className="break-all">{entry.row.source}</span><span>{sessionText(entry.row.session)}</span>
        <span>{t('Trading date ·')} {date(entry.row.trading_date)}</span>
        <span>{t('Reference price')} {number(entry.row.reference_price)} VND</span>
        <span>{t('Price change')} {signed(entry.row.change)} VND</span>
      </div>}
    </div>:null;
  return <section aria-label={t(scope==='watchlist'?'Market board · followed stocks':'Market board')}>
    <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-y py-3">
      <div className="flex min-w-0 flex-wrap items-baseline gap-x-3 gap-y-1">
        <h3 className="text-sm font-semibold">{label}</h3>
        <span role="status" className="text-xs text-muted-foreground">{loading?t('Loading observed quotes…'):t('{available}/{total} quotes',{available:fresh+stale,total:rows.length})}</span>
        {!loading&&<span className="text-[10px] text-muted-foreground">{t('{fresh} current · {stale} stale · {missing} missing',{fresh,stale,missing})}</span>}
      </div>
      <label className="flex items-center gap-2 text-xs text-muted-foreground">{t('Sort')}
        <select aria-label={t('Quote sorting')} className="h-8 rounded border bg-background px-2 text-xs text-foreground" value={sort} onChange={e=>setSort(e.target.value as BoardSort)}>
          <option value="change">{t('Change % ↓')}</option><option value="fallers">{t('Change % ↑')}</option>
          <option value="price">{t('Price ↓')}</option><option value="ticker">{t('Ticker A–Z')}</option>
        </select>
      </label>
    </div>
    <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] tabular-nums text-muted-foreground">
      <span className="positive">↑ {t('Up')} {loading?'—':counts[0]}</span><span className="negative">↓ {t('Down')} {loading?'—':counts[1]}</span>
      <span className="unchanged">= {t('Unchanged')} {loading?'—':counts[2]}</span>
      <span>{t('Current observations in this selection only')}</span>{data&&<span>{sessionText(data.session)}</span>}<span className="ml-auto">VND · ICT (UTC+7)</span>
    </div>
    {!loading&&fresh+stale===0&&<p role="status" className="mb-3 rounded border border-amber-500/40 p-3 text-xs">{t('No observed quotes for this selection. Metadata is available; prices have not been observed.')}</p>}
    {failed&&<p role="alert" className="mb-3 text-xs text-amber-700 dark:text-amber-400">{t('Quote request failed. Previous observations are not current.')}</p>}
    {mode==='heatmap'?<div className="grid grid-cols-3 gap-1 sm:grid-cols-5 lg:grid-cols-6">
      {rows.map(entry=><article key={entry.stock.symbol} data-quote-tile={entry.stock.symbol} data-tone={entry.tone} data-status={entry.status}
        className={`relative min-w-0 rounded border px-2 pt-2 ${selected===entry.stock.symbol?'col-span-full':''} ${backgrounds[entry.tone]}`}>
        <Link href={'/stocks/'+encodeURIComponent(entry.stock.symbol)} onClick={()=>onSelect?.(entry.stock.symbol)} aria-label={t('Research {ticker}',{ticker:entry.stock.symbol})}
          className="block rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring">
          <span className="block text-xs font-semibold">{entry.stock.symbol}</span>
          <span className="financial mt-1 block text-right text-sm font-semibold tabular-nums">{entry.row?number(entry.row.last_price):'—'}</span>
          <span className={`block text-right text-xs tabular-nums ${movement(entry.row?.change).color}`}>{signed(entry.row?.change_percent)}{entry.row?.change_percent!=null&&Number.isFinite(entry.row.change_percent)?'%':''}</span>
        </Link>{sourceControl(entry)}{sourceDetail(entry)}
      </article>)}
    </div>:<div className="grid grid-cols-1 items-start gap-3 md:grid-cols-2 xl:grid-cols-3">
      {columns.map((column,index)=><div key={index} className="min-w-0 overflow-hidden rounded-md border">
        <div className="flex items-center justify-between border-b bg-muted/45 px-3 py-2 text-xs font-semibold"><span>{label}</span><span className="text-[10px] font-normal text-muted-foreground">{t('Part {part} of {total}',{part:index+1,total:columns.length})}</span></div>
        <div className="grid grid-cols-[minmax(0,1fr)_48px] gap-1 px-2 py-1.5 text-[10px] text-muted-foreground">
          <div className="grid grid-cols-[minmax(46px,1fr)_minmax(66px,1fr)_62px] gap-1"><span>{t('Ticker')}</span><span className="text-right">{t('Price')}</span><span className="text-right">{t('Change %')}</span></div><span className="text-right">{t('Source time')}</span>
        </div>
        <div className="space-y-0.5 px-1 pb-1">{column.map(entry=><article key={entry.stock.symbol} data-quote-row={entry.stock.symbol} data-tone={entry.tone} data-status={entry.status}
          className={`grid grid-cols-[minmax(0,1fr)_48px] items-center gap-1 rounded border border-transparent px-1 ${backgrounds[entry.tone]}`}>
          <Link href={'/stocks/'+encodeURIComponent(entry.stock.symbol)} onClick={()=>onSelect?.(entry.stock.symbol)}
            title={(language==='vi'?entry.stock.company_name:entry.stock.display_name_en)||entry.stock.company_name||entry.stock.symbol}
            aria-label={t('Research {ticker}',{ticker:entry.stock.symbol})}
            className="grid min-h-9 grid-cols-[minmax(46px,1fr)_minmax(66px,1fr)_62px] items-center gap-1 rounded text-xs tabular-nums focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring">
            <strong className="flex items-center gap-1">{entry.stock.symbol}<ArrowUpRight size={10} aria-hidden="true" className="shrink-0 text-muted-foreground"/></strong>
            <span className="financial text-right font-semibold">{entry.row?number(entry.row.last_price):'—'}</span>
            <span className={`text-right font-medium ${movement(entry.row?.change).color}`}>{signed(entry.row?.change_percent)}{entry.row?.change_percent!=null&&Number.isFinite(entry.row.change_percent)?'%':''}</span>
          </Link>{sourceControl(entry)}{sourceDetail(entry)}
        </article>)}</div>
      </div>)}
    </div>}
    <details className="mt-3 text-[11px] leading-5 text-muted-foreground"><summary className="w-fit cursor-pointer">{t('Source, coverage & methodology')}</summary>
      <p className="mt-2">{t('SSI source observations, not synchronized market-wide coverage. Time buttons open the original timestamp, session and reference price. Stale and missing quotes stay neutral.')}</p>
      <p>{t('Current-direction counts exclude stale and missing quotes. Equal heatmap cells have no capitalization weighting. No sector return, money flow or strength is inferred.')}</p>
      <p>{t('Session volume is unavailable in the qualified quote contract; minute-bar volume is not session volume.')}</p>
      {scope==='watchlist'&&<p>{t('Only your followed stocks. This is not a market-wide view.')}</p>}
    </details>
  </section>;
}

export default function QuoteMap(props:Props) {
  const {data,failed}=useLivePrices();
  return <QuoteMapView {...props} mode={props.mode??(props.scope==='watchlist'?'heatmap':'board')} data={data} failed={failed}/>;
}
