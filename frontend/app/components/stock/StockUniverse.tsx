"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { Security } from "@/lib/types";
import { loadUniverse, type IndexGroups } from "@/lib/universe";
type Universe = { groups: IndexGroups; stocks: Security[]; loading: boolean; error: string; status: string; lastSynced: string | null; refresh: () => void };
const Context = createContext<Universe | null>(null);
export function StockUniverse({ children, enabled=true }: { children: React.ReactNode; enabled?: boolean }) {
  const [groups, setGroups] = useState<IndexGroups>({groups:{},status:"not_attempted",source:"SSI:FastConnect"});
  const [stocks, setStocks] = useState<Security[]>([]);
  const [status, setStatus] = useState('not_attempted');
  const [lastSynced, setLastSynced] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);
  const refresh = useCallback(() => setVersion(value => value + 1), []);
  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    setLoading(true); setError("");
    loadUniverse(fetch, controller.signal).then(result => {
      if (!controller.signal.aborted) { setStocks(result.stocks); setGroups(result.groups); setStatus(result.status); setLastSynced(result.lastSynced); }
    }).catch(error => { if (error.name !== "AbortError") setError("Could not load the equity universe. Please retry."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [version, enabled]);
  return <Context.Provider value={{ groups, stocks, loading, error, status, lastSynced, refresh }}>{children}</Context.Provider>;
}
export function useStocks() { const value = useContext(Context); if (!value) throw new Error("StockUniverse is required"); return value; }
