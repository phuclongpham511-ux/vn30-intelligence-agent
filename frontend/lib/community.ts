import { safeExternalUrl } from "./presentation.ts";

export type CommunitySource = {
  source_id: string; name: string; url: string;
  status: "healthy" | "stale" | "error" | "not_attempted";
  poll_interval_minutes: number; last_attempt_at: string | null;
  last_success_at: string | null; last_error: string | null; threads_received: number | null;
};
export type CommunityThread = CommunityPulseData["threads"][number];
export type CommunityUpdate = { symbol: string; data: CommunityPulseData | null };

export function communitySourceMessage(status: CommunitySource["status"]): string {
  return {
    healthy: "A bounded public listing sample observed in the last 72 hours; coverage is incomplete.",
    stale: "The source has not been checked recently. Stored discussions may be stale.",
    error: "The latest source acquisition failed. Stored discussions may be shown; coverage is incomplete.",
    not_attempted: "This source has not been checked yet. Discussion coverage is unknown.",
  }[status];
}

export function communityEvidence(thread: Pick<CommunityThread, "url" | "replies" | "views" | "activity_at" | "last_seen_at">) {
  return { url: safeExternalUrl(thread.url),
    replies: thread.replies == null ? "Replies unavailable" : `${thread.replies.toLocaleString("en-GB")} replies`,
    views: thread.views == null ? "Views unavailable" : `${thread.views.toLocaleString("en-GB")} views`,
    timeLabel: thread.activity_at ? "Last public activity" : "Observed",
    time: thread.activity_at || thread.last_seen_at };
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
export type CommunityPulseData = {
  as_of: string; sampled_threads: number;
  source: CommunitySource & { id: string };
  most_discussed: { ticker: string; thread_count: number }[];
  topics: { topic: string; thread_count: number }[];
  threads: { id: string; title: string; url: string; author: string | null; published_at: string | null; activity_at: string | null; last_seen_at: string; tickers: string[]; topics: string[]; replies: number | null; views: number | null }[];
};

export async function loadCommunity(ticker: string, topic: string, signal?: AbortSignal): Promise<CommunityPulseData> {
  const query = new URLSearchParams();
  if (ticker.trim()) query.set("ticker", ticker.trim().toUpperCase());
  if (topic.trim()) query.set("topic", topic.trim());
  const response = await fetch(`/api/community/pulse?${query}`, { cache: "no-store", signal });
  if (!response.ok) throw new Error("Community unavailable");
  return response.json();
}
