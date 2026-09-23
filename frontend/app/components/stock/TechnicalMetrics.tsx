import type { Market } from "@/lib/types";
import { TrendingUp, Gauge, Activity, Shield } from "lucide-react";
import MetricRow from "./MetricRow";
export default function TechnicalMetrics({ market }: { market: Market }) {
  return <section><div className="mb-4 flex items-center justify-between"><h2>Technical overview</h2><span className="text-[10px] text-muted-foreground">Calculated from daily OHLCV</span></div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <div className="panel p-4"><h3 className="mb-1 flex items-center gap-2 text-xs"><TrendingUp size={14} className="text-muted-foreground"/>Trend</h3><dl><MetricRow label="MA20" value={market.ma20} suffix=" VND"/><MetricRow label="MA50" value={market.ma50} suffix=" VND"/></dl></div>
      <div className="panel p-4"><h3 className="mb-1 flex items-center gap-2 text-xs"><Gauge size={14} className="text-muted-foreground"/>Momentum</h3><dl><MetricRow label="RSI 14" value={market.rsi14}/></dl><p className="mt-3 text-[10px] text-muted-foreground">Wilder smoothing Â· 14 sessions</p></div>
      <div className="panel p-4"><h3 className="mb-1 flex items-center gap-2 text-xs"><Activity size={14} className="text-muted-foreground"/>Activity</h3><dl><MetricRow label="Relative volume" value={market.relative_volume_20d} suffix="Ã—"/><MetricRow label="20D avg. volume" value={market.avg_volume_20d}/></dl></div>
      <div className="panel p-4"><h3 className="mb-1 flex items-center gap-2 text-xs"><Shield size={14} className="text-muted-foreground"/>Risk</h3><dl><MetricRow label="20D volatility" value={market.volatility_20d} percent/><MetricRow label="20D drawdown" value={market.drawdown_from_20d_high} percent signed/></dl></div>
    </div>
  </section>;
}
