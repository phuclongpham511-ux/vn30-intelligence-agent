"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { MascotState } from "../components/mascot/Mascot";
import SourceCoverage from "../components/news/SourceCoverage";
import ArticleRow from "../components/news/ArticleRow";
import { useStocks } from "../components/stock/StockUniverse";
import { englishCompanyName } from "@/lib/presentation";
import { emptyNewsFilters, newsViewQuery } from "@/lib/news";
import { emptyWatchlist, readWatchlist, followStock, unfollowStock, markReviewed, unreviewedStories, loadWatchlistUpdates, watchlistStorageKey } from "@/lib/watchlist";
import type { WatchlistState, WatchlistUpdates } from "@/lib/watchlist";

export default function WatchlistPage() {
  const universe = useStocks();
  const [state, setState] = useState<WatchlistState>(emptyWatchlist);
  const [ready, setReady] = useState(false);
  const [storageError, setStorageError] = useState(false);
  const [selected, setSelected] = useState("");
  const [data, setData] = useState<WatchlistUpdates | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const symbolsKey = state.symbols.join(",");

  useEffect(() => {
    const restore = () => {
      try { setState(readWatchlist(localStorage.getItem(watchlistStorageKey))); setStorageError(false); }
      catch { setStorageError(true); }
      setReady(true);
    };
    restore();
    const sync = (event: StorageEvent) => { if (event.key === watchlistStorageKey || event.key === null) restore(); };
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);
  useEffect(() => {
    if (!ready || !symbolsKey) { setData(null); setLoading(false); return; }
    const controller = new AbortController();
    const load = async () => {
      setLoading(true); setError(false); setData(null);
      try {
        const result = await loadWatchlistUpdates(symbolsKey.split(","), controller.signal);
        if (!controller.signal.aborted) setData(result);
      } catch { if (!controller.signal.aborted) setError(true); }
      finally { if (!controller.signal.aborted) setLoading(false); }
    };
    void load();
    const timer = setInterval(() => void load(), 15 * 60 * 1000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [ready, symbolsKey, attempt]);
  const save = (next: WatchlistState) => {
    try { localStorage.setItem(watchlistStorageKey, JSON.stringify(next)); setState(next); setStorageError(false); return true; }
    catch { setStorageError(true); return false; }
  };
  const available = universe.stocks.filter(stock => !state.symbols.includes(stock.symbol));
  const all = data?.stocks.flatMap(row => row.developments || []) || [];
  const recentCount = new Set(all.map(row => row.story_id)).size;
  const newCount = new Set(data?.stocks.flatMap(row => unreviewedStories(row.developments || [], state.seen[row.symbol])) || []).size;
  const unavailableCount = data?.stocks.filter(row => row.status === "unavailable").length || 0;
  return <div className="page-stack">
    <div className="flex items-start justify-between gap-3"><div><div className="eyebrow mb-3">Workspace / Watchlist</div><h1>Watchlist</h1><p className="mt-2 text-sm text-muted-foreground">What changed for the stocks you follow?</p></div>
      <Button variant="outline" disabled={!ready || !state.symbols.length || loading} onClick={() => setAttempt(value => value + 1)}>Refresh updates</Button>
    </div>
    <p className="text-xs text-muted-foreground">Saved in this browser only · No cross-device sync. Developments are ticker-matched news stories, not investment importance.</p>
    {storageError && <p role="alert" className="rounded border p-3 text-sm">Browser storage is unavailable or saved data cannot be read. Your saved Watchlist has not been overwritten. Reload to retry.</p>}
    <form aria-label="Follow a stock" className="flex flex-wrap items-end gap-3" onSubmit={event => { event.preventDefault(); if (available.some(stock => stock.symbol === selected) && save(followStock(state, selected))) setSelected(""); }}>
      <label className="text-xs">Stock to follow<select aria-label="Stock to follow" value={selected} onChange={event => setSelected(event.target.value)} disabled={!ready || universe.loading || !!universe.error || storageError || state.symbols.length >= 50} required className="mt-1 block h-10 max-w-full rounded border bg-background px-3 text-sm sm:min-w-64">
        <option value="">Choose an available stock</option>{available.map(stock => <option key={stock.symbol} value={stock.symbol}>{stock.symbol}{englishCompanyName(stock) ? ` · ${englishCompanyName(stock)}` : ""}</option>)}
      </select></label><Button disabled={!selected || storageError || !ready || state.symbols.length >= 50}>Follow stock</Button>
      <Link href="/" className="py-2 text-xs text-primary hover:underline">Find more stocks in Explore</Link>
    </form>
    {universe.error && <p role="alert" className="text-sm">Available stocks could not be loaded. <button className="text-primary underline" onClick={universe.refresh}>Retry stocks</button></p>}
    {state.symbols.length >= 50 && <p className="text-xs text-muted-foreground">This browser Watchlist supports up to 50 stocks.</p>}
    {!ready ? <MascotState state="loading" role="status">Loading your Watchlist…</MascotState>
      : !state.symbols.length ? !storageError && <section className="panel p-5"><MascotState state="noMatches"><div><h2 className="text-sm">No stocks followed yet</h2><p className="mt-1">Choose a stock above to monitor recent developments.</p></div></MascotState></section>
      : <>
        <SourceCoverage/>
        {loading ? <MascotState state="loading" role="status">Checking recent developments…</MascotState>
          : error ? <MascotState state="dataUnavailable" role="alert">Watchlist updates are temporarily unavailable. Counts are unknown. <button className="text-primary underline" onClick={() => setAttempt(value => value + 1)}>Retry updates</button></MascotState>
          : data && <div className="flex flex-wrap gap-x-5 gap-y-2 border-y py-3 text-sm" role="status"><span>{recentCount} observed recent developments</span><span>{newCount} unreviewed</span>{unavailableCount > 0 && <span>{unavailableCount} stocks unavailable · totals incomplete</span>}<span className="text-xs text-muted-foreground">Ingested in the last 72 hours · Checked {new Date(data.as_of).toLocaleString("en-GB")}</span></div>}
        <section className="panel divide-y" aria-label="Watched stocks">{state.symbols.map(symbol => {
          const row = data?.stocks.find(stock => stock.symbol === symbol);
          const developments = row?.developments;
          const fresh = developments ? unreviewedStories(developments, state.seen[symbol]) : [];
          const reviewedBefore = Object.hasOwn(state.seen, symbol);
          return <article key={symbol} className="grid gap-4 p-5 md:grid-cols-[170px_minmax(0,1fr)]" aria-label={`${symbol} monitoring`}>
            <div><Link href={`/stocks/${encodeURIComponent(symbol)}`} className="text-lg font-semibold text-primary hover:underline">{symbol}</Link><p className="mt-1 text-xs text-muted-foreground">{englishCompanyName(universe.stocks.find(stock => stock.symbol === symbol) || { company_name: null })}</p>
              <button className="mt-3 text-xs text-muted-foreground underline" aria-label={`Remove ${symbol} from Watchlist`} disabled={storageError} onClick={() => save(unfollowStock(state, symbol))}>Remove</button>
            </div>
            <div className="min-w-0">
              {loading ? <p className="text-sm text-muted-foreground">Checking news…</p>
                : error ? <p className="text-sm text-muted-foreground">Development count unavailable.</p>
                : row?.status === "unavailable" ? <p className="text-sm">Stock data is unavailable. This is not a no-change result.</p>
                : developments && <>
                  <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-sm">{developments.length} recent {developments.length === 1 ? "development" : "developments"} · {reviewedBefore ? `${fresh.length} new since your review` : "Not reviewed yet"}</h2>
                    {fresh.length > 0 && <button className="text-xs text-primary underline disabled:opacity-50" disabled={storageError} aria-label={`Mark ${symbol} reviewed`} onClick={() => save(markReviewed(state, symbol, developments))}>Mark reviewed</button>}
                  </div>
                  {!developments.length ? <p className="mt-3 text-sm text-muted-foreground">No recent ticker-matched stories ingested. This does not prove that nothing changed; coverage or tags may be incomplete.</p>
                    : <ul className="mt-3 divide-y">{developments.slice(0,3).map(story => <li key={story.story_id} className="py-3 first:pt-0">
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground"><span>{story.source_count} independent {story.source_count === 1 ? "source" : "sources"}</span><span>First matched <time dateTime={story.first_seen_at}>{new Date(story.first_seen_at).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })}</time></span>{fresh.includes(story.story_id) && <span className="text-primary">{reviewedBefore ? "New" : "Unreviewed"}</span>}</div>
                      <h3 className="mt-1 text-sm leading-6">{story.title}</h3><details className="mt-2 text-xs"><summary className="cursor-pointer text-primary">View source evidence</summary>{story.articles.map(article => <ArticleRow key={article.id} article={article}/>)}</details>
                    </li>)}</ul>}
                  {developments.length > 3 && <p className="text-xs text-muted-foreground">Showing 3 of {developments.length} developments. Open News for more reporting.</p>}
                </>}
              <div className="mt-3 flex flex-wrap gap-4 text-xs"><Link className="text-primary hover:underline" href={`/stocks/${encodeURIComponent(symbol)}`}>Open {symbol} stock detail</Link><Link className="text-primary hover:underline" href={`/news?${newsViewQuery({ ...emptyNewsFilters, ticker: symbol }, "latest", false)}`}>News mentioning {symbol}</Link></div>
            </div>
          </article>;
        })}</section>
      </>}
  </div>;
}
