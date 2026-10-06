export type CommunitySource = {
  source_id: string; name: string; url: string;
  status: "healthy" | "stale" | "error" | "not_attempted";
  poll_interval_minutes: number; last_attempt_at: string | null;
  last_success_at: string | null; last_error: string | null; threads_received: number | null;
};
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
