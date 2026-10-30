import type {LiveItem} from './live-market.ts';
import type {TickerAssociation} from './news.ts';

// Preserve the paginated backend order; discussions never enter editorial rows.
export function editorialStories<T extends {story:{id:string};research_category?:string|null}>(rows:T[]):T[] {
  const seen=new Set<string>();
  return rows.filter(row=>{
    if(!row.story?.id||!['COMPANY','INDUSTRY','MARKET_BRIEF'].includes(row.research_category||'')||seen.has(row.story.id))return false;
    seen.add(row.story.id);return true;
  });
}
type DatedArticle={published_at:string|null;first_seen_at:string};
export function newsArticleTime(article:DatedArticle):{kind:'Published'|'First seen';value:string|null} {
  if(article.published_at&&Number.isFinite(Date.parse(article.published_at)))return {kind:'Published',value:article.published_at};
  return {kind:'First seen',value:Number.isFinite(Date.parse(article.first_seen_at))?article.first_seen_at:null};
}
// Same clock as the archive: latest publication, or first seen when unavailable.
// last_seen_at is a source recheck, never a new publication.
export function latestReporting(item:{representative_article:DatedArticle;articles:DatedArticle[]}) {
  return [item.representative_article,...item.articles].map(newsArticleTime).reduce((latest,next)=>
    next.value&&(!latest.value||Date.parse(next.value)>Date.parse(latest.value))?next:latest,newsArticleTime(item.representative_article));
}

type Article={id:string;title:string;tickers:string[];url?:string};
type Story={representative_article:Article;articles?:Article[];ticker_associations?:TickerAssociation[]};
export function qualifiedAssociations(article:Article,associations:TickerAssociation[]=[]){
  return associations.filter(a=>a.policy==='issuer-context-v2'&&a.article_id===article.id&&a.article_title===article.title&&
    (!a.article_url||a.article_url===article.url)&&
    (a.evidence_origin!=='publisher_text'||!!(a.article_url&&a.text_receipt_id&&a.text_hash&&a.evidence_excerpt&&a.text_observed_at&&Number.isFinite(Date.parse(a.text_observed_at))))&&
    ['issuer_identity','explicit_stock','issuer_activity'].includes(a.kind)&&a.matched_text.trim()&&article.tickers.includes(a.symbol));
}
export const allRelatedTickers=(item:Story)=>{
  const members=new Map((item.articles||[]).map(article=>[article.id,article]));
  members.set(item.representative_article.id,item.representative_article);
  return [...new Set([...members.values()].flatMap(article=>qualifiedAssociations(article,item.ticker_associations).map(proof=>proof.symbol)))];
};
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
