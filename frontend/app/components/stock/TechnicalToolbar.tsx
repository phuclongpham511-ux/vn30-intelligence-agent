import { RANGES, type Range } from "@/lib/chart-data";
import { Button } from "../ui/button";

export type Indicators = { MA20: boolean; MA50: boolean; Volume: boolean; RSI: boolean };
export default function TechnicalToolbar({ range, onRange, reset, indicators, onIndicators }: {
  range: Range; onRange: (range: Range) => void; reset: () => void;
  indicators: Indicators; onIndicators: (indicators: Indicators) => void;
}) {
  return <div className="flex flex-wrap items-center justify-between gap-3">
    <div className="flex flex-wrap gap-1" role="group" aria-label="Price history range">
      {(Object.keys(RANGES) as Range[]).map(value => <Button key={value} size="sm" variant={range === value ? "secondary" : "ghost"} aria-pressed={range === value} onClick={() => onRange(value)}>{value}</Button>)}
    </div>
    <fieldset className="flex flex-wrap items-center gap-3 text-xs"><legend className="sr-only">Indicators</legend>
      {(Object.keys(indicators) as (keyof Indicators)[]).map(key => <label key={key} className="flex cursor-pointer items-center gap-1.5"><input className="accent-primary" type="checkbox" checked={indicators[key]} onChange={event => onIndicators({...indicators, [key]:event.target.checked})}/>{key}</label>)}
    </fieldset>
    <Button size="sm" variant="ghost" onClick={reset}>Reset view</Button>
  </div>;
}
