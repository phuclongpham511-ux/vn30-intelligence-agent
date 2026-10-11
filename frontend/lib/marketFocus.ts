import type {NewsArticle,TickerAssociation} from './news.ts';
import {qualifiedAssociations} from './newsPresentation.ts';
type Item={story:{id:string};representative_article:NewsArticle;research_category?:string|null;ticker_associations?:TickerAssociation[]};
// A bounded discovery list, ordered by documented publication. No sentiment or
// importance score. Company highlights require a qualified issuer association.
export function marketFocusItems<T extends Item>(rows:T[],limit=3):T[]{
  const seen=new Set<string>();
  return rows.filter(row=>{
    if(seen.has(row.story.id))return false;
    if(row.research_category!=='MARKET_BRIEF'&&(row.research_category!=='COMPANY'||!qualifiedAssociations(row.representative_article,row.ticker_associations).length))return false;
    seen.add(row.story.id);return true;
  }).sort((a,b)=>Date.parse(b.representative_article.published_at||b.representative_article.first_seen_at)-Date.parse(a.representative_article.published_at||a.representative_article.first_seen_at)||a.story.id.localeCompare(b.story.id)).slice(0,limit);
}
