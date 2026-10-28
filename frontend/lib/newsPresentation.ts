import type {LiveItem} from './live-market.ts';
import type {TickerAssociation} from './news.ts';

type Article={id:string;title:string;tickers:string[];url?:string};
type Story={representative_article:Article;ticker_associations?:TickerAssociation[]};
export function qualifiedAssociations(article:Article,associations:TickerAssociation[]=[]){
  return associations.filter(a=>a.policy==='issuer-context-v2'&&a.article_id===article.id&&a.article_title===article.title&&
    (!a.article_url||a.article_url===article.url)&&
    (a.evidence_origin!=='publisher_text'||!!(a.article_url&&a.text_receipt_id&&a.text_hash&&a.evidence_excerpt&&a.text_observed_at&&Number.isFinite(Date.parse(a.text_observed_at))))&&
    ['issuer_identity','explicit_stock','issuer_activity'].includes(a.kind)&&a.matched_text.trim()&&article.tickers.includes(a.symbol));
}
export const allRelatedTickers=(item:Story)=>[...new Set(qualifiedAssociations(item.representative_article,item.ticker_associations).map(a=>a.symbol))];
export const relatedTickers=(item:Story)=>allRelatedTickers(item).slice(0,3);
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
