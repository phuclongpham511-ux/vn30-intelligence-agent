import type { Fundamental } from "@/lib/types";
import MetricRow from "./MetricRow";
function pp(value: unknown) { return typeof value === "number" ? value * 100 : null; }
export default function FundamentalsCard({ data }: { data: Fundamental }) {
  return <section><div className="mb-4 flex flex-wrap items-center justify-between gap-2"><h2>Fundamentals</h2><span className="text-[10px] text-muted-foreground">Annual Â· {data.period || "Period unavailable"} Â· {data.source}</span></div>
    <div className="grid gap-4 xl:grid-cols-3">
      <div className="panel px-5 py-4"><h3 className="mb-2">Growth</h3><dl><MetricRow label="Revenue" value={data.revenue} suffix=" VND"/><MetricRow label="Revenue YoY" value={data.revenue_growth_yoy} percent signed/><MetricRow label="Net profit" value={data.net_profit} suffix=" VND"/><MetricRow label="Net profit YoY" value={data.net_profit_growth_yoy} percent signed/></dl></div>
      <div className="panel px-5 py-4"><h3 className="mb-2">Profitability</h3><dl><MetricRow label="Gross margin" value={data.gross_margin} percent/><MetricRow label="Net margin" value={data.net_margin} percent/><MetricRow label="Return on equity" value={data.roe} percent/></dl><p className="mt-4 text-[10px] leading-relaxed text-muted-foreground">Based on reported annual financial statements.</p></div>
      <div className="panel px-5 py-4"><h3 className="mb-2">Year-over-year change</h3><dl><MetricRow label="Gross margin" value={pp(data.gross_margin_change)} suffix=" pp" signed/><MetricRow label="Net margin" value={pp(data.net_margin_change)} suffix=" pp" signed/><MetricRow label="Return on equity" value={pp(data.roe_change)} suffix=" pp" signed/></dl><p className="mt-4 text-[10px] text-muted-foreground">pp = percentage points Â· â€” = unavailable</p></div>
    </div>
  </section>;
}
