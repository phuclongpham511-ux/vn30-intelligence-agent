"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import type { Overview } from "@/lib/types";
import StockHeader from "./stock/StockHeader";
import PriceChart from "./stock/PriceChart";
import MarketSnapshot from "./stock/MarketSnapshot";
import TechnicalMetrics from "./stock/TechnicalMetrics";
import FundamentalsCard from "./stock/FundamentalsCard";
import RawDataTable from "./stock/RawDataTable";
import MaterialitySlot from "./stock/MaterialitySlot";
import { Button } from "./ui/button";

export default function Explore({ ticker }: { ticker: string }) {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError("");
    fetch("/api/stocks/" + encodeURIComponent(ticker) + "/overview", { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error(response.status === 404 ? "This ticker has not been added. Find it in Explore to get started." : "The data provider is temporarily unavailable. Please try again.");
        setData(await response.json());
      }).catch(error => { if (error.name !== "AbortError") setError(error instanceof TypeError ? "The data service could not be reached. Please try again." : error.message); });
    return () => controller.abort();
  }, [ticker, attempt]);
  if (error) return <div role="alert" className="panel p-8"><h1>Could not load {ticker}</h1><p className="my-4 text-muted-foreground">{error}</p><Button onClick={() => setAttempt(attempt + 1)}>Retry</Button><Link href="/" className="ml-4 text-sm">Back to Explore</Link></div>;
  if (!data) return <p role="status">Loading {ticker} dataâ€¦</p>;
  return <div className="page-stack">
    <StockHeader stock={data.stock} market={data.market}/>
    <MaterialitySlot/>
    <div className="grid min-w-0 gap-4 xl:grid-cols-12"><div className="min-w-0 xl:col-span-8"><PriceChart bars={data.history} source={data.market.source}/></div><div className="min-w-0 xl:col-span-4"><MarketSnapshot market={data.market}/></div></div>
    <TechnicalMetrics market={data.market}/>
    <FundamentalsCard data={data.fundamentals}/>
    <section className="panel p-5"><h2>Sample News Feed</h2><p className="my-3 text-xs text-muted-foreground">Live news ingestion is not connected yet.</p>{data.news.map(item => <article key={item.id} className="border-t py-3 text-sm"><h3>{item.title}</h3><p className="mt-1 text-xs text-muted-foreground">{item.source} Â· Fixture</p></article>)}</section>
    <RawDataTable bars={data.history}/>
  </div>;
}
