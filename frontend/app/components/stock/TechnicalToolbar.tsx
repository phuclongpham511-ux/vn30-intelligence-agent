import { RANGES, type Range } from "@/lib/chart-data";
import { Button } from "../ui/button";

export default function TechnicalToolbar({ range, onRange, reset }: { range: Range; onRange: (range: Range) => void; reset: () => void }) {
  return <div className="flex flex-wrap items-center justify-between gap-3">
    <div className="flex flex-wrap gap-1" role="group" aria-label="Price history range">
      {(Object.keys(RANGES) as Range[]).map(value => <Button key={value} size="sm" variant={range === value ? "secondary" : "ghost"} aria-pressed={range === value} onClick={() => onRange(value)}>{value}</Button>)}
    </div>
    <Button size="sm" variant="ghost" onClick={reset}>Reset view</Button>
  </div>;
}
