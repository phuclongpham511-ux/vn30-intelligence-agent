/** Never infer English from raw names, ASCII spelling, or ticker-specific branches. */
export function englishCompanyName(stock: { display_name_en?: string | null; company_name?: string | null }): string | null {
  return stock.display_name_en?.trim() || null;
}
export function formatNumber(value: unknown, decimals = 2): string {
  return typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat("en-US", { maximumFractionDigits: decimals }).format(value) : "—";
}
export function formatPercent(value: unknown, signed = false): string {
  return typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 2, signDisplay: signed ? "exceptZero" : "auto" }).format(value) : "—";
}
export function formatDate(value: string | null, short = false): string {
  if (!value) return "Unavailable";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "Unavailable" : new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", ...(short ? {} : { year: "numeric" }), timeZone: "UTC" }).format(date);
}
export function direction(value: unknown): string {
  return typeof value === "number" ? value > 0 ? "positive" : value < 0 ? "negative" : "" : "";
}
export function safeExternalUrl(value: string | null): string | null {
  if (!value) return null;
  try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) ? url.href : null; } catch { return null; }
}
