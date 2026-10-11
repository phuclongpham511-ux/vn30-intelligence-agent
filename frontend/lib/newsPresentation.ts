import type {LiveItem} from './live-market.ts';

type Story={representative_article:{tickers:string[]}};
export const relatedTickers=(item:Story)=>[...new Set(item.representative_article.tickers)].slice(0,3);
// One page-scoped demand lease, never one quote request per article.
export const newsSymbols=(items:Story[])=>[...new Set(items.flatMap(relatedTickers))].sort().slice(0,50);
export function quoteStatus(item:LiveItem|undefined,failed=false,now=new Date()) {
  const row=item?.snapshot;
  if(!row||item?.status==='unavailable')return 'unavailable';
  const updated=Date.parse(row.updated_at);
  const day=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Ho_Chi_Minh',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);
  return failed||item.status==='stale'||row.trading_date!==day||!Number.isFinite(updated)||updated>now.getTime()+5000||
    (row.session==='active'||row.session==='unknown')&&now.getTime()-updated>120000?'stale':'fresh';
}
