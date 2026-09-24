"use client";
import { useEffect, useRef, useState } from "react";
import { useTheme } from "next-themes";
import { createChart, CandlestickSeries, HistogramSeries, ColorType, type IChartApi, type ISeriesApi, type MouseEventParams } from "lightweight-charts";
import type { TechnicalBar } from "@/lib/types";
import { rangeDates, technicalSeries, type Range } from "@/lib/chart-data";
import { formatNumber } from "@/lib/presentation";
import TechnicalToolbar from "./TechnicalToolbar";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";

type ChartRefs = { chart: IChartApi; candles: ISeriesApi<"Candlestick">; volume: ISeriesApi<"Histogram"> };
export default function TechnicalChart({ ticker }: { ticker: string }) {
  const host = useRef<HTMLDivElement>(null);
  const api = useRef<ChartRefs | null>(null);
  const currentRows = useRef<TechnicalBar[]>([]);
  const [rows, setRows] = useState<TechnicalBar[]>([]);
  const [selected, setSelected] = useState<TechnicalBar | null>(null);
  const [range, setRange] = useState<Range>("6M");
  const [attempt, setAttempt] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(false); setRows([]); setSelected(null);
    const query = new URLSearchParams(rangeDates(range));
    fetch("/api/stocks/" + encodeURIComponent(ticker) + "/technical-history?" + query, { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error("Unavailable");
        const data: TechnicalBar[] = await response.json();
        if (!controller.signal.aborted) setRows(data);
      })
      .catch(() => { if (!controller.signal.aborted) setError(true); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [ticker, range, attempt]);

  useEffect(() => {
    if (!host.current) return;
    const chart = createChart(host.current, {
      autoSize: true, height: 480, layout: { attributionLogo: true, panes: { enableResize: false } },
      localization: { locale: "en-US", priceFormatter: (value: number) => formatNumber(value, 0) },
      rightPriceScale: { minimumWidth: 65, borderVisible: false },
      timeScale: { borderVisible: false, timeVisible: false },
      handleScroll: { vertTouchDrag: false },
    });
    const candles = chart.addSeries(CandlestickSeries, { borderVisible: false, priceFormat: { type: "price", precision: 0, minMove: 1 } }, 0);
    const volume = chart.addSeries(HistogramSeries, { priceFormat: { type: "volume" }, priceLineVisible: false, lastValueVisible: false }, 1);
    chart.panes()[0].setStretchFactor(.8);
    chart.panes()[1].setStretchFactor(.2);
    const crosshair = (event: MouseEventParams) => {
      const candle = event.seriesData.get(candles);
      setSelected(candle ? currentRows.current.find(row => row.date === String(candle.time)) ?? null : null);
    };
    chart.subscribeCrosshairMove(crosshair);
    api.current = { chart, candles, volume };
    return () => { chart.unsubscribeCrosshairMove(crosshair); chart.remove(); api.current = null; };
  }, []);

  useEffect(() => {
    if (!api.current || !host.current) return;
    const style = getComputedStyle(host.current);
    const color = (token: string) => style.getPropertyValue(token).trim();
    const { chart, candles, volume } = api.current;
    chart.applyOptions({
      layout: { background: { type: ColorType.Solid, color: color("--card") }, textColor: color("--muted-foreground"), panes: { separatorColor: color("--border") } },
      grid: { vertLines: { visible: false }, horzLines: { color: color("--border") } },
      crosshair: { vertLine: { labelBackgroundColor: color("--muted") }, horzLine: { labelBackgroundColor: color("--muted") } },
    });
    candles.applyOptions({ upColor: color("--positive"), downColor: color("--negative"), wickUpColor: color("--positive"), wickDownColor: color("--negative") });
    const data = technicalSeries(rows, color("--positive"), color("--negative"));
    candles.setData(data.candles); volume.setData(data.volume);
  }, [rows, resolvedTheme]);

  useEffect(() => {
    currentRows.current = rows; setSelected(null);
    if (rows.length) api.current?.chart.timeScale().fitContent();
  }, [rows]);

  const bar = selected ?? rows.at(-1);
  return <section className="panel min-w-0 overflow-hidden" aria-label="Technical chart">
    <div className="space-y-3 border-b p-4 sm:p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2"><h2>Technical Chart</h2><span className="text-xs text-muted-foreground">Daily OHLCV · VND</span></div>
      <TechnicalToolbar range={range} onRange={setRange} reset={() => api.current?.chart.timeScale().fitContent()}/>
      <div className="financial flex min-h-10 flex-wrap gap-x-4 gap-y-1 text-xs" aria-label="Selected candle values">
        <span className="text-muted-foreground">{bar?.date ?? "No observation"}</span>
        {(["open", "high", "low", "close", "volume"] as const).map((key, index) => <span key={key}><span className="mr-1 text-muted-foreground">{["O", "H", "L", "C", "Volume"][index]}</span>{formatNumber(bar?.[key], 0)}</span>)}
      </div>
    </div>
    <div className="relative">
      <div ref={host} className="h-[480px] w-full" role="img" aria-label={ticker + " daily candlesticks and volume; values are available in the data table"}/>
      {(loading || error || !rows.length) && <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-card p-6" role="status">
        {loading ? <><Skeleton className="h-48 w-full"/><p className="text-sm text-muted-foreground">Loading technical history…</p></> : error ? <><p>Technical history is temporarily unavailable.</p><Button variant="outline" onClick={() => setAttempt(value => value + 1)}>Retry chart</Button></> : <p>No daily observations are available for this period.</p>}
      </div>}
    </div>
    <div className="flex flex-wrap justify-between gap-2 border-t px-4 py-3 text-[10px] text-muted-foreground"><span>{rows.length} sessions · {rows[0]?.source ?? "Provider data"} · Drag to pan / scroll to zoom</span><a href="https://www.tradingview.com/" target="_blank" rel="noreferrer" className="underline">TradingView Lightweight Charts™ · Copyright (с) 2025 TradingView, Inc.</a></div>
  </section>;
}
