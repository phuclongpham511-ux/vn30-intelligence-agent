import type { Security } from './types.ts';
const fold = (value: string) => value.normalize('NFKD').replace(/\p{M}/gu, '').replace(/[đĐ]/g, 'd').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
export function browseSecurities(stocks: Security[], q = '', exchange = '', page = 0, size = 10, members?: string[]) {
  const query = fold(q);
  const matches = stocks.filter(stock => (!exchange || stock.exchange === exchange) && (!members || members.includes(stock.symbol)) && fold([stock.symbol, stock.display_name_en, stock.company_name].filter(Boolean).join(' ')).includes(query));
  return { items: matches.slice(page * size, (page + 1) * size), total: matches.length };
}
export type IndexGroups = { groups: Record<string,string[]>; status: string; last_synced_at?: string | null; source: string };
type UniversePage = { items: Security[]; total: number; status: string; last_synced_at?: string | null; index_groups?: IndexGroups };
export async function loadUniverse(fetcher: typeof fetch = fetch, signal?: AbortSignal) {
  const stocks: Security[] = [];
  let metadata: UniversePage;
  do {
    const response = await fetcher(`/api/stocks/universe?limit=500&offset=${stocks.length}`, { signal });
    if (!response.ok) throw new Error('Equity universe unavailable');
    metadata = await response.json();
    if (!Array.isArray(metadata.items) || metadata.total > 30000 || (stocks.length < metadata.total && !metadata.items.length)) throw new Error('Incomplete equity universe');
    stocks.push(...metadata.items);
  } while (stocks.length < metadata.total);
  return { stocks, status: metadata.status, lastSynced: metadata.last_synced_at || null, groups: metadata.index_groups || {groups:{},status:"not_attempted",source:"SSI:FastConnect"} };
}

export const recentSearchKey = 'vn30.recent-equity-searches.v1';
export function readRecentSearches(raw: string | null): string[] {
  try { const rows = JSON.parse(raw || '[]'); return Array.isArray(rows) ? [...new Set(rows.filter((s: unknown): s is string => typeof s === 'string' && /^[A-Z0-9]{1,20}$/.test(s)))].slice(0,5) : []; } catch { return []; }
}
export function rememberSearch(rows: string[], symbol: string) { return [symbol, ...rows.filter(s=>s!==symbol)].slice(0,5); }
export function stockSuggestions(stocks: Security[], query: string, recent: string[]) {
  return query.trim() ? browseSecurities(stocks,query,'',0,6).items : recent.map(symbol=>stocks.find(s=>s.symbol===symbol)).filter((s): s is Security=>!!s).slice(0,5);
}
