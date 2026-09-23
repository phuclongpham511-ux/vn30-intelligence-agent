import { ChartNoAxesCombined, Landmark, Newspaper, ArrowUpRight, ScanLine } from "lucide-react";
import TickerPicker from "./components/TickerPicker";
export default function Home() {
  return <div className="page-stack">
    <div className="flex flex-wrap items-center justify-between gap-3"><span className="eyebrow">Workspace / Explore</span><span className="rounded-full border px-3 py-1 text-[10px] tracking-wide text-muted-foreground">VIETNAM EQUITIES</span></div>
    <section className="relative overflow-hidden rounded-2xl border bg-card p-6 md:p-8">
      <div aria-hidden="true" className="pointer-events-none absolute -right-10 -top-16 hidden h-72 w-72 items-center justify-center rounded-full border border-primary/10 bg-primary/5 md:flex"><div className="flex size-44 items-center justify-center rounded-full border border-primary/15"><ChartNoAxesCombined size={70} strokeWidth={1} className="text-primary/50"/></div></div>
      <div className="relative max-w-2xl"><div className="mb-4 flex items-center gap-2 text-xs text-primary"><ScanLine size={15}/>A clearer view of the market</div>
        <h1 className="max-w-lg text-3xl leading-tight tracking-tight md:text-[36px]">Vietnam Equity<br className="hidden sm:block"/> Intelligence</h1>
        <p className="mt-4 max-w-lg text-sm leading-6 text-muted-foreground">Explore market data, fundamentals and news.<br/>One focused workspace. Evidence behind every number.</p>
        <div className="mt-6 flex flex-wrap gap-2">{[{icon:ChartNoAxesCombined,text:"MARKET DATA"},{icon:Landmark,text:"FUNDAMENTALS"},{icon:Newspaper,text:"SAMPLE NEWS"}].map(({icon:Icon,text}) => <span key={text} className="flex items-center gap-2 rounded-md border bg-background/50 px-2.5 py-1.5 text-[9px] font-medium tracking-wider text-muted-foreground"><Icon size={12}/>{text}</span>)}</div>
      </div>
    </section>
    <TickerPicker/>
    <section className="flex items-start gap-4 rounded-xl border border-dashed p-5"><span className="rounded-lg bg-muted p-2 text-muted-foreground"><ScanLine size={18}/></span><div className="flex-1"><h2 className="text-sm">Less noise. More perspective.</h2><p className="mt-1 text-xs leading-5 text-muted-foreground">Personalized materiality intelligence will be added in the next section.</p></div><span className="flex shrink-0 items-center gap-1 text-[10px] text-muted-foreground">COMING NEXT <ArrowUpRight size={12}/></span></section>
  </div>;
}
