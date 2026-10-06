"use client";
import {useLocale} from "@/lib/i18n";
import { useEffect, useState } from "react";
import { ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, Cell } from "recharts";
import type { FundamentalPeriod } from "@/lib/types";
import { annualChartData, availableSeries, FINANCIAL_LABELS, type FinancialKey } from "@/lib/fundamental-data";
import { direction } from "@/lib/presentation";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";

const axis = { fill:"var(--muted-foreground)", fontSize:11 };
const tip = { background:"var(--card)", border:"1px solid var(--border)", borderRadius:8, color:"var(--foreground)", fontSize:12 };
const profitabilityKeys = ["gross_margin","net_margin","roe"] as const;

function AnnualBars({ rows, field }: { rows: FundamentalPeriod[]; field: "revenue" | "net_profit" }) {
  const {t,ui,number:localNumber,percent:localPercent,compact:localCompact}=useLocale();
  const label = ui(FINANCIAL_LABELS[field]), latest = rows.at(-1);
  const hasData = availableSeries(rows,[field]).length > 0;
  return <article className="panel min-w-0 p-4 sm:p-5" aria-label={t("{label} annual chart",{label})}>
    <div className="mb-4 flex flex-wrap justify-between gap-3"><div><h3>{label}</h3><p className="financial mt-2 text-2xl font-semibold">{localCompact(latest?.[field])} <span className="text-xs font-normal text-muted-foreground">VND</span></p></div>
      <div className="text-right text-xs"><p className="text-muted-foreground">{latest?.period ?? t("Annual")}</p><p className={"financial mt-2 " + direction(latest?.[field + "_growth_yoy" as "revenue_growth_yoy" | "net_profit_growth_yoy"])}>{localPercent(latest?.[field + "_growth_yoy" as "revenue_growth_yoy" | "net_profit_growth_yoy"],true)} {t("YoY")}</p></div></div>
    {hasData ? <div className="h-56 w-full min-w-0"><ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} margin={{top:8,right:4,bottom:0,left:0}} accessibilityLayer>
        <CartesianGrid stroke="var(--border)" vertical={false}/><XAxis dataKey="period" tick={axis} axisLine={false} tickLine={false}/><YAxis width={52} tick={axis} tickFormatter={localCompact} axisLine={false} tickLine={false}/>
        <Tooltip contentStyle={tip} cursor={{fill:"var(--muted)"}} formatter={(value: unknown) => [localNumber(value,0) + " VND",label]} filterNull/>
        <ReferenceLine y={0} stroke="var(--border)"/><Bar dataKey={field} name={label} fill={field === "revenue" ? "var(--chart)" : "var(--chart-secondary)"} radius={[3,3,0,0]} maxBarSize={48} isAnimationActive={false}/>
      </BarChart>
    </ResponsiveContainer></div> : <p className="flex h-56 items-center justify-center px-3 text-center text-sm leading-6 text-muted-foreground">{t("{label} data is unavailable from the current provider.",{label})}</p>}
  </article>;
}

function ReportedData({ rows }: { rows: FundamentalPeriod[] }) {
  const {t,ui,number:localNumber,percent:localPercent}=useLocale();
  const keys = Object.keys(FINANCIAL_LABELS) as FinancialKey[];
  return <details className="panel min-w-0 overflow-hidden"><summary className="px-5 py-4 text-xs font-medium">{t("View reported data")} <span className="ml-2 text-muted-foreground">{t("{count} annual periods",{count:rows.length})}</span></summary>
    <div role="region" aria-label={t("Annual reported evidence")} tabIndex={0} className="table-scroll border-t"><table className="text-xs"><caption className="sr-only">{t("Annual reported financials. Amounts in VND. Dash means unavailable.")}</caption>
      <thead><tr><th scope="col">{t("Period")}</th>{keys.map(key => <th scope="col" key={key}>{ui(FINANCIAL_LABELS[key])}</th>)}<th scope="col">{t("Source")}</th></tr></thead>
      <tbody>{rows.map(row => <tr key={row.period}><td>{row.period}</td>{keys.map(key => <td key={key}>{key === "revenue" || key === "net_profit" ? localNumber(row[key],0) : localPercent(row[key],key.includes("growth"))}</td>)}<td>{row.source}</td></tr>)}</tbody>
    </table></div>
  </details>;
}

