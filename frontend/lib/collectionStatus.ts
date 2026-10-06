export type CollectionStatus = "healthy" | "stale" | "error" | "not_attempted" | "disabled";
export const collectionLabels: Record<CollectionStatus, string> = {
  healthy: "Healthy", stale: "Fetch overdue", error: "Last attempt failed",
  not_attempted: "Never checked", disabled: "Disabled",
};

export function fetchTime(value: string | null): string {
  if (!value || !Number.isFinite(Date.parse(value))) return "Unavailable";
  return new Date(value).toLocaleString("en-GB");
}

export function newsFreshness(sources: { enabled: boolean; status: CollectionStatus; last_success_at: string | null }[]) {
  const enabled = sources.filter(source => source.enabled);
  const successful = enabled.map(source => source.last_success_at)
    .filter((time): time is string => !!time && Number.isFinite(Date.parse(time)));
  const latest = successful.sort((a, b) => Date.parse(b) - Date.parse(a))[0] || null;
  return { healthy: enabled.filter(source => source.status === "healthy").length,
    enabled: enabled.length, lastSuccess: latest };
}
