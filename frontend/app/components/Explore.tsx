"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

type Bar = { date: string; close: number };
type Market = { ticker: string; as_of: string | null; close: number | null; source: string } & Record<string, string | number | null>;
type Fundamental = { period: string | null; source: string } & Record<string, string | number | null>;
type News = { id: string; published_at: string; title: string; source: string; is_fixture: boolean; url: string | null };
type Overview = { stock: { symbol: string; company_name: string | null }; history: Bar[]; market: Market; fundamentals: Fundamental; news: News[] };

function number(value: unknown, percent = false) {
  return typeof value === "number" ? (percent ? new Intl.NumberFormat("en", { style: "percent", maximumFractionDigits: 2 }).format(value) : new Intl.NumberFormat("en", { maximumFractionDigits: 2 }).format(value)) : "—";
}
function Chart({ bars }: { bars: Bar[] }) {
  if (!bars.length) return <p>No price history available.</p>;
  const low = Math.min(...bars.map(bar => bar.close));
  const high = Math.max(...bars.map(bar => bar.close));
  const span = high - low || 1;
  const points = bars.map((bar, index) => `${40 + index / Math.max(bars.length - 1, 1) * 720},${190 - (bar.close - low) / span * 150}`).join(" ");
  return <><svg viewBox="0 0 800 240" role="img" aria-label={`Daily close price chart in VND, from ${bars[0].date} to ${bars[bars.length - 1].date}`}>
    <title>Daily close price in VND</title><line x1="40" y1="195" x2="760" y2="195" stroke="#cbd5d1"/>
    <polyline points={points} fill="none" stroke="#166b5b" strokeWidth="2"/>
    <text x="40" y="20">{number(high)} VND</text><text x="40" y="220">{bars[0].date}</text>
    <text x="760" y="220" textAnchor="end">{bars[bars.length - 1].date}</text>
  </svg><details><summary>Inspect daily close values</summary><div className="table-scroll"><table><thead><tr><th>Date</th><th>Close (VND)</th></tr></thead><tbody>
    {bars.map(bar => <tr key={bar.date}><td>{bar.date}</td><td>{number(bar.close)}</td></tr>)}
  </tbody></table></div></details></>;
}
export default function Explore({ ticker }: { ticker: string }) {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError("");
    fetch("/api/stocks/" + encodeURIComponent(ticker) + "/overview", { signal: controller.signal })
      .then(async response => { const body = await response.json(); if (!response.ok) throw new Error(body.detail || "Data unavailable"); setData(body); })
      .catch(error => { if (error.name !== "AbortError") setError(error.message); });
    return () => controller.abort();
  }, [ticker, attempt]);
  if (error) return <><h1>{ticker}</h1><p role="alert" className="error">{error}</p><button onClick={() => setAttempt(attempt + 1)}>Retry</button> <Link href="/">Select or add a ticker</Link></>;
  if (!data) return <p role="status">Loading {ticker} market data and annual reports…</p>;
  const { stock, market, fundamentals, history, news } = data;
  const marketFields: [string, string, boolean][] = [
    ["return_5d", "5D return", true], ["return_20d", "20D return", true], ["ma20", "MA20 · VND", false], ["ma50", "MA50 · VND", false],
    ["rsi14", "RSI14", false], ["avg_volume_20d", "20D average volume · shares", false], ["relative_volume_20d", "Relative volume · ×", false],
    ["volatility_20d", "20D volatility · annualized", true], ["drawdown_from_20d_high", "From 20D high", true],
  ];
  const fundamentalFields: [string, string, boolean][] = [
    ["revenue", "Revenue · VND", false], ["revenue_growth_yoy", "Revenue growth · YoY", true], ["net_profit", "Net profit after tax · VND", false],
    ["net_profit_growth_yoy", "Profit growth · YoY", true], ["gross_margin", "Gross margin", true], ["net_margin", "Net margin", true], ["roe", "ROE", true],
    ["gross_margin_change", "Gross margin change · pp", false], ["net_margin_change", "Net margin change · pp", false], ["roe_change", "ROE change · pp", false],
  ];
  return <><Link href="/">← Change ticker</Link><p className="eyebrow">{stock.company_name || "Stock explore"}</p><h1>{stock.symbol}</h1>
    <p className="price">{number(market.close)} VND <small>Daily {number(market.daily_return, true)}</small></p>
    <p>As of {market.as_of || "unavailable"} · {market.source} · Daily data, not realtime</p>
    <section><h2>Price history</h2><Chart bars={history}/></section>
    <section><h2>Market metrics</h2><div className="metrics">{marketFields.map(([key,label,percent]) => <div key={key}><small>{label}</small><strong>{number(market[key], percent)}</strong></div>)}</div>
      <p className="note">— means insufficient observations. Returns use trading sessions. Volatility uses 252 sessions/year.</p></section>
    <section><h2>Annual fundamentals</h2><p>Period: {fundamentals.period || "unavailable"} · {fundamentals.source}</p>
      <div className="metrics">{fundamentalFields.filter(([key]) => fundamentals[key] !== null).map(([key,label,percent]) => <div key={key}><small>{label}</small><strong>{number(key.endsWith("_change") && typeof fundamentals[key] === "number" ? Number(fundamentals[key]) * 100 : fundamentals[key], percent)}</strong></div>)}</div>
      <p className="note">Missing or unreliable fields are omitted. Margin changes compare the same period one year earlier; pp = percentage points.</p></section>
    <section><h2>News</h2><p className="note">Sample feed only — live news ingestion is not connected.</p>{news.map(item => <article key={item.id}><strong>{item.title}</strong><p>{item.published_at.slice(0,10)} · {item.source}{item.is_fixture ? " · Fixture, not an actual announcement" : ""}</p></article>)}</section>
  </>;
}
