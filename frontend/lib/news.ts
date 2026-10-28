export type NewsArticle = {
  id: string; title: string; url: string; source_name: string; published_at: string | null;
  first_seen_at: string; last_seen_at?:string; topics: string[]; tickers: string[]; sectors: string[];
  thumbnail_url?: string | null; thumbnail_provenance?: string | null;
};
export type TickerAssociation = {
  symbol:string; article_id:string; article_title:string; article_url?:string|null;
  kind:'issuer_identity'|'explicit_stock'|'issuer_activity'; matched_text:string; policy:string;
  evidence_origin?:'headline'|'publisher_text'; evidence_excerpt?:string|null; text_receipt_id?:string|null; text_hash?:string|null; text_observed_at?:string|null;
};
export type NewsSource = {
  source_id: string; name: string; country: string; category: "VN" | "GLOBAL";
  enabled: boolean; poll_interval_minutes: number;
  status: "healthy" | "stale" | "error" | "not_attempted" | "disabled";
  last_attempt_at: string | null; last_success_at: string | null;
  last_error: string | null; articles_received: number | null;
};
export type NewsFilters = { ticker: string; sector: string; country: string; source: string; topic: string };
export const emptyNewsFilters: NewsFilters = { ticker: "", sector: "", country: "", source: "", topic: "" };
export type NewsView = "company" | "industry" | "briefing" | "community";
export const newsSectionLabels = {industry: 'Industry', company: 'Company', briefing: 'Market', community: 'Community Pulse'};
export function readNewsView(search: string): { view: NewsView } {
  const value = new URLSearchParams(search).get("view");
  const view = value === 'company' || value === 'briefing' || value === 'community' ? value : 'industry';
  return { view };
}
export function readCommunityWindow(search: string): 'today' | 'last24h' {
  return new URLSearchParams(search).get('window') === 'last24h' ? 'last24h' : 'today';
}
export function newsViewQuery(filters: NewsFilters, view: NewsView, communityWindow: 'today' | 'last24h' = 'today'): string {
  const params = new URLSearchParams(newsQuery(filters));
  const canonical = readNewsView(`view=${view}`).view;
  if (canonical !== 'industry') params.set("view", canonical);
  if (canonical === 'community' && communityWindow === 'last24h') params.set('window', communityWindow);
  return params.toString();
}
export function readNewsFilters(search: string): NewsFilters {
  const params = new URLSearchParams(search);
  return Object.fromEntries(Object.keys(emptyNewsFilters).map(key => [key, (params.get(key) || "").trim()])) as NewsFilters;
}
export function newsQuery(filters: NewsFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    const text = value.trim();
    if (text) params.set(key, key === "ticker" ? text.toUpperCase() : text);
  }
  return params.toString();
}
// Promotion deduplicates only its own list; category archives keep their stories.
export function uniqueHotTopics<T extends {story:{id:string}}>(rows:T[]):T[] {
  const seen=new Set<string>();
  return rows.filter(row=>{if(seen.has(row.story.id))return false;seen.add(row.story.id);return true;});
}
