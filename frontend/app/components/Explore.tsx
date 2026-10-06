"use client";
import {useLocale} from "@/lib/i18n";
import { useEffect, useState } from "react";
import StockNews from "./stock/StockNews";
import StockCommunity from "./stock/StockCommunity";
import { StockLoading, StockError } from "./stock/StockStates";
import type { Overview, TechnicalBar } from "@/lib/types";
import StockHeader from "./stock/StockHeader";
import TechnicalChart from "./stock/TechnicalChart";
import MarketSnapshot from "./stock/MarketSnapshot";
import FundamentalTrends from "./stock/FundamentalTrends";
import RawDataTable from "./stock/RawDataTable";


export default function Explore({ ticker }: { ticker: string }) {
  const {t}=useLocale();
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
    <nav aria-label={t("Stock sections")} className="flex flex-wrap gap-4 text-sm text-primary"><a href="#stock-price" className="hover:underline">{t("Price & technicals")}</a><a href="#stock-fundamentals" className="hover:underline">{t("Fundamentals")}</a><a href="#stock-news" className="hover:underline">{t("News mentioning {ticker}",{ticker})}</a><a href="#stock-community" className="hover:underline">{t("Community discussions")}</a></nav>
    <div id="stock-price" className="scroll-mt-24"><TechnicalChart ticker={ticker} onRows={setTechnicalRows}/></div>
    <MarketSnapshot market={data.market}/>
    <div id="stock-fundamentals" className="scroll-mt-24"><FundamentalTrends ticker={ticker}/></div>
    <div id="stock-news" className="scroll-mt-24"><StockNews ticker={ticker}/></div>
    <div id="stock-community" className="scroll-mt-24"><StockCommunity ticker={ticker}/></div>
    <RawDataTable bars={technicalRows}/>
  </div>;
}
