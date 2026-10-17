"use client";
import {useRef,useState,type ReactNode} from 'react';
import Link from 'next/link';
import {Dialog} from 'radix-ui';
import {X} from 'lucide-react';
import {useLocale} from '@/lib/i18n';
import type {LiveBatch} from '@/lib/live-market';
import {boardRows,boardColumns,movementGroups,heatmapBin,type BoardRow,type BoardIdentity,type BoardSort,type MovementGroup} from '@/lib/quoteMap';
import {useLivePrices} from './LivePrice';

type Props={stocks:BoardIdentity[];scope:'page'|'watchlist';scopeLabel?:string;onSelect?:(symbol:string)=>void;mode?:'board'|'heatmap';controls?:ReactNode;sorting?:BoardSort;onSortingChange?:(sort:BoardSort)=>void;organization?:'ordinary'|'movement';onOrganizationChange?:(value:'ordinary'|'movement')=>void};
const groupLabels={advancing:'Advancing',declining:'Declining',unchanged:'Unchanged',unqualified:'Stale / Missing'} as const;
export function QuoteMapView({stocks,data,failed=false,now=new Date(),scope,scopeLabel,mode='board',onSelect,controls,sorting,onSortingChange,organization:controlledOrganization,onOrganizationChange}:Props&{data:LiveBatch|null;failed?:boolean;now?:Date}) {
  const {t,ui,number,date,language,locale}=useLocale();
  const sourceFocus=useRef<HTMLButtonElement|null>(null);
  const [localSort,setLocalSort]=useState<BoardSort>('change');
  const [localOrganization,setLocalOrganization]=useState<'ordinary'|'movement'>('ordinary');
  const sort=sorting??localSort,setSort=onSortingChange??setLocalSort;
  const organization=controlledOrganization??localOrganization,setOrganization=onOrganizationChange??setLocalOrganization;
  const [selected,setSelected]=useState<string|null>(null);
  const [density,setDensity]=useState<'compact'|'detailed'>(scope==='watchlist'?'detailed':'compact');
  const rows=boardRows(stocks,data,failed,now,sort),groups=movementGroups(rows);
  const entry=rows.find(row=>row.stock.symbol===selected);
  const loading=!data&&!failed,unknownCoverage=failed;
  const fresh=rows.filter(r=>r.status==='fresh').length,stale=rows.filter(r=>r.status==='stale').length;
  const missing=rows.filter(r=>r.status==='unavailable').length;
  const label=scopeLabel||t(scope==='watchlist'?'Followed stocks':'Loaded results');
  const signed=(v:number|null|undefined)=>typeof v==='number'&&Number.isFinite(v)?(v>0?'+':'')+number(v):'—';
  const percentage=(r:BoardRow)=>signed(r.row?.change_percent)+(typeof r.row?.change_percent==='number'&&Number.isFinite(r.row.change_percent)?'%':'');
  const clock=(v:string)=>Number.isFinite(Date.parse(v))?new Intl.DateTimeFormat(locale,{timeZone:'Asia/Ho_Chi_Minh',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(v)):'—';
  const sourceDay=(v:string)=>Number.isFinite(Date.parse(v))?new Intl.DateTimeFormat(locale,{timeZone:'Asia/Ho_Chi_Minh',day:'2-digit',month:'2-digit'}).format(new Date(v)):'—';
  const statusText=(status:string)=>t(status==='fresh'?'Current source observation':status==='stale'?'Stale market data':'Market data unavailable');
  const sessionText=(session:string)=>ui(session==='active'?'Active trading session':session==='break'?'Midday break':session==='closed'?'Market closed':'Session unconfirmed');
  const color=(r:BoardRow)=>r.status!=='fresh'?'text-muted-foreground':r.tone==='up'?'positive':r.tone==='down'?'negative':r.tone==='unchanged'?'unchanged':'text-muted-foreground';
  const count=(key:MovementGroup)=>loading||unknownCoverage?'—':groups[key].length;
  const sourceControl=(row:BoardRow)=><button type="button" className={`quote-source ${row.status==='stale'?'quote-stale':''}`} aria-label={t('Quote source for {ticker}',{ticker:row.stock.symbol})} aria-haspopup="dialog" title={statusText(row.status)+(row.row?' · '+date(row.row.updated_at,true):'')} onClick={event=>{sourceFocus.current=event.currentTarget;setSelected(row.stock.symbol);}}>
    {row.row?<><span className="sr-only">{statusText(row.status)} · </span>{row.status==='stale'?<><time className="sr-only" dateTime={row.row.updated_at}>{date(row.row.updated_at,true)}</time><span>{t('Stale')} · {sourceDay(row.row.updated_at)}</span></>:<time dateTime={row.row.updated_at}>{clock(row.row.updated_at)}</time>}</>:loading?'…':unknownCoverage?t('Unknown'):t('Missing')}
  </button>;
  const table=(entries:BoardRow[])=><table className="quote-table"><thead><tr><th scope="col">{t('Ticker')}</th><th scope="col">{t('Price')} · VND</th><th scope="col">Δ %</th><th scope="col">{t('Time')} · ICT</th></tr></thead><tbody>{entries.map(row=><tr key={row.stock.symbol} data-quote-row={row.stock.symbol} data-tone={row.tone} data-status={row.status}>
    <th scope="row"><Link href={'/stocks/'+encodeURIComponent(row.stock.symbol)} onClick={()=>onSelect?.(row.stock.symbol)} aria-label={t('Research {ticker}',{ticker:row.stock.symbol})} title={(language==='vi'?row.stock.company_name:row.stock.display_name_en)||row.stock.company_name||row.stock.symbol}>{row.stock.symbol}<span aria-hidden="true"> ↗</span></Link></th>
    <td className={color(row)}>{row.row?number(row.row.last_price):'—'}</td><td className={color(row)}>{percentage(row)}</td><td>{sourceControl(row)}</td>
  </tr>)}</tbody></table>;
  const tiles=(entries:BoardRow[])=><div className={`quote-map-grid heatmap-${density}`}>{entries.map(row=><article key={row.stock.symbol} data-quote-tile={row.stock.symbol} data-tone={row.tone} data-status={row.status} className={`quote-tile bin-${heatmapBin(row)}`}>
    <Link href={'/stocks/'+encodeURIComponent(row.stock.symbol)} onClick={()=>onSelect?.(row.stock.symbol)} aria-label={t('Research {ticker}',{ticker:row.stock.symbol})}><strong>{row.stock.symbol} ↗</strong><b>{percentage(row)}</b>{density==='detailed'&&<span>{row.row?number(row.row.last_price)+' VND':'—'}</span>}</Link>{density==='detailed'?sourceControl(row):<button type="button" className="quote-compact-source" aria-label={t('Quote source for {ticker}',{ticker:row.stock.symbol})} aria-haspopup="dialog" onClick={event=>{sourceFocus.current=event.currentTarget;setSelected(row.stock.symbol);}}>{row.status==='fresh'?t('Source'):loading?'…':unknownCoverage?t('Unknown'):row.status==='stale'?t('Stale'):t('Missing')}</button>}
  </article>)}</div>;
  const groupSection=(key:MovementGroup)=><section className="quote-panel" key={key}><div className="quote-group-heading"><h3 className={key==='advancing'?'positive':key==='declining'?'negative':key==='unchanged'?'unchanged':''}>{t(groupLabels[key])}</h3><span>{count(key)} {t('stocks')}</span></div>{groups[key].length?(mode==='board'?table(groups[key]):tiles(groups[key])):<p className="quote-empty">{loading?t('Loading observed quotes…'):unknownCoverage?t('Quote coverage unavailable'):t('No stocks in this category')}</p>}</section>;
  return <section className="quote-workspace" aria-label={t(scope==='watchlist'?'Market board · followed stocks':'Market board')}>
    <div className="quote-toolbar">{controls}<label>{t('Sort')}<select aria-label={t('Quote sorting')} value={sort} onChange={e=>setSort(e.target.value as BoardSort)}><option value="change">{t('Change % ↓')}</option><option value="fallers">{t('Change % ↑')}</option><option value="price">{t('Price ↓')}</option><option value="ticker">{t('Ticker A–Z')}</option></select></label><label>{t('Organization')}<select aria-label={t('Organization')} value={organization} onChange={e=>setOrganization(e.target.value as typeof organization)}><option value="ordinary">{t(mode==='board'?'Sortable table':'Sorted grid')}</option><option value="movement">{t('Movement groups')}</option></select></label>
      {mode==='heatmap'&&scope==='page'&&<label>{t('Density')}<select aria-label={t('Heatmap density')} value={density} onChange={e=>setDensity(e.target.value as typeof density)}><option value="compact">{t('Compact')}</option><option value="detailed">{t('Detailed')}</option></select></label>}
      <span className="quote-coverage" role="status"><strong>{label}</strong> · {t(scope==='watchlist'?'Followed sample':'Visible sample')}: {loading?t('Loading observed quotes…'):unknownCoverage?t('Quote coverage unavailable'):t('{available}/{total} quotes',{available:fresh+stale,total:rows.length})}{!loading&&!unknownCoverage&&<> · {t('{fresh} current · {stale} stale · {missing} missing',{fresh,stale,missing})}</>}</span>
    </div>
    <div className="quote-sample-note"><span className="positive">↑ {t('Up')} {count('advancing')}</span><span className="negative">↓ {t('Down')} {count('declining')}</span><span className="unchanged">= {t('Unchanged')} {count('unchanged')}</span><span>{t('Current observations in this selection only')}</span>{data&&<span>{sessionText(data.session)}</span>}</div>
    {!loading&&!unknownCoverage&&fresh+stale===0&&<p role="status" className="quote-warning">{t('No observed quotes for this selection. Metadata is available; prices have not been observed.')}</p>}
    {failed&&<p role="alert" className="quote-warning">{t('Quote request failed. Previous observations are not current.')}</p>}
    {mode==='heatmap'&&<div className="quote-legend"><b>{t('Price change')} %</b>{[['negative-strong','≤ −1%'],['negative','−1% < Δ < 0'],['zero','0%'],['positive','0 < Δ < 1%'],['positive-strong','≥ +1%']].map(([bin,text])=><span key={bin}><i className={'bin-'+bin}/>{text}</span>)}<span>▧ {t('Stale / Missing')}</span></div>}
    {organization==='movement'?(mode==='board'?<div className="quote-columns">{groupSection('advancing')}{groupSection('declining')}<div className="quote-group-stack">{groupSection('unchanged')}{groupSection('unqualified')}</div></div>:<div className="quote-group-stack">{(Object.keys(groups) as MovementGroup[]).map(groupSection)}</div>):mode==='board'?<div className="quote-columns">{boardColumns(rows).map((column,index)=><div key={index} className="quote-panel">{table(column)}</div>)}</div>:<div className="quote-panel">{tiles(rows)}</div>}
    <p className="quote-footnote">{t(organization==='movement'?'Movement within this selection only · not sectors.':'Read down each panel, then left → right.')} · VND · ICT (UTC+7){mode==='heatmap'&&<> · {t('Equal cell area, not capitalization.')}</>}</p>
    <details className="quote-method"><summary>{t('Source, coverage & methodology')}</summary><p>{t('SSI source observations, not synchronized market-wide coverage. Time buttons open the original timestamp, session and reference price. Stale and missing quotes stay neutral.')}</p><p>{t('Current-direction counts exclude stale and missing quotes. Equal heatmap cells have no capitalization weighting. No sector return, money flow or strength is inferred.')}</p><p>{t('Session volume is unavailable in the qualified quote contract; minute-bar volume is not session volume.')}</p>{scope==='watchlist'&&<p>{t('Only your followed stocks. This is not a market-wide view.')}</p>}</details>
    <Dialog.Root open={!!entry} onOpenChange={open=>{if(!open)setSelected(null);}}><Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-50 bg-black/60"/><Dialog.Content className="quote-source-dialog" onCloseAutoFocus={event=>{event.preventDefault();sourceFocus.current?.focus();}}><Dialog.Title>{entry?.stock.symbol} · {t('Source & session')}</Dialog.Title><Dialog.Description>{entry&&statusText(entry.status)} · {entry?.stock.exchange} · {(language==='vi'?entry?.stock.company_name:entry?.stock.display_name_en)||entry?.stock.company_name}</Dialog.Description>
      {entry?.row?<dl><dt>{t('Source:')}</dt><dd>{entry.row.source}</dd><dt>{t('Source time')}</dt><dd><time dateTime={entry.row.updated_at}>{date(entry.row.updated_at,true)}</time> · ICT</dd><dt>{t('Trading date ·')}</dt><dd>{date(entry.row.trading_date)} · {sessionText(entry.row.session)}</dd><dt>{t('Price')}</dt><dd>{number(entry.row.last_price)} VND</dd><dt>{t('Reference price')}</dt><dd>{number(entry.row.reference_price)} VND</dd><dt>{t('Price change')}</dt><dd>{signed(entry.row.change)} VND</dd></dl>:<p>{loading?t('Loading observed quotes…'):unknownCoverage?t('Quote coverage unavailable'):t('No observed quote or timestamp is available.')}</p>}
      <Dialog.Close className="quote-dialog-close" aria-label={t('Close quote source')}><X size={18}/></Dialog.Close>
    </Dialog.Content></Dialog.Portal></Dialog.Root>
  </section>;
}
export default function QuoteMap(props:Props){const {data,failed}=useLivePrices();return <QuoteMapView {...props} mode={props.mode??(props.scope==='watchlist'?'heatmap':'board')} data={data} failed={failed}/>;}
