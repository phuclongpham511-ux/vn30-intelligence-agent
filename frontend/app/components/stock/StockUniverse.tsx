"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { Security } from "@/lib/types";
import { loadUniverse } from "@/lib/universe";
type Universe = { stocks: Security[]; loading: boolean; error: string; status: string; lastSynced: string | null; refresh: () => void };
const Context = createContext<Universe | null>(null);
export function StockUniverse({ children }: { children: React.ReactNode }) {
  const [stocks, setStocks] = useState<Security[]>([]);
  const [status, setStatus] = useState('not_attempted');
  const [lastSynced, setLastSynced] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);
  const refresh = useCallback(() => setVersion(value => value + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError("");
    loadUniverse(fetch, controller.signal).then(result => {
      if (!controller.signal.aborted) { setStocks(result.stocks); setStatus(result.status); setLastSynced(result.lastSynced); }
    }).catch(error => { if (error.name !== "AbortError") setError("Could not load the equity universe. Please retry."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [version]);
  return <Context.Provider value={{ stocks, loading, error, status, lastSynced, refresh }}>{children}</Context.Provider>;
}
export function useStocks() { const value = useContext(Context); if (!value) throw new Error("StockUniverse is required"); return value; }
