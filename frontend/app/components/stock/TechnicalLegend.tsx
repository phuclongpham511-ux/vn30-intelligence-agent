import type { TechnicalBar } from "@/lib/types";
import { formatNumber } from "@/lib/presentation";

export default function TechnicalLegend({ bar }: { bar?: TechnicalBar }) {
  return <div className="financial flex min-h-12 flex-wrap items-center gap-x-4 gap-y-2 text-xs" aria-label="Selected candle and indicator values">
    <span className="font-medium">{bar?.date ?? "No observation"}</span>
    {(["open", "high", "low", "close", "volume", "ma20", "ma50", "rsi14"] as const).map((key, index) => <span key={key}><span className="mr-1 text-muted-foreground">{["O", "H", "L", "C", "Volume", "MA20", "MA50", "RSI14"][index]}</span><span style={index === 5 ? {color:"var(--ma20)"} : index === 6 ? {color:"var(--ma50)"} : index === 7 ? {color:"var(--rsi)"} : undefined}>{formatNumber(bar?.[key], index < 5 ? 0 : 2)}</span></span>)}
  </div>;
}
