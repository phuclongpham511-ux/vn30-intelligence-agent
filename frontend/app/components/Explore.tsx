"use client";
import { useEffect, useState } from "react";
import NewsFeed from "./stock/NewsFeed";
import { StockLoading, StockError } from "./stock/StockStates";
import type { Overview, TechnicalBar } from "@/lib/types";
import StockHeader from "./stock/StockHeader";
import TechnicalChart from "./stock/TechnicalChart";
import MarketSnapshot from "./stock/MarketSnapshot";
import FundamentalsCard from "./stock/FundamentalsCard";
import RawDataTable from "./stock/RawDataTable";
import MaterialitySlot from "./stock/MaterialitySlot";


export default function Explore({ ticker }: { ticker: string }) {
  const [data, setData] = useState<Overview | null>(null);
  const [technicalRows, setTechnicalRows] = useState<TechnicalBar[]>([]);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError("");
    fetch("/api/stocks/" + encodeURIComponent(ticker) + "/overview", { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error(response.status === 404 ? "STOCK_NOT_FOUND" : "PROVIDER_UNAVAILABLE");
        setData(await response.json());
      }).catch(error => { if (error.name !== "AbortError") setError(error.message === "STOCK_NOT_FOUND" ? "This ticker has not been added. Find it in Explore to get started." : "The data provider is temporarily unavailable. Please try again."); });
    return () => controller.abort();
  }, [ticker, attempt]);
  if (error) return <StockError ticker={ticker} message={error} retry={() => setAttempt(attempt + 1)}/>;
  if (!data) return <StockLoading ticker={ticker}/>;
  return <div className="page-stack">
    <StockHeader stock={data.stock} market={data.market}/>
    <MaterialitySlot/>
    <TechnicalChart ticker={ticker} onRows={setTechnicalRows}/>
    <MarketSnapshot market={data.market}/>
    <FundamentalsCard data={data.fundamentals}/>
    <NewsFeed items={data.news}/>
    <RawDataTable bars={technicalRows}/>
  </div>;
}
