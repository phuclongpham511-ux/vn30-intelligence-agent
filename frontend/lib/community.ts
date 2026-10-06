import { safeExternalUrl } from "./presentation.ts";

export type CommunitySource = {
  source_id: string; name: string; url: string; enabled: boolean; qualification: string; reason: string | null; items_received: number | null;
  status: "healthy" | "stale" | "error" | "not_attempted" | "disabled";
  poll_interval_minutes: number; last_attempt_at: string | null;
  last_success_at: string | null; last_error: string | null; threads_received: number | null;
};
export type CommunityThread = CommunityItem;
export type CommunityUpdate = { symbol: string; data: CommunityPulseData | null };

export function communityTime(value: string | null): string {
  if (!value || !Number.isFinite(Date.parse(value))) return "Unavailable";
  return new Date(value).toLocaleString("en-GB", { timeZone: "Asia/Ho_Chi_Minh" });
}

export function communitySourceMessage(status: CommunitySource["status"]): string {
  return {
    healthy: "A bounded same-day public discussion sample; coverage is incomplete.",
    stale: "The source has not been checked recently. Stored discussions may be stale.",
    error: "The latest source acquisition failed. Stored discussions may be shown; coverage is incomplete.",
    disabled: "This source is deferred; no verified public discussion acquisition is available.",
    not_attempted: "This source has not been checked yet. Discussion coverage is unknown.",
  }[status];
}

export function communityEvidence(thread: Pick<CommunityThread, "url" | "replies" | "views" | "published_at">) {
  return { url: safeExternalUrl(thread.url),
    replies: thread.replies == null ? "Replies unavailable" : `${thread.replies.toLocaleString("en-GB")} replies`,
    views: thread.views == null ? "Views unavailable" : `${thread.views.toLocaleString("en-GB")} views`,
    timeLabel: "Published", time: thread.published_at };
}

export async function loadCommunityUpdates(symbols: string[], signal?: AbortSignal,
  request: typeof loadCommunity = loadCommunity): Promise<CommunityUpdate[]> {
  const output: CommunityUpdate[] = [];
  // Reuse the ticker-filtered persisted read API with bounded client concurrency.
  for (let index = 0; index < symbols.length; index += 4) {
    if (signal?.aborted) throw new DOMException("Aborted", "AbortError");
    output.push(...await Promise.all(symbols.slice(index, index + 4).map(async symbol => {
      try { return { symbol, data: await request(symbol, "", signal) }; }
      catch { return { symbol, data: null }; }
    })));
  }
  return output;
}
export type CommunityItem = {
  id: string; revision_id: string; source_id: string; source_item_id: string; item_type: string;
  title: string | null; excerpt: string; url: string; author: string | null;
  published_at: string; last_seen_at: string; tickers: string[];
  replies: number | null; views: number | null; is_fixture: boolean;
};
export type CommunityPulseData = {
  as_of: string; sampled_items: number; unique_items: number; truncated: boolean; coverage_partial: boolean;
  window: { kind: "today" | "last24h"; label: string; timezone: string; start: string; end: string };
  sources: CommunitySource[]; items: CommunityItem[];
  active_tickers: { ticker: string; item_count: number }[];
  themes: { id: string; label: string; keywords: string[]; summary: string; summary_kind: string;
    item_count: number; source_count: number; source_ids: string[]; latest_at: string;
    representative_id: string; evidence_ids: string[]; evidence_revisions: { id: string; revision_id: string }[] }[];
};

export async function loadCommunity(ticker: string, topic: string, signal?: AbortSignal, window: "today" | "last24h" = "today"): Promise<CommunityPulseData> {
  const query = new URLSearchParams();
  query.set("window", window);
  if (ticker.trim()) query.set("ticker", ticker.trim().toUpperCase());
  // Publisher topic filters do not constrain Community discussion themes.
  void topic;
  const response = await fetch(`/api/community/pulse?${query}`, { cache: "no-store", signal });
  if (!response.ok) throw new Error("Community unavailable");
  return response.json();
}
