import type { Security } from './types.ts';
const fold = (value: string) => value.normalize('NFKD').replace(/\p{M}/gu, '').replace(/[đĐ]/g, 'd').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
export function browseSecurities(stocks: Security[], q = '', exchange = '', page = 0, size = 24) {
  const query = fold(q);
  const matches = stocks.filter(stock => (!exchange || stock.exchange === exchange) && fold([stock.symbol, stock.display_name_en, stock.company_name].filter(Boolean).join(' ')).includes(query));
  return { items: matches.slice(page * size, (page + 1) * size), total: matches.length };
}
type UniversePage = { items: Security[]; total: number; status: string; last_synced_at?: string | null };
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
  return { stocks, status: metadata.status, lastSynced: metadata.last_synced_at || null };
}
