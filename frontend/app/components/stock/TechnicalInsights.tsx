"use client";
import { useEffect, useState } from "react";
import { useLocale } from "@/lib/i18n";
import { loadTechnical, type TechnicalResponse } from "@/lib/technical-insights";

const labels = {
  abnormal_price_move: "Unusual price movement", unusual_volume: "Unusual trading volume",
  ma_cross: "Moving average transition", rsi_regime_entry: "RSI regime transition",
  bollinger_lower_reversal_volume: "Lower Bollinger reversal with volume",
  bollinger_upper_reversal_volume: "Upper Bollinger reversal with volume",
} as const;
export function TechnicalInsightsView({ticker, data, loading, error, retry, sectionId='stock-technical-insights'}: {
  ticker: string; data: TechnicalResponse | null; loading: boolean; error: boolean; retry: () => void; sectionId?:string;
}) {
  const {t,ui,date} = useLocale();
  const accepted = !loading && !error && data?.kind === "provisional_packet" ? data : null;
  const diagnostic = !loading && !error && data?.kind === "diagnostic" ? data : null;
  const retracted = diagnostic?.reason_codes.some(code => /revis|retract|supersed|definition_changed/.test(code));
  return <section id={sectionId} aria-label={t("Technical Insights")} className="scroll-mt-24 rounded-xl border p-4 sm:p-5">
    <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-sm font-medium">{t("Technical Insights")}</h2>
      {accepted && <span className="rounded border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[10px] font-medium text-amber-700 dark:text-amber-300">PROVISIONAL</span>}</div>
    {loading ? <p role="status" className="mt-3 text-sm text-muted-foreground">{t("Loading Technical Insights…")}</p>
      : error ? <p role="alert" className="mt-3 text-sm">{t("Technical Insights are temporarily unavailable.")} <button onClick={retry} className="text-primary underline">{t("Retry")}</button></p>
      : accepted ? <>
        <p className="mt-2 text-xs text-muted-foreground">{t("Evaluated session")}: <time dateTime={accepted.packet.trading_session}>{date(accepted.packet.trading_session)}</time> · {t("Delayed session review; corrections remain possible.")}</p>
        <p className="mt-1 text-xs text-muted-foreground">{t("Source checked")}: <time dateTime={accepted.last_checked_at}>{date(accepted.last_checked_at,true)}</time> · {t("Vietnam time")}{accepted.freshness === "STALE" && <span className="text-amber-700 dark:text-amber-300"> · {t("Source check overdue")}</span>}</p>
        {accepted.packet.packet_state === "NO_MEANINGFUL_TECHNICAL_CHANGE" ? <div className="mt-4"><p className="text-sm font-medium">{t("No meaningful technical change")}</p><p className="mt-1 text-sm text-muted-foreground">{t("No qualifying events met the attention threshold for this evaluated session.")}</p></div>
          : accepted.packet.packet_state === "TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE" ? <p className="mt-4 text-sm text-muted-foreground">{t("Technical evidence is incomplete; insights are withheld.")}</p>
          : <ol className="mt-4 divide-y">{accepted.packet.top_insights.slice(0,3).map(event => <li key={event.event_id} data-insight={event.event_id} className="py-3 first:pt-0">
            <h3 className="text-sm font-medium">{ui(labels[event.event_type as keyof typeof labels] || event.event_type)}</h3>
            <p className="mt-1 text-xs text-muted-foreground">{t("Observed direction")}: {event.direction}</p>
            <details className="mt-2 text-xs"><summary className="cursor-pointer text-primary">{t("Inspect technical evidence")}</summary>
              <pre className="mt-2 whitespace-pre-wrap break-all rounded bg-muted/40 p-3">{JSON.stringify({direction:event.direction,evidence:event.evidence,evidence_refs:event.evidence_refs},null,2)}</pre>
            </details></li>)}</ol>}
        <details className="mt-4 text-xs text-muted-foreground"><summary className="cursor-pointer">{t("Data provenance and checks")} · {t("Version")} {accepted.snapshot_version}</summary>
          <p className="mt-2">{t("Accepted at")}: {date(accepted.persisted_at,true)} · {t("Next source check due")}: {date(accepted.next_check_due_at,true)} · {t("Vietnam time")}</p>
          <pre className="mt-2 whitespace-pre-wrap break-all rounded bg-muted/40 p-3">{JSON.stringify({snapshot_id:accepted.snapshot_id,packet_id:accepted.packet.packet_id,data_provenance:accepted.packet.data_provenance,family_checks:accepted.packet.family_checks,limitations:accepted.packet.limitations},null,2)}</pre>
        </details>
      </> : <div className="mt-3 text-sm text-muted-foreground"><p>{t(retracted ? "The provisional result was withdrawn. Insights remain unavailable until corrected evidence is accepted." : "Technical evidence is not yet accepted for this ticker.")}</p>
        {diagnostic?.requested_session && <p className="mt-1 text-xs">{t("Evaluated session")}: {date(diagnostic.requested_session)}</p>}
        {diagnostic && <details className="mt-2 text-xs"><summary className="cursor-pointer">{t("Evidence diagnostics")}</summary><p className="mt-2 break-words">{diagnostic.readiness_status} · {diagnostic.reason_codes.join(" · ")}</p></details>}</div>}
  </section>;
}
export default function TechnicalInsights({ticker}: {ticker:string}) {
  const [state,setState] = useState<{ticker:string;data:TechnicalResponse|null;loading:boolean;error:boolean}>({ticker,data:null,loading:true,error:false});
  const [attempt,setAttempt] = useState(0);
  useEffect(() => {
    let disposed = false;
    let current: AbortController | null = null;
    const refresh = async () => {
      current?.abort(); const controller = new AbortController(); current = controller;
      setState({ticker,data:null,loading:true,error:false});
      try {
        const data = await loadTechnical(ticker,controller.signal);
        if (!disposed && !controller.signal.aborted) setState({ticker,data,loading:false,error:false});
      } catch {
        if (!disposed && !controller.signal.aborted) setState({ticker,data:null,loading:false,error:true});
      }
    };
    void refresh();
    const visibleRefresh = () => { if (document.visibilityState === "visible") void refresh(); };
    const timer = window.setInterval(visibleRefresh,60000);
    document.addEventListener("visibilitychange",visibleRefresh);
    window.addEventListener("focus",visibleRefresh);
    return () => { disposed = true; current?.abort(); window.clearInterval(timer); document.removeEventListener("visibilitychange",visibleRefresh); window.removeEventListener("focus",visibleRefresh); };
  },[ticker,attempt]);
  const visible = state.ticker === ticker ? state : {data:null,loading:true,error:false};
  return <TechnicalInsightsView ticker={ticker} {...visible} retry={() => setAttempt(n => n+1)}/>;
}
