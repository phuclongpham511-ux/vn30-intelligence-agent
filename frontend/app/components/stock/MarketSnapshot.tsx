"use client";
import {useLocale} from "@/lib/i18n";
import type { Market } from "@/lib/types";
import { direction } from "@/lib/presentation";
export default function MarketSnapshot({ market }: { market: Market }) {
  const {t,ui,number:localNumber,percent:localPercent}=useLocale();
  const metrics = [
    ["Daily return",market.daily_return,true], ["5D return",market.return_5d,true],
    ["20D return",market.return_20d,true], ["Relative volume",market.relative_volume_20d,false],
    ["20D volatility",market.volatility_20d,true], ["20D drawdown",market.drawdown_from_20d_high,true],
  ] as const;
  return <section className="panel p-4 sm:p-5" aria-label={t("Market context")}>
    <div className="mb-4 flex flex-wrap items-center justify-between gap-2"><h2>{t("Market context")}</h2><p className="text-[10px] text-muted-foreground">{t("Trading-session returns · Annualized volatility")}</p></div>
    <dl className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">{metrics.map(([label,value,percent]) => <div key={ui(label)} className="min-w-0"><dt className="mb-1 text-xs text-muted-foreground">{ui(label)}</dt><dd className={"financial text-lg font-medium " + (label.includes("return") || label.includes("drawdown") ? direction(value) : "")}>{percent ? localPercent(value,label.includes("return") || label.includes("drawdown")) : localNumber(value) + (typeof value === "number" ? "×" : "")}</dd></div>)}</dl>
  </section>;
}
