"use client";
import Link from "next/link";
import { ArrowUpRight, Database, ArrowRight, RefreshCw } from "lucide-react";
import { useStocks } from "./stock/StockUniverse";
import { englishCompanyName } from "@/lib/presentation";
import { Button } from "./ui/button";
import { Skeleton } from "./ui/skeleton";
export default function TickerPicker() {
  const { stocks, loading, error, refresh } = useStocks();
  return <section aria-labelledby="available-title">
    <div className="mb-4 flex items-center justify-between"><div className="flex items-center gap-3"><h2 id="available-title">Available stocks</h2><span className="rounded-md border px-2 py-0.5 text-[11px] text-muted-foreground">{loading ? "â€¦" : stocks.length}</span></div><span className="hidden text-xs text-muted-foreground sm:block">Your market starting points</span></div>
    {loading ? <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{[0,1,2].map(i => <Skeleton key={i} className="h-40 rounded-xl"/>)}</div>
      : error ? <div role="alert" className="panel p-6"><p>{error}</p><Button variant="outline" onClick={refresh} className="mt-4"><RefreshCw/>Retry</Button></div>
      : stocks.length ? <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{stocks.map(stock => <Link key={stock.id} href={"/stocks/" + stock.symbol} className="group panel p-5 transition-colors hover:border-primary/60 hover:bg-muted/30">
        <div className="flex items-start justify-between"><span className="flex h-11 min-w-11 items-center justify-center rounded-lg border bg-muted/40 px-2 text-sm font-semibold tracking-wide">{stock.symbol}</span><ArrowUpRight size={17} className="text-muted-foreground transition-colors group-hover:text-primary"/></div>
        <h3 className="mt-4 text-base">{stock.symbol}</h3>{englishCompanyName(stock) && <p className="mt-1 truncate text-xs text-muted-foreground">{englishCompanyName(stock)}</p>}
        <div className="mt-5 flex items-center justify-between border-t pt-3 text-[11px] text-muted-foreground"><span>{stock.exchange || "Vietnam equity"}</span><span className="flex items-center gap-1.5">Open overview<ArrowRight size={12}/></span></div>
      </Link>)}</div> : <div className="panel p-8 text-center"><Database className="mx-auto mb-3 text-muted-foreground"/><h3>No stocks added yet</h3><p className="mt-2 text-sm text-muted-foreground">Use the search above to validate and add a ticker.</p></div>}
  </section>;
}
