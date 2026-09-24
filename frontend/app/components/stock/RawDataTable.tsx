import { Table2 } from "lucide-react";
import type { TechnicalBar } from "@/lib/types";
import { formatNumber } from "@/lib/presentation";
export default function RawDataTable({ bars }: { bars: TechnicalBar[] }) {
  return <details className="panel min-w-0 overflow-hidden"><summary className="flex flex-wrap items-center gap-2 px-5 py-4 text-xs font-medium"><Table2 size={15} className="text-muted-foreground"/>View technical data<span className="ml-auto text-[10px] text-muted-foreground">{bars.length} daily observations · Expand</span></summary>
    <div className="table-scroll border-t" tabIndex={0} role="region" aria-label="Daily technical evidence"><table className="text-xs"><caption className="sr-only">Selected chart period. Prices and moving averages in VND, volume in shares, RSI from zero to one hundred. Unavailable indicators are shown as a dash.</caption><thead><tr>{["Date","Open","High","Low","Close","Volume","MA20","MA50","RSI14","Source"].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead>
      <tbody>{bars.map(bar => <tr key={bar.date}><td>{bar.date}</td>{(["open","high","low","close","volume","ma20","ma50","rsi14"] as const).map(key => <td key={key}>{formatNumber(bar[key],key === "volume" ? 0 : 2)}</td>)}<td>{bar.source}</td></tr>)}</tbody></table>{!bars.length && <p className="p-5 text-sm text-muted-foreground">No observations loaded for the selected chart period.</p>}</div>
  </details>;
}