export default function FundamentalTrends({ ticker }: { ticker: string }) {
  const {t,ui,percent:localPercent,compact:localCompact}=useLocale();
  const [rows,setRows] = useState<FundamentalPeriod[]>([]);
  const [loading,setLoading] = useState(true), [error,setError] = useState(false), [attempt,setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(false); setRows([]);
    fetch("/api/stocks/" + encodeURIComponent(ticker) + "/fundamentals/history?limit=4",{signal:controller.signal})
      .then(async response => {
        if (!response.ok) throw new Error("Unavailable");
        const data = annualChartData(await response.json());
        if (!controller.signal.aborted) setRows(data);
      }).catch(() => {if (!controller.signal.aborted) setError(true);})
      .finally(() => {if (!controller.signal.aborted) setLoading(false);});
    return () => controller.abort();
  },[ticker,attempt]);
  const profits = availableSeries(rows,profitabilityKeys);
  const growth = availableSeries(rows,["revenue_growth_yoy","net_profit_growth_yoy"]);
  const latest = rows.at(-1);
  return <section className="space-y-4 min-w-0" aria-labelledby="fundamental-trends-title">
    <div className="flex flex-wrap items-end justify-between gap-2"><div><div className="eyebrow mb-1">{t("Company performance")}</div><h2 id="fundamental-trends-title" className="text-xl">{t("Fundamental Trends")}</h2><p className="mt-1 text-xs text-muted-foreground">{t("Annual reported financials")}</p></div><span className="text-xs text-muted-foreground">{rows[0]?.period}{rows.length > 1 ? "–" + latest?.period : ""}{latest ? " · " + latest.source : ""}</span></div>
    {loading ? <div className="grid gap-4 md:grid-cols-2" role="status" aria-label={t("Loading annual financial history")}><Skeleton className="h-72"/><Skeleton className="h-72"/></div> : error ? <div className="panel p-8 text-center" role="alert"><p className="mb-4">{t("Annual financial history is temporarily unavailable.")}</p><Button variant="outline" onClick={() => setAttempt(value => value + 1)}>{t("Retry financials")}</Button></div> : !rows.length ? <p className="panel p-8 text-sm text-muted-foreground">{t("No annual financial observations are available from the current provider.")}</p> : <>
      <div className="grid min-w-0 gap-4 md:grid-cols-2"><AnnualBars rows={rows} field="revenue"/><AnnualBars rows={rows} field="net_profit"/></div>
      <div className="grid min-w-0 gap-4 md:grid-cols-2">
        <article className="panel min-w-0 p-4 sm:p-5" aria-label={t("Historical growth")}><h3>{t("Growth")}</h3><p className="mt-1 text-xs text-muted-foreground">{t("Year-over-year · Positive / negative change")}</p>
          {growth.length ? <div className="mt-4 h-60 min-w-0"><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} margin={{left:0,right:4}} accessibilityLayer>
            <CartesianGrid stroke="var(--border)" vertical={false}/><XAxis dataKey="period" tick={axis} axisLine={false} tickLine={false}/><YAxis width={52} tick={axis} tickFormatter={value => localPercent(value)} axisLine={false} tickLine={false}/>
            <Tooltip contentStyle={tip} cursor={{fill:"var(--muted)"}} formatter={(value: unknown) => localPercent(value,true)} filterNull/><Legend wrapperStyle={{fontSize:11}}/><ReferenceLine y={0} stroke="var(--muted-foreground)"/>
            {growth.map((key,index) => <Bar key={key} dataKey={key} name={ui(FINANCIAL_LABELS[key])} fill="var(--muted-foreground)" fillOpacity={index ? .55 : 1} maxBarSize={24} isAnimationActive={false}>{rows.map(row => <Cell key={row.period} fill={row[key] == null ? "transparent" : row[key]! < 0 ? "var(--negative)" : row[key]! > 0 ? "var(--positive)" : "var(--muted-foreground)"}/>)}</Bar>)}
          </BarChart></ResponsiveContainer></div> : <p className="flex h-60 items-center justify-center text-sm text-muted-foreground">{t("Comparable prior-year data is unavailable.")}</p>}
        </article>
        <article className="panel min-w-0 p-4 sm:p-5" aria-label={t("Historical profitability")}><h3>{t("Profitability")}</h3><p className="mt-1 text-xs text-muted-foreground">{t("Reported margins and return on equity")}</p>
          {profits.length ? <div className="mt-4 h-60 min-w-0"><ResponsiveContainer width="100%" height="100%"><LineChart data={rows} margin={{left:0,right:12}} accessibilityLayer>
            <CartesianGrid stroke="var(--border)" vertical={false}/><XAxis dataKey="period" tick={axis} axisLine={false} tickLine={false}/><YAxis width={52} tick={axis} tickFormatter={value => localPercent(value)} axisLine={false} tickLine={false}/>
            <Tooltip contentStyle={tip} formatter={(value: unknown) => localPercent(value)} filterNull/><Legend wrapperStyle={{fontSize:11}}/>
            {profits.map(key => <Line key={key} dataKey={key} name={ui(FINANCIAL_LABELS[key])} stroke={key === "gross_margin" ? "var(--chart)" : key === "net_margin" ? "var(--chart-secondary)" : "var(--ma20)"} strokeWidth={2} dot={{r:3}} connectNulls={false} isAnimationActive={false}/>)}
          </LineChart></ResponsiveContainer></div> : <p className="flex h-60 items-center justify-center px-3 text-center text-sm text-muted-foreground">{t("Profitability data is unavailable from the current provider.")}</p>}
        </article>
      </div>
      <div className="panel p-4 sm:p-5"><div className="mb-4 flex flex-wrap justify-between gap-2"><h3>{t("Latest reported ·")} {latest?.period}</h3><span className="text-[10px] text-muted-foreground">{t("— Unavailable · Amounts in VND")}</span></div>
        <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-5">{(["revenue","net_profit","gross_margin","net_margin","roe"] as const).map(key => <div key={key}><dt className="text-xs text-muted-foreground">{ui(FINANCIAL_LABELS[key])}</dt><dd className="financial mt-1 font-medium">{key === "revenue" || key === "net_profit" ? localCompact(latest?.[key]) : localPercent(latest?.[key])}</dd></div>)}</dl>
        <p className="mt-4 text-[11px] leading-5 text-muted-foreground">{t("Only reported observations are plotted. Missing values are not zero.")}{!profits.includes("roe") ? " "+t("ROE is unavailable and is omitted from the chart.") : ""}{!availableSeries(rows,["revenue"]).length ? " "+t("Generic revenue and margin fields may be unavailable for this sector.") : ""}</p>
      </div>
      <ReportedData rows={rows}/>
    </>}
  </section>;
}
