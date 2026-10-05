export type NewsArticle = {
  id: string; title: string; url: string; source_name: string; published_at: string | null;
  first_seen_at: string; topics: string[]; tickers: string[]; sectors: string[];
  thumbnail_url?: string | null; thumbnail_provenance?: string | null;
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
export type NewsView = "briefing" | "latest" | "global" | "community";
export function readNewsView(search: string): { view: NewsView; financialOnly: boolean } {
  const params = new URLSearchParams(search);
  const view = params.get("view");
  return { view: view === "latest" || view === "global" || view === "community" ? view : "briefing", financialOnly: params.get("financial_only") !== "false" };
}
export function newsViewQuery(filters: NewsFilters, view: NewsView, financialOnly: boolean): string {
  const params = new URLSearchParams(newsQuery(filters));
  params.set("financial_only", String(financialOnly));
  if (view !== "briefing") params.set("view", view);
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
