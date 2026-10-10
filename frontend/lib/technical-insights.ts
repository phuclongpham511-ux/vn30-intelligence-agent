// Presentation only: preserve the server's D5 order, decisions and original evidence.
export type TechnicalInsight = {
  event_id: string; event_type: string; ticker: string; trading_session: string;
  eligible: true; is_fixture: false; direction: string;
  evidence: Record<string, unknown>[]; evidence_refs: string[];
};
export type OperationalPacket = {
  kind: "provisional_packet"; assurance: "PROVISIONAL"; safe_to_display_as_verified: false;
  snapshot_id: string; snapshot_version: number; persisted_at: string;
  last_checked_at: string; next_check_due_at: string; freshness: "FRESH" | "STALE";
  packet: { ticker: string; trading_session: string; packet_id: string; generated_at: string;
    packet_state: "HAS_INSIGHTS" | "NO_MEANINGFUL_TECHNICAL_CHANGE" | "TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE";
    top_insights: TechnicalInsight[]; family_checks: Record<string, unknown>[];
    limitations: string[]; data_provenance: Record<string, unknown> };
};
export type TechnicalDiagnostic = {
  kind: "diagnostic"; ticker: string; requested_session: string | null;
  readiness_status: string; reason_codes: string[]; safe_to_display_as_verified: false;
};
export type TechnicalResponse = OperationalPacket | TechnicalDiagnostic;
const record = (value: unknown): value is Record<string, unknown> => !!value && typeof value === "object" && !Array.isArray(value);
const strings = (value: unknown): value is string[] => Array.isArray(value) && value.every(v => typeof v === "string");
const session = (value: unknown): value is string => typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0,10) === value;
const timestamp = (value: unknown): value is string => typeof value === "string" && /(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value));

export function parseTechnicalResponse(value: unknown, ticker: string): TechnicalResponse {
  const invalid = () => { throw new Error("Invalid operational Technical response"); };
  if (!record(value) || value.safe_to_display_as_verified !== false) return invalid();
  if (value.kind === "diagnostic") {
    if (value.ticker !== ticker || !(value.requested_session === null || session(value.requested_session))
      || typeof value.readiness_status !== "string" || !strings(value.reason_codes)) return invalid();
    return value as TechnicalDiagnostic;
  }
  const p = value.packet;
  if (value.kind !== "provisional_packet" || value.assurance !== "PROVISIONAL"
    || typeof value.snapshot_id !== "string" || !value.snapshot_id || !Number.isInteger(value.snapshot_version) || Number(value.snapshot_version) < 1
    || !timestamp(value.persisted_at) || !timestamp(value.last_checked_at) || !timestamp(value.next_check_due_at)
    || !["FRESH", "STALE"].includes(String(value.freshness)) || !record(p) || p.ticker !== ticker
    || !session(p.trading_session) || !timestamp(p.generated_at) || typeof p.packet_id !== "string"
    || !record(p.data_provenance) || p.data_provenance.completion_assurance !== "PROVISIONAL"
    || !Array.isArray(p.family_checks) || !p.family_checks.every(record) || !strings(p.limitations)
    || !["HAS_INSIGHTS", "NO_MEANINGFUL_TECHNICAL_CHANGE", "TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE"].includes(String(p.packet_state))
    || !Array.isArray(p.top_insights)) return invalid();
  const seen = new Set();
  for (const e of p.top_insights) {
    if (!record(e) || typeof e.event_id !== "string" || !e.event_id || seen.has(e.event_id)
      || typeof e.event_type !== "string" || typeof e.direction !== "string"
      || e.ticker !== ticker || e.trading_session !== p.trading_session || e.eligible !== true || e.is_fixture !== false
      || !Array.isArray(e.evidence) || !e.evidence.every(record) || !strings(e.evidence_refs)) return invalid();
    seen.add(e.event_id);
  }
  if ((p.packet_state === "HAS_INSIGHTS" && p.top_insights.length === 0)
    || (p.packet_state !== "HAS_INSIGHTS" && p.top_insights.length !== 0)) return invalid();
  return value as OperationalPacket;
}
export async function loadTechnical(ticker: string, signal: AbortSignal, fetcher: typeof fetch = fetch) {
  signal.throwIfAborted();
  const response = await fetcher("/api/technical/" + encodeURIComponent(ticker) + "/daily/operational/latest",
    { cache: "no-store", signal: AbortSignal.any([signal, AbortSignal.timeout(12000)]) });
  if (!response.ok) throw new Error("Technical API unavailable");
  const value: unknown = await response.json();
  signal.throwIfAborted();
  return parseTechnicalResponse(value, ticker);
}
