"use client";
import { useId, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, CornerDownLeft, ArrowUpRight } from "lucide-react";
import { useStocks } from "./StockUniverse";
import { browseSecurities } from "@/lib/universe";
import { englishCompanyName } from "@/lib/presentation";
export default function TickerSearch() {
  const { stocks } = useStocks();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [error, setError] = useState("");
  const router = useRouter();
  const id = useId();
  const symbol = query.trim().toUpperCase();
  const matches = browseSecurities(stocks, query, '', 0, 8).items;
  const count = matches.length;
  function navigate(ticker: string) {
    setOpen(false); setQuery(""); router.push("/stocks/" + ticker);
  }
  function choose(index: number) {
    if (index >= 0 && index < matches.length) navigate(matches[index].symbol);
  }
  return <div className="relative max-w-lg" onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false); }}>
    <form onSubmit={event => { event.preventDefault(); if (active >= 0) choose(active); else if (symbol) { const exact = stocks.find(stock => stock.symbol === symbol); if (exact) navigate(symbol); else if (matches.length) choose(0); else setError("No matching listed equity in the cached universe."); } }} className="flex items-center gap-2.5 rounded-lg border bg-card px-3 focus-within:border-primary">
      <Search size={16} className="shrink-0 text-muted-foreground"/>
      <input aria-label="Search ticker" role="combobox" aria-expanded={open} aria-controls={id} aria-autocomplete="list" aria-activedescendant={open && active >= 0 ? id + "-" + active : undefined}
        value={query} onFocus={() => setOpen(true)}
        onChange={event => { setQuery(event.target.value); setOpen(true); setActive(-1); setError(""); }}
        onKeyDown={event => { if (event.key === "Escape") { setOpen(false); setActive(-1); } if (event.key === "ArrowDown") { event.preventDefault(); setOpen(true); setActive(value => Math.min(value + 1, count - 1)); } if (event.key === "ArrowUp") { event.preventDefault(); setActive(value => Math.max(value - 1, 0)); } }}
        className="h-10 w-full min-w-0 bg-transparent text-sm outline-none focus-visible:outline-none" placeholder="Search ticker or company" maxLength={120} autoComplete="off"/>
      <button type="submit" aria-label="Open selected ticker" disabled={!symbol} className="rounded p-1 text-muted-foreground hover:text-foreground disabled:opacity-40"><CornerDownLeft size={15}/></button>
    </form>
    {open && <div className="absolute top-full z-50 mt-2 w-full min-w-0 overflow-hidden rounded-xl border bg-popover shadow-xl">
      <div className="eyebrow border-b px-4 py-3">{symbol ? "Search results" : "Vietnam equities"}</div>
      <ul role="listbox" id={id} aria-label="Ticker suggestions" className="max-h-80 overflow-y-auto p-1">
        {matches.map((stock,index) => <li key={stock.symbol} role="option" aria-selected={active === index} id={id + "-" + index} className={active === index ? "rounded-lg bg-muted" : ""}>
          <button type="button" onMouseDown={event => event.preventDefault()} onClick={() => choose(index)} className="flex w-full items-center gap-3 rounded-lg p-3 text-left hover:bg-muted">
            <span className="w-11 shrink-0 font-semibold">{stock.symbol}</span><span className="min-w-0 flex-1 truncate text-xs text-muted-foreground">{englishCompanyName(stock) || "Stock"}</span><span className="text-[10px] text-muted-foreground">{stock.exchange}</span><ArrowUpRight size={13}/>
          </button></li>)}
        {!count && <li className="p-4 text-sm text-muted-foreground">No matching listed equities.</li>}
      </ul>
      <div className="border-t px-4 py-2 text-[10px] text-muted-foreground">↑ ↓ to navigate · Enter to open · Esc to close</div>
    </div>}
    {error && <p role="alert" className="absolute top-full z-50 mt-2 w-full rounded-lg border bg-card p-3 text-xs">{error}</p>}

  </div>;
}
