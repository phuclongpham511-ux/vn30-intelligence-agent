import type { Market } from "@/lib/types";
import { Card } from "../ui/card";
import MetricRow from "./MetricRow";
export default function MarketSnapshot({ market }: { market: Market }) {
  return <Card className="gap-0 p-5 shadow-none"><div className="mb-1 flex items-center justify-between"><h2>Market snapshot</h2><span className="eyebrow">Daily</span></div><dl>
    <MetricRow label="Daily return" value={market.daily_return} percent signed/>
    <MetricRow label="5D return" value={market.return_5d} percent signed/>
    <MetricRow label="20D return" value={market.return_20d} percent signed/>
    <MetricRow label="RSI 14" value={market.rsi14}/>
    <MetricRow label="Relative volume" value={market.relative_volume_20d} suffix="×"/>
    <MetricRow label="20D volatility" value={market.volatility_20d} percent/>
    <MetricRow label="20D drawdown" value={market.drawdown_from_20d_high} percent signed/>
  </dl><p className="mt-auto pt-3 text-[10px] leading-relaxed text-muted-foreground">Returns use trading sessions. Volatility is annualized.</p></Card>;
}
