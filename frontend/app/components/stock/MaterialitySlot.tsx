import { ScanLine } from "lucide-react";
export default function MaterialitySlot() {
  return <section data-slot="materiality" aria-labelledby="materiality-title" className="flex flex-wrap items-center gap-3 rounded-xl border border-dashed px-5 py-4">
    <ScanLine size={19} className="shrink-0 text-muted-foreground"/><div className="min-w-0 flex-1"><h2 id="materiality-title" className="text-xs">Your attention, focused.</h2><p className="mt-0.5 text-[11px] text-muted-foreground">Materiality intelligence will appear here in Section 2.</p></div><span className="rounded border px-2 py-1 text-[9px] tracking-wider text-muted-foreground">COMING NEXT</span>
  </section>;
}
