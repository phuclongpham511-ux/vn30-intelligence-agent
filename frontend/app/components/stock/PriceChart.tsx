"use client";
import { useId } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartNoAxesCombined } from "lucide-react";
import type { Bar } from "@/lib/types";
import { formatDate, formatNumber } from "@/lib/presentation";
import { Card } from "../ui/card";

export default function PriceChart({ bars, source }: { bars: Bar[]; source: string }) {
  const gradient = "price-" + useId().replaceAll(":", "");
  return <Card className="min-w-0 gap-0 overflow-hidden py-0 shadow-none">
    <div className="flex items-center justify-between gap-3 px-5 pb-2 pt-5"><div><h2>Price history</h2><p className="mt-1 text-xs text-muted-foreground">Daily closing price · VND</p></div><span className="rounded-md border bg-muted/40 px-2.5 py-1 text-[10px] text-muted-foreground">180-day window</span></div>
    <div className="h-[310px] min-w-0 px-2 pt-5 sm:h-[330px]" aria-label="Daily closing price chart">
      {!bars.length ? <div className="flex h-full flex-col items-center justify-center gap-3 text-muted-foreground"><ChartNoAxesCombined/><p className="text-sm">No price history available.</p></div> :
      <ResponsiveContainer width="100%" height="100%" minWidth={0} initialDimension={{ width: 600, height: 300 }}>
        <AreaChart data={bars} margin={{ top: 5, right: 16, left: 0, bottom: 0 }} accessibilityLayer>
          <defs><linearGradient id={gradient} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="var(--chart)" stopOpacity={0.24}/><stop offset="100%" stopColor="var(--chart)" stopOpacity={0.01}/></linearGradient></defs>
          <CartesianGrid vertical={false} stroke="var(--border)" strokeDasharray="3 5"/>
          <XAxis dataKey="date" axisLine={false} tickLine={false} minTickGap={50} tick={{ fill: "var(--muted-foreground)", fontSize: 10 }} tickFormatter={value => formatDate(value,true)} dy={8} height={35}/>
          <YAxis orientation="right" axisLine={false} tickLine={false} width={54} domain={["auto","auto"]} tick={{ fill: "var(--muted-foreground)", fontSize: 10 }} tickFormatter={value => new Intl.NumberFormat("en-US",{ notation:"compact", maximumFractionDigits:1 }).format(value)}/>
          <Tooltip cursor={{ stroke: "var(--muted-foreground)", strokeDasharray: "3 3" }} content={({ active, payload, label }) => active && payload?.length ? <div className="rounded-lg border bg-card px-3 py-2.5 text-xs shadow-lg"><p className="mb-1 text-muted-foreground">{formatDate(String(label))}</p><p className="financial font-semibold">{formatNumber(payload[0].value)} VND</p></div> : null}/>
          <Area type="linear" dataKey="close" name="Close" stroke="var(--chart)" strokeWidth={2} fill={`url(#${gradient})`} isAnimationActive={false} activeDot={{ r: 4, fill: "var(--chart)", stroke: "var(--card)", strokeWidth: 2 }}/>
        </AreaChart>
      </ResponsiveContainer>}
    </div>
    <div className="flex flex-wrap justify-between gap-2 border-t px-5 py-3 text-[10px] text-muted-foreground"><span>{bars.length ? `${formatDate(bars[0].date,true)} — ${formatDate(bars[bars.length-1].date)}` : "No reporting dates"}</span><span>{bars.length} sessions · {source}</span></div>
  </Card>;
}
