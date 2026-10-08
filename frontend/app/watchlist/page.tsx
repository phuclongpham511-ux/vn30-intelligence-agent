"use client";
import {useLocale} from "@/lib/i18n";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { MascotState } from "../components/mascot/Mascot";
import SourceCoverage from "../components/news/SourceCoverage";
import ArticleRow from "../components/news/ArticleRow";
import NewsThumbnail from "../components/news/NewsThumbnail";
import StockSearch from "../components/stock/StockSearch";
import { useStocks } from "../components/stock/StockUniverse";
import { englishCompanyName } from "@/lib/presentation";
import { emptyNewsFilters, newsViewQuery } from "@/lib/news";
import { emptyWatchlist, readWatchlist, followStock, unfollowStock, markReviewed, unreviewedStories, loadWatchlistUpdates, watchlistStorageKey, markCommunityReviewed, unreviewedThreads } from "@/lib/watchlist";
import type { WatchlistState, WatchlistUpdates } from "@/lib/watchlist";
import { loadCommunityUpdates } from "@/lib/community";
import type { CommunityUpdate } from "@/lib/community";
import { CommunityDiscussions } from "../components/stock/StockCommunity";
import {LivePrices,LivePrice} from '../components/stock/LivePrice';

export default function WatchlistPage() {
  const {t,ui,date:localDate}=useLocale();
  const universe = useStocks();
  const [state, setState] = useState<WatchlistState>(emptyWatchlist);
  const [ready, setReady] = useState(false);
  const [storageError, setStorageError] = useState(false);
  const [selected, setSelected] = useState("");
  const [data, setData] = useState<WatchlistUpdates | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [community, setCommunity] = useState<CommunityUpdate[] | null>(null);
  const [communityLoading, setCommunityLoading] = useState(false);
  const [communityError, setCommunityError] = useState(false);
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
  useEffect(() => {
    if (!ready || !symbolsKey) { setCommunity(null); setCommunityLoading(false); return; }
    const controller = new AbortController();
    const load = async () => {
      setCommunityLoading(true); setCommunityError(false); setCommunity(null);
      try {
        const result = await loadCommunityUpdates(symbolsKey.split(","), controller.signal);
        if (!controller.signal.aborted) setCommunity(result);
      } catch { if (!controller.signal.aborted) setCommunityError(true); }
      finally { if (!controller.signal.aborted) setCommunityLoading(false); }
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
  const communityCount = new Set(community?.flatMap(row => row.data?.items.map(thread => thread.id) || []) || []).size;
  const newCommunityCount = new Set(community?.flatMap(row => unreviewedThreads(row.data?.items || [], state.communitySeen[row.symbol])) || []).size;
  const communityIncomplete = community?.some(row => !row.data || row.data.coverage_partial);
  const communityAvailable = community?.some(row => row.data !== null);
  return <LivePrices symbols={ready?state.symbols:[]} interval={20000}><div className="page-stack">
    <div className="flex items-start justify-between gap-3"><div><div className="eyebrow mb-3">{t("Workspace / Watchlist")}</div><h1>{t("Watchlist")}</h1><p className="mt-2 text-sm text-muted-foreground">{t("What changed for the stocks you follow?")}</p></div>
      <Button variant="outline" disabled={!ready || !state.symbols.length || loading || communityLoading} onClick={() => setAttempt(value => value + 1)}>{t("Refresh updates")}</Button>
    </div>
    <p className="text-xs text-muted-foreground">{t("Saved in this browser only · No cross-device sync. News stories and Community discussions have separate review states. News counts describe recent Stories; Community counts describe same-day discussions.")}</p>
    {storageError && <p role="alert" className="rounded border p-3 text-sm">{t("Browser storage is unavailable or saved data cannot be read. Your saved Watchlist has not been overwritten. Reload to retry.")}</p>}
    <form aria-label={t("Follow a stock")} className="flex flex-wrap items-end gap-3" onSubmit={event => { event.preventDefault(); if (available.some(stock => stock.symbol === selected) && save(followStock(state, selected))) setSelected(""); }}>
      <div className="min-w-0 w-full sm:w-80"><p className="mb-1 text-xs">{t("Stock to follow")}</p><StockSearch stocks={available} label="Stock to follow" onSelect={setSelected} disabled={!ready || universe.loading || !!universe.error || storageError || state.symbols.length>=50}/></div>
      <Button disabled={!selected || storageError || !ready || state.symbols.length>=50}>{selected?t("Follow {ticker}",{ticker:selected}):t("Follow stock")}</Button>
      <Link href="/" className="py-2 text-xs text-primary hover:underline">{t("Find more stocks in Explore")}</Link>
    </form>
    {universe.error && <p role="alert" className="text-sm">{t("Equity metadata could not be loaded.")} <button className="text-primary underline" onClick={universe.refresh}>{t("Retry stocks")}</button></p>}
    {state.symbols.length >= 50 && <p className="text-xs text-muted-foreground">{t("This browser Watchlist supports up to 50 stocks.")}</p>}
    {!ready ? <MascotState state="loading" role="status">{t("Loading your Watchlist…")}</MascotState>
      : !state.symbols.length ? !storageError && <section className="panel p-5"><MascotState state="emptyWatchlist"><div><h2 className="text-sm">{t("No stocks followed yet")}</h2><p className="mt-1">{t("Choose a stock above to monitor recent developments.")}</p></div></MascotState></section>
      : <>
        <SourceCoverage/>
        {loading ? <MascotState state="loading" role="status">{t("Checking recent developments…")}</MascotState>
          : error ? <MascotState state="dataUnavailable" role="alert">{t("Watchlist updates are temporarily unavailable. Counts are unknown.")} <button className="text-primary underline" onClick={() => setAttempt(value => value + 1)}>{t("Retry updates")}</button></MascotState>
          : data && <div className="flex flex-wrap gap-x-5 gap-y-2 border-y py-3 text-sm" role="status"><span>{t("News: {count} observed recent developments",{count:recentCount})}</span><span>{t("{count} unreviewed News developments",{count:newCount})}</span>{unavailableCount > 0 && <span>{t("{count} stocks unavailable · totals incomplete",{count:unavailableCount})}</span>}<span className="text-xs text-muted-foreground">{t("Ingested in the last 72 hours · Checked")} {localDate(data.as_of,true)}</span></div>}
        <div role="status" className="text-sm">{communityLoading ? t("Checking Community discussions…")
          : communityError || (community !== null && !communityAvailable) ? t("Community counts are unknown. Retry updates to check again.")
          : community && <><span>{t("Community: {count} same-day discussions · {fresh} unreviewed",{count:communityCount,fresh:newCommunityCount})}</span>{communityIncomplete && <span className="text-muted-foreground"> · {t("source coverage incomplete or unavailable")}</span>}</>}</div>
        <section className="panel divide-y" aria-label={t("Watched stocks")}>{state.symbols.map(symbol => {
          const row = data?.stocks.find(stock => stock.symbol === symbol);
          const developments = row?.developments;
          const fresh = developments ? unreviewedStories(developments, state.seen[symbol]) : [];
          const reviewedBefore = Object.hasOwn(state.seen, symbol);
          const discussions = community?.find(stock => stock.symbol === symbol)?.data || null;
          return <article key={symbol} className="grid gap-4 p-5 md:grid-cols-[170px_minmax(0,1fr)]" aria-label={t("{ticker} monitoring",{ticker:symbol})}>
            <div><Link href={`/stocks/${encodeURIComponent(symbol)}`} className="text-lg font-semibold text-primary hover:underline">{symbol}</Link><p className="mt-1 text-xs text-muted-foreground">{englishCompanyName(universe.stocks.find(stock => stock.symbol === symbol) || { company_name: null })}</p>
              <div className="mt-3"><LivePrice symbol={symbol}/></div><button className="mt-3 text-xs text-muted-foreground underline" aria-label={t("Remove {ticker} from Watchlist",{ticker:symbol})} disabled={storageError} onClick={() => save(unfollowStock(state, symbol))}>{t("Remove")}</button>
            </div>
            <div className="min-w-0">
              {loading ? <p className="text-sm text-muted-foreground">{t("Checking news…")}</p>
                : error ? <p className="text-sm text-muted-foreground">{t("Development count unavailable.")}</p>
                : row?.status === "unavailable" ? <p className="text-sm">{t("Stock data is unavailable. This is not a no-change result.")}</p>
                : developments && <>
                  <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-sm">{t("News · {count} recent developments · {review}",{count:developments.length,review:reviewedBefore?t("{count} new since your review",{count:fresh.length}):t("Not reviewed yet")})}</h2>
                    {fresh.length > 0 && <button className="text-xs text-primary underline disabled:opacity-50" disabled={storageError} aria-label={t("Mark {ticker} reviewed",{ticker:symbol})} onClick={() => save(markReviewed(state, symbol, developments))}>{t("Mark reviewed")}</button>}
                  </div>
                  {!developments.length ? <p className="mt-3 text-sm text-muted-foreground">{t("No recent ticker-matched stories ingested. This does not prove that nothing changed; coverage or tags may be incomplete.")}</p>
                    : <ul className="mt-3 divide-y">{developments.slice(0,3).map(story => <NewsThumbnail key={story.story_id} images={story.articles.map(article=>article.thumbnail_url)} revision={story.articles.map(article=>article.last_seen_at||'').join('|')}>{image=><li className="py-3 first:pt-0"><div className="flex items-start gap-3">{image}<div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground"><span>{t(story.source_count===1?"{count} independent source":"{count} independent sources",{count:story.source_count})}</span><span>{t("First matched")} <time dateTime={story.first_seen_at}>{localDate(story.first_seen_at,true)}</time></span>{fresh.includes(story.story_id) && <span className="text-primary">{ui(reviewedBefore?"New":"Unreviewed")}</span>}</div>
                      <h3 className="mt-1 text-sm leading-6">{story.title}</h3><details className="mt-2 text-xs"><summary className="cursor-pointer text-primary">{t("View source evidence")}</summary>{story.articles.map(article => <ArticleRow key={article.id} article={article}/>)}</details></div></div>
                    </li>}</NewsThumbnail>)}</ul>}
                  {developments.length > 3 && <p className="text-xs text-muted-foreground">{t("Showing 3 of {count} developments. Open News for more reporting.",{count:developments.length})}</p>}
                </>}
              <div className="mt-5 border-t pt-4"><CommunityDiscussions ticker={symbol} data={discussions}
                loading={communityLoading} error={communityError || (!communityLoading && community !== null && !discussions)}
                retry={() => setAttempt(value => value + 1)} seen={state.communitySeen[symbol]} storageError={storageError}
                review={() => { if (discussions) save(markCommunityReviewed(state, symbol, discussions.items)); }}/></div>
              <div className="mt-3 flex flex-wrap gap-4 text-xs"><Link className="text-primary hover:underline" href={`/stocks/${encodeURIComponent(symbol)}`}>{t("Open {ticker} stock detail",{ticker:symbol})}</Link><Link className="text-primary hover:underline" href={`/news?${newsViewQuery({ ...emptyNewsFilters, ticker: symbol }, "company")}`}>{t("News mentioning {ticker}",{ticker:symbol})}</Link></div>
            </div>
          </article>;
        })}</section>
      </>}
  </div></LivePrices>;
}
