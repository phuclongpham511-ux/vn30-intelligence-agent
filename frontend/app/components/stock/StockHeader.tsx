import Link from "next/link";
import { ArrowLeft, ArrowUpRight, ArrowDownRight, Clock3 } from "lucide-react";
import type { Stock, Market } from "@/lib/types";
import { englishCompanyName, formatDate, formatNumber, formatPercent, direction } from "@/lib/presentation";
export default function StockHeader({ stock, market }: { stock: Stock; market: Market }) {
  const name = englishCompanyName(stock);
  const move = market.daily_return;
  return <div>
    <Link href="/" className="mb-6 inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground"><ArrowLeft size={13}/>Back to Explore</Link>
    <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
      <div className="flex items-center gap-4"><span className="flex size-14 shrink-0 items-center justify-center rounded-xl border border-primary/20 bg-primary/10 text-lg font-semibold text-primary">{stock.symbol.slice(0,3)}</span>
        <div><div className="flex flex-wrap items-center gap-3"><h1 className="text-[32px] leading-none">{stock.symbol}</h1>{stock.exchange && <span className="rounded border px-2 py-1 text-[10px] text-muted-foreground">{stock.exchange}</span>}</div>
          {name && <p className="mt-2 text-sm text-muted-foreground">{name}</p>}
        </div>
      </div>
      <div className="sm:text-right"><div className="financial text-[32px] font-semibold leading-tight tracking-tight">{formatNumber(market.close)} <span className="text-sm font-normal text-muted-foreground">VND</span></div>
        <div className={`financial mt-1 flex items-center gap-1.5 text-sm sm:justify-end ${direction(move)}`}>{typeof move === "number" && move !== 0 && (move > 0 ? <ArrowUpRight size={16}/> : <ArrowDownRight size={16}/>)}<span>{formatPercent(move, true)}</span><span className="ml-1 text-xs text-muted-foreground">daily change</span></div>
      </div>
    </div>
    <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] text-muted-foreground"><span className="flex items-center gap-1.5"><Clock3 size={12}/>As of {formatDate(market.as_of)}</span><span>Source: {market.source}</span><span>Daily data · Not realtime</span></div>
  </div>;
}
