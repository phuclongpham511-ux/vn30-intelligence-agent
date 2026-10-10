import type { NewsArticle } from "./news.ts";
import {parseTechnicalResponse,type TechnicalResponse} from "./technical-insights.ts";
import type { NewsSource } from "./news.ts";
import type { CommunitySource } from "./community.ts";

export const watchlistStorageKey = "vn30.watchlist.v1";
export type ReviewReceipt = { revision: string; reviewed_at: string | null; members?:Record<string,string> };
export type WatchlistState = { symbols: string[]; seen: Record<string, string[]>; communitySeen: Record<string, string[]>;
  receipts?: Record<string, Record<string, ReviewReceipt>>; reviewedAt?: Record<string, string> };
export type Development = {
  story_id: string; title: string; first_seen_at: string; published_at: string | null;
  source_count: number; articles: NewsArticle[];
};
export type MonitoredStock = { symbol: string; status: "ready" | "unavailable"; developments: Development[] | null };
export type WatchlistUpdates = { as_of: string; window_start: string; stocks: MonitoredStock[] };
export const emptyWatchlist = (): WatchlistState => ({ symbols: [], seen: {}, communitySeen: {} });

function validReviewState(value: unknown): value is Record<string, string[]> {
  return !!value && typeof value === "object" && !Array.isArray(value) &&
    Object.values(value).every(ids => Array.isArray(ids) && ids.every(id => typeof id === "string"));
}

export function readWatchlist(raw: string | null): WatchlistState {
  if (raw === null) return emptyWatchlist();
  const value = JSON.parse(raw);
  if (!value || !Array.isArray(value.symbols) || value.symbols.length > 50 ||
    !value.symbols.every((symbol: unknown) => typeof symbol === "string" && /^[A-Z0-9]{1,20}$/.test(symbol)) ||
    !validReviewState(value.seen) ||
    (value.communitySeen !== undefined && !validReviewState(value.communitySeen))) {
    throw new Error("Saved Watchlist is unavailable");
  }
  if (value.receipts !== undefined && (!value.receipts || typeof value.receipts !== 'object' || Array.isArray(value.receipts) ||
    !Object.values(value.receipts).every(rows => !!rows && typeof rows === 'object' && !Array.isArray(rows) && Object.values(rows).every((row: unknown) => {
      const r = row as ReviewReceipt; return !!r && typeof r.revision === 'string' && (r.reviewed_at === null || validTime(r.reviewed_at)) &&
        (r.members===undefined || (!!r.members && typeof r.members==='object' && !Array.isArray(r.members) && Object.values(r.members).every(v=>typeof v==='string')));
    })))) throw new Error("Saved reviews are unavailable");
  if (value.reviewedAt !== undefined && (!value.reviewedAt || typeof value.reviewedAt !== 'object' || Array.isArray(value.reviewedAt) ||
    !Object.values(value.reviewedAt).every(validTime))) throw new Error("Saved review times are unavailable");
  return { symbols: [...new Set<string>(value.symbols)], seen: value.seen, communitySeen: value.communitySeen ?? {},
    ...(value.receipts ? {receipts:value.receipts} : {}), ...(value.reviewedAt ? {reviewedAt:value.reviewedAt} : {}) };
}

export function followStock(state: WatchlistState, symbol: string): WatchlistState {
  if (!/^[A-Z0-9]{1,20}$/.test(symbol) || state.symbols.length >= 50) throw new Error("Invalid stock");
  return { ...state, symbols: [...new Set([...state.symbols, symbol])] };
}
export function unfollowStock(state: WatchlistState, symbol: string): WatchlistState {
  const seen = { ...state.seen }; delete seen[symbol];
  const communitySeen = { ...state.communitySeen }; delete communitySeen[symbol];
  const receipts = {...state.receipts}; delete receipts[symbol];
  const reviewedAt = {...state.reviewedAt}; delete reviewedAt[symbol];
  return { symbols: state.symbols.filter(value => value !== symbol), seen, communitySeen,
    ...(Object.keys(receipts).length ? {receipts} : {}), ...(Object.keys(reviewedAt).length ? {reviewedAt} : {}) };
}
export function unreviewedThreads(threads: { id: string }[], seen: string[] = []): string[] {
  const reviewed = new Set(seen);
  return [...new Set(threads.map(row => row.id))].filter(id => !reviewed.has(id));
}
export function markCommunityReviewed(state: WatchlistState, symbol: string, threads: { id: string }[]): WatchlistState {
  return { ...state, communitySeen: { ...state.communitySeen,
    [symbol]: [...new Set([...(state.communitySeen[symbol] || []), ...threads.map(row => row.id)])] } };
}
export function unreviewedStories(developments: Development[], seen: string[] = []): string[] {
  const reviewed = new Set(seen);
  return [...new Set(developments.map(row => row.story_id))].filter(id => !reviewed.has(id));
}
export function markReviewed(state: WatchlistState, symbol: string, developments: Development[]): WatchlistState {
  return { ...state, seen: { ...state.seen, [symbol]: [...new Set([...(state.seen[symbol] || []), ...developments.map(row => row.story_id)])] } };
}

const validTime = (value: unknown): value is string => typeof value === 'string' && /(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value));
export type UpdateKind = 'news' | 'community' | 'technical';
export type AttentionUpdate = { id: string; entity_id: string; revision: string; kind: UpdateKind;
  title: string; occurred_at: string; url: string; source_count?: number; evidence: unknown; evidence_truncated?: boolean; revision_members?:Record<string,string> };
