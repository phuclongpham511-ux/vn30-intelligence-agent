"use client";
import {useLocale} from "@/lib/i18n";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import type { Stock, Market } from "@/lib/types";
import { englishCompanyName } from "@/lib/presentation";
import {LivePrices,LivePrice} from './LivePrice';
import FollowStock from './FollowStock';
export default function StockHeader({ stock, market, available=true }: { stock: Omit<Stock,'id'>; market?: Market; available?:boolean }) {
  const {t,language,date:localDate}=useLocale();
  const name = (language==='vi'?stock.company_name:englishCompanyName(stock))||stock.company_name;
  return <header className="stock-header">
    <Link href="/" className="mb-4 inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground"><ArrowLeft size={13}/>{t("Back to Explore")}</Link>
    <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
      <div className="flex items-center gap-4"><span className="flex size-14 shrink-0 items-center justify-center rounded-xl border border-primary/20 bg-primary/10 text-lg font-semibold text-primary">{stock.symbol.slice(0,3)}</span>
        <div><div className="flex flex-wrap items-center gap-3"><h1 className="text-[32px] leading-none">{stock.symbol}</h1>{stock.exchange && <span className="rounded border px-2 py-1 text-[10px] text-muted-foreground">{stock.exchange}</span>}</div>
          {name && <p className="mt-2 text-sm text-muted-foreground">{name}</p>}
        </div>
      </div>
      <div className="stock-header-actions"><LivePrices symbols={available?[stock.symbol]:[]} interval={15000}><LivePrice symbol={stock.symbol} prominent showSession/></LivePrices><FollowStock ticker={stock.symbol} available={available}/></div>
    </div>
    {market&&<details className="mt-4 text-[11px] text-muted-foreground"><summary className="cursor-pointer">{t("Completed daily analytics")} · {localDate(market.as_of)}</summary><p className="mt-2">{t("Source:")} {market.source}</p></details>}
  </header>;
}
