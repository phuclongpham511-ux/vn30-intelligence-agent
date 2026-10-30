import type {Intelligence,AttentionUpdate,WatchlistState} from './watchlist.ts';
import {isUnread,uniqueUpdates} from './watchlist.ts';
import {qualifiedAssociations} from './newsPresentation.ts';
import type {NewsArticle,TickerAssociation} from './news.ts';
import type {CommunityItem} from './community.ts';
import {actionUrl} from './stock-detail.ts';
import type {CollectionStatus} from './collectionStatus.ts';

export type ResearchEntry={item:AttentionUpdate;url:string;source:string;sourceStatus:CollectionStatus|'unknown';
  published:string|null;observed:string|null;updated:string|null;unread:boolean|null;corrected:boolean;
  relevance:'Explicit ticker evidence'|'Issuer-context evidence'|'Stored ticker match; detailed proof unavailable'|'Community ticker association';
  articles:NewsArticle[];proofs:TickerAssociation[];discussion:CommunityItem|null;topics:string[]};
const validTime=(value:unknown):value is string=>typeof value==='string'&&/(?:Z|[+-]\d{2}:\d{2})$/.test(value)&&Number.isFinite(Date.parse(value));

/** View projection only. Server-owned 72h/24h windows and identity revisions stay intact. */
export function stockResearch(data:Intelligence,ticker:string,state:WatchlistState|null) {
  if(data.stocks.length!==1||data.stocks[0].symbol!==ticker||!validTime(data.as_of))throw new Error('Wrong stock research ownership');
  const row=data.stocks[0],following=state?.symbols.includes(ticker)===true;
  let omitted=false;
  const entries=(kind:'news'|'community'):ResearchEntry[]=>uniqueUpdates(row[kind]?.items||[]).flatMap((item):ResearchEntry[]=>{
    const url=actionUrl(item.url);
    if(item.kind!==kind||!url||!validTime(item.occurred_at)||Date.parse(item.occurred_at)>Date.parse(data.as_of)){omitted=true;return [];}
    const articles=kind==='news'&&Array.isArray(item.evidence)?item.evidence as NewsArticle[]:[];
    const discussion=kind==='community'?item.evidence as CommunityItem:null;
    const article=articles[0];
    if(kind==='news'&&(!article||article.title!==item.title||actionUrl(article.url)!==url||!Array.isArray(article.tickers)||!article.tickers.includes(ticker))||
       discussion&&(!Array.isArray(discussion.tickers)||!discussion.tickers.includes(ticker)||discussion.id!==item.entity_id||actionUrl(discussion.url)!==url)){
      omitted=true;return [];
    }
    if(kind==='community'&&!discussion){omitted=true;return [];}
    const published=article?.published_at??discussion?.published_at??null;
    const observed=article?.first_seen_at??discussion?.first_seen_at??null;
    if(observed!==null&&(!validTime(observed)||Date.parse(observed)>Date.parse(data.as_of))||published!==null&&(!validTime(published)||Date.parse(published)>Date.parse(data.as_of))){omitted=true;return [];}
    const source=article?data.news_sources.find(s=>s.name===article.source_name):data.community_sources.find(s=>s.source_id===discussion?.source_id);
    const proofs=article?qualifiedAssociations(article,item.ticker_associations).filter(proof=>proof.symbol===ticker&&(!proof.text_observed_at||Date.parse(proof.text_observed_at)<=Date.parse(data.as_of))):[];
    const unread=following&&state?isUnread(state,ticker,item):null;
    const updated=article?.last_seen_at??discussion?.last_seen_at??null;
    return [{item,url,source:source?.name||article?.source_name||discussion?.source_id||'Unavailable',sourceStatus:source?.status||'unknown',
      published,observed,updated:validTime(updated)&&Date.parse(updated)<=Date.parse(data.as_of)?updated:null,
      unread,corrected:unread===true&&!!state?.receipts?.[ticker]?.[item.id],
      relevance:discussion?'Community ticker association':proofs.some(proof=>proof.kind==='explicit_stock')?'Explicit ticker evidence':proofs.length?'Issuer-context evidence':'Stored ticker match; detailed proof unavailable',
      articles,proofs,discussion,topics:[...new Set(articles.flatMap(a=>Array.isArray(a.topics)?a.topics:[]))]}];
  }).sort((a,b)=>Number(b.unread===true)-Number(a.unread===true)||Date.parse(b.published||b.observed||b.item.occurred_at)-Date.parse(a.published||a.observed||a.item.occurred_at)||a.item.id.localeCompare(b.item.id));
  const news=entries('news'),community=entries('community');
  const grouped=new Set<string>(),communityGroups:ResearchEntry[][]=[];
  for(const ids of row.community?.display_groups||[]){
    if(!Array.isArray(ids)){omitted=true;continue;}
    const members=community.filter(entry=>ids.includes(entry.item.entity_id)&&!grouped.has(entry.item.entity_id));
    members.forEach(entry=>grouped.add(entry.item.entity_id));if(members.length)communityGroups.push(members);
  }
  community.filter(entry=>!grouped.has(entry.item.entity_id)).forEach(entry=>communityGroups.push([entry]));
  communityGroups.sort((a,b)=>community.indexOf(a[0])-community.indexOf(b[0]));
  return {news,community,communityGroups,following,unavailable:row.status!=='ready',omitted,
    incomplete:omitted||!!row.news?.has_more||!!row.news?.truncated||!!row.community?.has_more||!!row.community?.truncated};
}
