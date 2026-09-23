"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { Stock } from "@/lib/types";
type Universe = { stocks: Stock[]; loading: boolean; error: string; refresh: () => void; remember: (stock: Stock) => void };
const Context = createContext<Universe | null>(null);
export function StockUniverse({ children }: { children: React.ReactNode }) {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);
  const refresh = useCallback(() => setVersion(value => value + 1), []);
  const remember = useCallback((stock: Stock) => setStocks(previous => [...previous.filter(row => row.symbol !== stock.symbol), stock].sort((a,b) => a.symbol.localeCompare(b.symbol))), []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError("");
    fetch("/api/stocks", { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error("Stock list unavailable");
      setStocks(await response.json());
    }).catch(error => { if (error.name !== "AbortError") setError("Could not load available stocks. Please retry."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [version]);
  return <Context.Provider value={{ stocks, loading, error, refresh, remember }}>{children}</Context.Provider>;
}
export function useStocks() { const value = useContext(Context); if (!value) throw new Error("StockUniverse is required"); return value; }
