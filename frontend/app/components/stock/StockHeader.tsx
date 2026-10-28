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
    <Link href="/#market-board" className="mb-2 inline-flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground"><ArrowLeft size={13}/>{t("Market board")}</Link>
    <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
      <div className="stock-company-identity"><span aria-hidden="true" className="stock-symbol-mark">{stock.symbol}</span>
        <div className="min-w-0"><div className="stock-company-heading"><h1>{stock.symbol}</h1>{stock.exchange && <span className="stock-exchange">{stock.exchange}</span>}</div>
          <p className="stock-company-name">{name||t('Company name unavailable')}</p>
        </div>
      </div>
      <div className="stock-header-actions"><LivePrices symbols={available?[stock.symbol]:[]} interval={15000}><LivePrice symbol={stock.symbol} prominent showSession/></LivePrices><FollowStock ticker={stock.symbol} available={available}/></div>
    </div>
    {market&&<details className="mt-4 text-[11px] text-muted-foreground"><summary className="cursor-pointer">{t("Completed daily analytics")} · {localDate(market.as_of)}</summary><p className="mt-2">{t("Source:")} {market.source}</p></details>}
  </header>;
}
