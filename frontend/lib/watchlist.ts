import type { NewsArticle } from "./news.ts";

export const watchlistStorageKey = "vn30.watchlist.v1";
export type WatchlistState = { symbols: string[]; seen: Record<string, string[]> };
export type Development = {
  story_id: string; title: string; first_seen_at: string; published_at: string | null;
  source_count: number; articles: NewsArticle[];
};
export type MonitoredStock = { symbol: string; status: "ready" | "unavailable"; developments: Development[] | null };
export type WatchlistUpdates = { as_of: string; window_start: string; stocks: MonitoredStock[] };
export const emptyWatchlist = (): WatchlistState => ({ symbols: [], seen: {} });

export function readWatchlist(raw: string | null): WatchlistState {
  if (raw === null) return emptyWatchlist();
  const value = JSON.parse(raw);
  if (!value || !Array.isArray(value.symbols) || value.symbols.length > 50 ||
    !value.symbols.every((symbol: unknown) => typeof symbol === "string" && /^[A-Z0-9]{1,20}$/.test(symbol)) ||
    !value.seen || typeof value.seen !== "object" || Array.isArray(value.seen) ||
    !Object.values(value.seen).every(ids => Array.isArray(ids) && ids.every(id => typeof id === "string"))) {
    throw new Error("Saved Watchlist is unavailable");
  }
  return { symbols: [...new Set<string>(value.symbols)], seen: value.seen };
}

export function followStock(state: WatchlistState, symbol: string): WatchlistState {
  if (!/^[A-Z0-9]{1,20}$/.test(symbol) || state.symbols.length >= 50) throw new Error("Invalid stock");
  return { ...state, symbols: [...new Set([...state.symbols, symbol])] };
}
export function unfollowStock(state: WatchlistState, symbol: string): WatchlistState {
  const seen = { ...state.seen }; delete seen[symbol];
  return { symbols: state.symbols.filter(value => value !== symbol), seen };
}
export function unreviewedStories(developments: Development[], seen: string[] = []): string[] {
  const reviewed = new Set(seen);
  return [...new Set(developments.map(row => row.story_id))].filter(id => !reviewed.has(id));
}
export function markReviewed(state: WatchlistState, symbol: string, developments: Development[]): WatchlistState {
  return { ...state, seen: { ...state.seen, [symbol]: [...new Set(developments.map(row => row.story_id))] } };
}

export async function loadWatchlistUpdates(symbols: string[], signal?: AbortSignal, request: typeof fetch = fetch): Promise<WatchlistUpdates> {
  const response = await request("/api/watchlists/monitoring", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbols }), signal, cache: "no-store",
  });
  if (!response.ok) throw new Error("Watchlist updates unavailable");
  return response.json();
}
