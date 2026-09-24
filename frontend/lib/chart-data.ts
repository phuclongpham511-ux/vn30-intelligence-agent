import type { TechnicalBar } from "./types.ts";

export const RANGES = { "3M": 90, "6M": 180, "1Y": 365, "2Y": 730 } as const;
export type Range = keyof typeof RANGES;
export function rangeDates(range: Range, end = new Date()): { start: string; end: string } {
  // Match the Vietnam trading calendar, independent of the browser's timezone.
  const day = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Ho_Chi_Minh", year: "numeric", month: "2-digit", day: "2-digit" }).format(end);
  const start = new Date(day + "T00:00:00Z");
  start.setUTCDate(start.getUTCDate() - RANGES[range]);
  return { start: start.toISOString().slice(0, 10), end: day };
}
export function technicalSeries(rows: TechnicalBar[], up: string, down: string) {
  const ordered = [...rows].sort((a, b) => a.date.localeCompare(b.date));
  return {
    ma20: ordered.filter(row => row.ma20 != null).map(row => ({ time: row.date, value: row.ma20! })),
    ma50: ordered.filter(row => row.ma50 != null).map(row => ({ time: row.date, value: row.ma50! })),
    rsi14: ordered.filter(row => row.rsi14 != null).map(row => ({ time: row.date, value: row.rsi14! })),
    candles: ordered.map(({ date: time, open, high, low, close }) => ({ time, open, high, low, close })),
    volume: ordered.map(row => ({ time: row.date, value: row.volume, color: row.close >= row.open ? up : down })),
  };
}
