"use client";
import {useLocale} from "@/lib/i18n";
import { direction } from "@/lib/presentation";
type Props = { label: string; value: unknown; percent?: boolean; signed?: boolean; suffix?: string };
export default function MetricRow({ label, value, percent = false, signed = false, suffix = "" }: Props) {
  const {t,ui,number:localNumber,percent:localPercent}=useLocale();
  const available = typeof value === "number" && Number.isFinite(value);
  return <div className="flex min-w-0 items-center justify-between gap-3 border-b py-3 last:border-0">
    <dt className="text-xs text-muted-foreground">{ui(label)}</dt>
    <dd className={`financial shrink-0 text-right text-[13px] font-medium ${signed ? direction(value) : ""}`} title={!available ? t("Not available from the current provider or insufficient history") : undefined}>
      {percent ? localPercent(value,signed) : localNumber(value)}{available ? suffix : ""}
      {!available && <span className="sr-only"> {t("Not available from the current provider or insufficient history")}</span>}
    </dd>
  </div>;
}
