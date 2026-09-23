"use client";
import { useEffect, useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type Stock = { symbol: string; company_name: string | null };
export default function TickerPicker() {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [ticker, setTicker] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  useEffect(() => {
    fetch("/api/stocks").then(async response => {
      if (!response.ok) throw new Error("Could not load stocks. Check the backend.");
      setStocks(await response.json());
    }).catch(error => setError(error.message));
  }, []);
  async function open(event: FormEvent) {
    event.preventDefault(); setError(""); setBusy(true);
    const symbol = ticker.trim().toUpperCase();
    try {
      const response = await fetch("/api/stocks", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ticker: symbol }) });
      const body = await response.json();
      if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Enter a valid ticker.");
      router.push("/stocks/" + encodeURIComponent(body.symbol));
    } catch (error) { setError(error instanceof Error ? error.message : "Unable to open stock."); }
    finally { setBusy(false); }
  }
  return <section><h2>Explore a stock</h2>
    <form onSubmit={open}><label htmlFor="ticker">Ticker</label>{" "}
      <input id="ticker" value={ticker} onChange={event => setTicker(event.target.value)} placeholder="Enter a ticker" maxLength={20} required pattern="[A-Za-z0-9 ]+" />
      <button disabled={busy}>{busy ? "Validating…" : "Open / add stock"}</button>
    </form>
    {error && <p role="alert" className="error">{error}</p>}
    <div className="tickers">{stocks.filter(stock => stock.symbol.includes(ticker.trim().toUpperCase())).map(stock =>
      <Link key={stock.symbol} href={"/stocks/" + stock.symbol}>{stock.symbol}<small>{stock.company_name}</small></Link>)}</div>
  </section>;
}
