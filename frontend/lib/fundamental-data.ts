import type { FundamentalPeriod } from "./types.ts";
export const FINANCIAL_LABELS = {
  revenue: "Revenue", net_profit: "Profit after tax",
  revenue_growth_yoy: "Revenue YoY", net_profit_growth_yoy: "Profit after tax YoY",
  gross_margin: "Gross Margin", net_margin: "Net Margin", roe: "ROE",
  operating_income:'Operating income', operating_income_growth_yoy:'Operating income YoY',
  profit_parent:'Parent-shareholder profit',total_assets:'Total assets',equity:'Total equity',total_liabilities:'Total liabilities',
  cash_operating:'Operating cash flow',cash_investing:'Investing cash flow',cash_financing:'Financing cash flow',free_cash_flow:'Free cash flow',
  eps_reported:'Reported basic EPS',roa:'ROA',debt_equity:'Debt / equity',liabilities_assets:'Liabilities / assets',
  current_ratio:'Current ratio',quick_ratio:'Quick ratio',cash_conversion:'Operating cash flow / profit',
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