export type UpdatePage = {items: AttentionUpdate[]; has_more: boolean; truncated: boolean; window_start?: string};
export type IntelligentStock = {symbol:string; status:'ready'|'unavailable'; company_name:string|null; display_name_en:string|null; exchange:string|null;
  news:UpdatePage|null; community:UpdatePage|null; technical:(UpdatePage & {data:TechnicalResponse;waiting_for_gate?:boolean;awaiting_source_check?:boolean;next_check_due_at?:string|null;last_checked_at?:string|null})|null};
export type Intelligence = {as_of:string; offset:number; page_size:number; stocks:IntelligentStock[];
  news_sources:NewsSource[]; community_sources:CommunitySource[]};

export function technicalCountKnown(page:IntelligentStock['technical']):boolean {
  return page?.data.kind==='provisional_packet' && page.data.packet.packet_state!=='TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE';
}
export function parseIntelligence(value:unknown,symbols:string[],offset:number):Intelligence {
  const data=value as Intelligence;
  const invalid=()=>{throw new Error('Invalid Watchlist updates');};
  if(!data||!validTime(data.as_of)||data.offset!==offset||data.page_size!==12||!Array.isArray(data.stocks)||
    data.stocks.length!==symbols.length||!Array.isArray(data.news_sources)||!Array.isArray(data.community_sources))return invalid();
  for(let index=0;index<symbols.length;index++) {
    const row=data.stocks[index];
    if(row.symbol!==symbols[index]||!['ready','unavailable'].includes(row.status))return invalid();
    if(row.status==='unavailable') {if(row.news!==null||row.community!==null||row.technical!==null)return invalid();continue;}
    for(const kind of ['news','community','technical'] as const) {
      const page=row[kind];
      if(!page||!Array.isArray(page.items)||page.items.length>(kind==='technical'?3:12)||typeof page.has_more!=='boolean'||typeof page.truncated!=='boolean')return invalid();
      const seen=new Set<string>();
      for(const item of page.items) {
        if(item.kind!==kind||typeof item.entity_id!=='string'||!item.entity_id||item.id!==kind+':'+item.entity_id||
          seen.has(item.id)||typeof item.revision!=='string'||!item.revision||typeof item.title!=='string'||
          !validTime(item.occurred_at)||typeof item.url!=='string')return invalid();
        seen.add(item.id);
      }
    }
    const technical=row.technical!;
    technical.data=parseTechnicalResponse(technical.data,row.symbol);
    if((technical.waiting_for_gate||technical.awaiting_source_check)&&
      (technical.data.kind!=='diagnostic'||!validTime(technical.next_check_due_at)))return invalid();
    const events=technical.data.kind==='provisional_packet'?technical.data.packet.top_insights:[];
    if(events.length!==technical.items.length||events.some((event,index)=>event.event_id!==technical.items[index].entity_id||
      JSON.stringify(event)!==JSON.stringify(technical.items[index].evidence)))return invalid();
  }
  return data;
}

export function isUnread(state: WatchlistState, symbol: string, item: AttentionUpdate): boolean {
  const receipt = state.receipts?.[symbol]?.[item.id];
  // Story members already acknowledged provide the revision baseline. A new
  // publisher may become representative on a timestamp tie, without novelty.
  if(receipt?.members && item.revision_members) return Object.entries(receipt.members).some(([id,version])=>
    item.revision_members?.[id] !== undefined && item.revision_members[id] !== version);
  if (receipt) return receipt.revision !== item.revision || Object.entries(receipt.members || {}).some(([id,version])=>
    item.revision_members?.[id] !== undefined && item.revision_members[id] !== version);
  const legacy = item.kind === 'news' ? state.seen[symbol] : item.kind === 'community' ? state.communitySeen[symbol] : [];
  return !(legacy || []).includes(item.entity_id);
}
export function uniqueUpdates(items: AttentionUpdate[]) {
  return [...new Map(items.map(item => [item.id,item])).values()];
}
export function reviewUpdates(state: WatchlistState, symbol: string, items: AttentionUpdate[], at = new Date().toISOString()): WatchlistState {
  if (!validTime(at)) throw new Error('Invalid review time');
  const receipts = {...state.receipts?.[symbol]};
  for (const item of uniqueUpdates(items)) receipts[item.id] = {revision:item.revision, reviewed_at:at,
    ...(item.revision_members?{members:item.revision_members}:{})};
  return {...state, receipts:{...state.receipts,[symbol]:receipts}, reviewedAt:{...state.reviewedAt,[symbol]:at}};
}
// Upgrade only identities already explicitly reviewed in the legacy storage.
// This is a version baseline, not a review action; historical time stays unknown.
export function baselineLegacyReviews(state: WatchlistState, data: Intelligence): WatchlistState {
  let next = state;
  for (const row of data.stocks) for (const item of [...(row.news?.items || []), ...(row.community?.items || [])]) {
    if (!next.receipts?.[row.symbol]?.[item.id] && !isUnread(next,row.symbol,item)) next = {...next,
      receipts:{...next.receipts,[row.symbol]:{...next.receipts?.[row.symbol],[item.id]:{revision:item.revision,reviewed_at:null,
        ...(item.revision_members?{members:item.revision_members}:{})}}}};
  }
  return next;
}
export async function loadIntelligence(symbols:string[], offset=0, signal?:AbortSignal, request:typeof fetch=fetch):Promise<Intelligence> {
  const response = await request('/api/watchlists/intelligence', {method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({symbols,offset,page_size:12}),signal,cache:'no-store'});
  if (!response.ok) throw new Error('Watchlist updates unavailable');
  return parseIntelligence(await response.json(),symbols,offset);
}

export async function loadWatchlistUpdates(symbols: string[], signal?: AbortSignal, request: typeof fetch = fetch): Promise<WatchlistUpdates> {
  const response = await request("/api/watchlists/monitoring", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbols }), signal, cache: "no-store",
  });
  if (!response.ok) throw new Error("Watchlist updates unavailable");
  return response.json();
}
