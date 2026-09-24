import type { FundamentalPeriod } from "./types.ts";
export const FINANCIAL_LABELS = {
  revenue: "Revenue", net_profit: "Net Profit",
  revenue_growth_yoy: "Revenue YoY", net_profit_growth_yoy: "Net Profit YoY",
  gross_margin: "Gross Margin", net_margin: "Net Margin", roe: "ROE",
} as const;
export type FinancialKey = keyof typeof FINANCIAL_LABELS;
export function annualChartData(rows: FundamentalPeriod[]): FundamentalPeriod[] {
  return rows.filter(row => /^\d{4}$/.test(row.period)).map(row => ({...row})).sort((a,b) => a.period.localeCompare(b.period));
}
export function availableSeries(rows: FundamentalPeriod[], keys: readonly FinancialKey[]): FinancialKey[] {
  return keys.filter(key => rows.some(row => typeof row[key] === "number" && Number.isFinite(row[key])));
}
export function compactVnd(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat("en-US", {notation:"compact",maximumFractionDigits:1}).format(value) : "—";
}
