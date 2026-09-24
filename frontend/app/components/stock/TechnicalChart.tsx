"use client";
import { useEffect, useRef, useState } from "react";
import { useTheme } from "next-themes";
import { createChart, CandlestickSeries, HistogramSeries, LineSeries, ColorType, type IChartApi, type ISeriesApi, type MouseEventParams } from "lightweight-charts";
import type { TechnicalBar } from "@/lib/types";
import { rangeDates, technicalSeries, type Range } from "@/lib/chart-data";
import { formatNumber } from "@/lib/presentation";
import TechnicalToolbar, { type Indicators } from "./TechnicalToolbar";
import TechnicalLegend from "./TechnicalLegend";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";

type ChartRefs = { chart: IChartApi; candles: ISeriesApi<"Candlestick">; ma20: ISeriesApi<"Line">; ma50: ISeriesApi<"Line">; volume?: ISeriesApi<"Histogram">; rsi?: ISeriesApi<"Line"> };
export default function TechnicalChart({ ticker, onRows }: { ticker: string; onRows: (rows: TechnicalBar[]) => void }) {
  const host = useRef<HTMLDivElement>(null);
  const api = useRef<ChartRefs | null>(null);
  const currentRows = useRef<TechnicalBar[]>([]);
  const [rows, setRows] = useState<TechnicalBar[]>([]);
  const [selected, setSelected] = useState<TechnicalBar | null>(null);
  const [range, setRange] = useState<Range>("6M");
  const [attempt, setAttempt] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [indicators, setIndicators] = useState<Indicators>({MA20:true, MA50:true, Volume:true, RSI:true});
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
      autoSize: true, height: 520, layout: { attributionLogo: true, panes: { enableResize: false } },
      localization: { locale: "en-US" },
      rightPriceScale: { minimumWidth: 65, borderVisible: false },
      timeScale: { borderVisible: false, timeVisible: false },
      handleScroll: { vertTouchDrag: false },
    });
    const candles = chart.addSeries(CandlestickSeries, { borderVisible: false, priceFormat: { type: "price", precision: 0, minMove: 1 } }, 0);
    const ma20 = chart.addSeries(LineSeries, { lineWidth: 1, priceLineVisible: false, lastValueVisible: false }, 0);
    const ma50 = chart.addSeries(LineSeries, { lineWidth: 1, priceLineVisible: false, lastValueVisible: false }, 0);
    const crosshair = (event: MouseEventParams) => {
      const candle = event.seriesData.get(candles);
      setSelected(candle ? currentRows.current.find(row => row.date === String(candle.time)) ?? null : null);
    };
    chart.subscribeCrosshairMove(crosshair);
    api.current = { chart, candles, ma20, ma50 };
    return () => { chart.unsubscribeCrosshairMove(crosshair); chart.remove(); api.current = null; };
  }, []);

  useEffect(() => {
    if (!api.current || !host.current) return;
    const style = getComputedStyle(host.current);
    const color = (token: string) => style.getPropertyValue(token).trim();
    const refs = api.current;
    const { chart, candles, ma20, ma50 } = refs;
    if (!indicators.Volume && refs.volume) { chart.removeSeries(refs.volume); refs.volume = undefined; }
    if (!indicators.RSI && refs.rsi) { chart.removeSeries(refs.rsi); refs.rsi = undefined; }
    if (indicators.Volume && !refs.volume) {
      refs.volume = chart.addSeries(HistogramSeries, { priceFormat: { type: "volume" }, priceLineVisible: false, lastValueVisible: false }, chart.panes().length);
      refs.volume.getPane().moveTo(1);
    }
    if (indicators.RSI && !refs.rsi) {
      refs.rsi = chart.addSeries(LineSeries, { lineWidth: 1, priceLineVisible: false, lastValueVisible: false, priceFormat: { type: "price", precision: 1, minMove: .1 }, autoscaleInfoProvider: () => ({priceRange:{minValue:0,maxValue:100}}) }, chart.panes().length);
      for (const price of [30,70]) refs.rsi.createPriceLine({price, color:color("--muted-foreground"), lineWidth:1, lineStyle:2, axisLabelVisible:true, title:String(price)});
    }
    chart.panes()[0].setStretchFactor(.65);
    refs.volume?.getPane().setStretchFactor(.15);
    refs.rsi?.getPane().setStretchFactor(.20);
    chart.applyOptions({
      layout: { background: { type: ColorType.Solid, color: color("--card") }, textColor: color("--muted-foreground"), panes: { separatorColor: color("--border") } },
      grid: { vertLines: { visible: false }, horzLines: { color: color("--border") } },
      crosshair: { vertLine: { labelBackgroundColor: color("--muted") }, horzLine: { labelBackgroundColor: color("--muted") } },
    });
    candles.applyOptions({ upColor: color("--positive"), downColor: color("--negative"), wickUpColor: color("--positive"), wickDownColor: color("--negative") });
    const data = technicalSeries(rows, color("--positive"), color("--negative"));
    candles.applyOptions({priceFormat:{type:"custom",minMove:1,formatter:(value: number) => formatNumber(value,0)}});
    candles.setData(data.candles); refs.volume?.setData(data.volume);
    ma20.applyOptions({visible:indicators.MA20,color:color("--ma20")});
    ma50.applyOptions({visible:indicators.MA50,color:color("--ma50")});
    ma20.setData(data.ma20); ma50.setData(data.ma50);
    refs.rsi?.applyOptions({color:color("--rsi")}); refs.rsi?.setData(data.rsi14);
  }, [rows, resolvedTheme, indicators]);

  useEffect(() => {
    currentRows.current = rows; setSelected(null); onRows(rows);
    if (rows.length) api.current?.chart.timeScale().fitContent();
  }, [rows, onRows]);

  const bar = selected ?? rows.at(-1);
  return <section className="panel min-w-0 overflow-hidden" aria-label="Technical chart">
    <div className="space-y-3 border-b p-4 sm:p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2"><h2>Technical Chart</h2><span className="text-xs text-muted-foreground">Daily OHLCV · VND</span></div>
      <TechnicalToolbar range={range} onRange={setRange} indicators={indicators} onIndicators={setIndicators} reset={() => api.current?.chart.timeScale().fitContent()}/>
      <TechnicalLegend bar={bar}/>
    </div>
    <div className="relative">
      <div ref={host} className="h-[520px] w-full" role="img" aria-label={ticker + " daily candlesticks, MA20, MA50, volume and RSI14; values are available in the technical data table"}/>
      {(loading || error || !rows.length) && <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-card p-6" role="status">
        {loading ? <><Skeleton className="h-48 w-full"/><p className="text-sm text-muted-foreground">Loading technical history…</p></> : error ? <><p>Technical history is temporarily unavailable.</p><Button variant="outline" onClick={() => setAttempt(value => value + 1)}>Retry chart</Button></> : <p>No daily observations are available for this period.</p>}
      </div>}
    </div>
    <p className="px-4 py-2 text-[10px] text-muted-foreground">Price / Volume / RSI panes · RSI reference levels: 30 and 70 · Indicators warm up within the selected period; unavailable values are omitted.</p>
    <div className="flex flex-wrap justify-between gap-2 border-t px-4 py-3 text-[10px] text-muted-foreground"><span>{rows.length} sessions · {rows[0]?.source ?? "Provider data"} · Drag to pan / scroll to zoom</span><a href="https://www.tradingview.com/" target="_blank" rel="noreferrer" className="underline">TradingView Lightweight Charts™ · Copyright (с) 2025 TradingView, Inc.</a></div>
  </section>;
}
