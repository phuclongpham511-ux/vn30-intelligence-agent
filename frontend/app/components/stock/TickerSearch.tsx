"use client";
import { useId, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, CornerDownLeft, Loader2, Plus, ArrowUpRight } from "lucide-react";
import { useStocks } from "./StockUniverse";
import { englishCompanyName } from "@/lib/presentation";
export default function TickerSearch() {
  const { stocks, remember } = useStocks();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  const id = useId();
  const symbol = query.trim().toUpperCase();
  const matches = stocks.filter(stock => stock.symbol.includes(symbol) || englishCompanyName(stock)?.toUpperCase().includes(symbol)).slice(0, 8);
  const canAdd = Boolean(symbol) && !stocks.some(stock => stock.symbol === symbol);
  const count = matches.length + (canAdd ? 1 : 0);
  async function navigate(ticker: string, existing: boolean) {
    if (busy) return;
    if (!/^[A-Z0-9]{1,20}$/.test(ticker)) { setError("Enter a valid stock ticker."); return; }
    setError("");
    if (existing) { setOpen(false); setQuery(""); router.push("/stocks/" + ticker); return; }
    setBusy(true);
    try {
      const response = await fetch("/api/stocks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ticker }) });
      if (!response.ok) throw new Error(response.status === 404 ? "Ticker not found. Try another symbol." : "Could not validate this ticker. Please retry.");
      const stock = await response.json();
      remember(stock); setOpen(false); setQuery(""); router.push("/stocks/" + stock.symbol);
    } catch (error) { setError(error instanceof Error ? error.message : "Could not open this ticker."); }
    finally { setBusy(false); }
  }
  function choose(index: number) {
    if (index >= 0 && index < matches.length) void navigate(matches[index].symbol, true);
    else if (canAdd) void navigate(symbol, false);
  }
  return <div className="relative max-w-lg" onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false); }}>
    <form onSubmit={event => { event.preventDefault(); if (active >= 0) choose(active); else if (symbol) { const exact = stocks.find(stock => stock.symbol === symbol); if (exact) void navigate(symbol, true); else if (matches.length) choose(0); else void navigate(symbol, false); } }} className="flex items-center gap-2.5 rounded-lg border bg-card px-3 focus-within:border-primary">
      {busy ? <Loader2 size={16} className="shrink-0 animate-spin"/> : <Search size={16} className="shrink-0 text-muted-foreground"/>}
      <input aria-label="Search ticker" role="combobox" aria-expanded={open} aria-controls={id} aria-autocomplete="list" aria-activedescendant={open && active >= 0 ? id + "-" + active : undefined}
        value={query} onFocus={() => setOpen(true)} disabled={busy}
        onChange={event => { setQuery(event.target.value); setOpen(true); setActive(-1); setError(""); }}
        onKeyDown={event => { if (event.key === "Escape") { setOpen(false); setActive(-1); } if (event.key === "ArrowDown") { event.preventDefault(); setOpen(true); setActive(value => Math.min(value + 1, count - 1)); } if (event.key === "ArrowUp") { event.preventDefault(); setActive(value => Math.max(value - 1, 0)); } }}
        className="h-10 w-full min-w-0 bg-transparent text-sm outline-none focus-visible:outline-none" placeholder="Search ticker or company" maxLength={20} autoComplete="off"/>
      <button type="submit" aria-label="Open selected ticker" disabled={busy || !symbol} className="rounded p-1 text-muted-foreground hover:text-foreground disabled:opacity-40"><CornerDownLeft size={15}/></button>
    </form>
    {open && <div className="absolute top-full z-50 mt-2 w-full min-w-0 overflow-hidden rounded-xl border bg-popover shadow-xl">
      <div className="eyebrow border-b px-4 py-3">{symbol ? "Search results" : "Available stocks"}</div>
      <ul role="listbox" id={id} aria-label="Ticker suggestions" className="max-h-80 overflow-y-auto p-1">
        {matches.map((stock,index) => <li key={stock.symbol} role="option" aria-selected={active === index} id={id + "-" + index} className={active === index ? "rounded-lg bg-muted" : ""}>
          <button type="button" onMouseDown={event => event.preventDefault()} onClick={() => choose(index)} className="flex w-full items-center gap-3 rounded-lg p-3 text-left hover:bg-muted">
            <span className="w-11 shrink-0 font-semibold">{stock.symbol}</span><span className="min-w-0 flex-1 truncate text-xs text-muted-foreground">{englishCompanyName(stock) || "Stock"}</span><span className="text-[10px] text-muted-foreground">{stock.exchange}</span><ArrowUpRight size={13}/>
          </button></li>)}
        {canAdd && <li role="option" aria-selected={active === matches.length} id={id + "-" + matches.length}><button type="button" onMouseDown={event => event.preventDefault()} onClick={() => void navigate(symbol, false)} className={`flex w-full items-center gap-2 rounded-lg p-3 text-left text-sm text-primary hover:bg-muted ${active === matches.length ? "bg-muted" : ""}`}><Plus size={16}/>Validate and add {symbol}</button></li>}
        {!count && <li className="p-4 text-sm text-muted-foreground">Type a ticker to get started.</li>}
      </ul>
      <div className="border-t px-4 py-2 text-[10px] text-muted-foreground">â†‘ â†“ to navigate Â· Enter to open Â· Esc to close</div>
    </div>}
    {error && <p role="alert" className="absolute top-full z-50 mt-2 w-full rounded-lg border bg-card p-3 text-xs">{error}</p>}
    {busy && <span role="status" className="sr-only">Validating ticker</span>}
  </div>;
}
