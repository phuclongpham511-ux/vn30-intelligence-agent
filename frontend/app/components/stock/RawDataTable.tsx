import { Table2 } from "lucide-react";
import type { Bar } from "@/lib/types";
import { formatNumber } from "@/lib/presentation";
export default function RawDataTable({ bars }: { bars: Bar[] }) {
  return <details className="panel overflow-hidden"><summary className="flex items-center gap-2 px-5 py-4 text-xs font-medium"><Table2 size={15} className="text-muted-foreground"/>View raw data<span className="ml-auto text-[10px] text-muted-foreground">{bars.length} daily observations · Expand</span></summary>
    <div className="table-scroll border-t" tabIndex={0} role="region" aria-label="Daily OHLCV data"><table className="text-xs"><caption className="sr-only">Daily market evidence. Prices in VND, volume in shares.</caption><thead><tr>{["Date","Open","High","Low","Close","Volume"].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead>
      <tbody>{bars.map(bar => <tr key={bar.date}><td>{bar.date}</td><td>{formatNumber(bar.open)}</td><td>{formatNumber(bar.high)}</td><td>{formatNumber(bar.low)}</td><td>{formatNumber(bar.close)}</td><td>{formatNumber(bar.volume,0)}</td></tr>)}</tbody></table></div>
  </details>;
}
