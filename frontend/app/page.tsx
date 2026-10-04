import { ChartNoAxesCombined, Landmark, Newspaper, ArrowUpRight, ScanLine } from "lucide-react";
import TickerPicker from "./components/TickerPicker";
import Link from "next/link";
import { MascotIllustration } from "./components/mascot/Mascot";
export default function Home() {
  return <div className="page-stack">
    <div className="flex flex-wrap items-center justify-between gap-3"><span className="eyebrow">Workspace / Explore</span><span className="rounded-full border px-3 py-1 text-[10px] tracking-wide text-muted-foreground">VIETNAM EQUITIES</span></div>
    <section className="panel grid items-center gap-6 p-5 md:p-6 xl:grid-cols-[1fr_1fr]">
      <div><div className="mb-2 flex items-center gap-2 text-xs text-primary"><ScanLine size={15}/>A clearer view of the market</div>
        <div className="flex items-center gap-3"><h1 className="text-2xl leading-tight tracking-tight md:text-3xl">Vietnam Equity Intelligence</h1><MascotIllustration state="discovery"/></div>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">Explore market data, fundamentals and news.<br/>One focused workspace. Evidence behind every number.</p>
      </div>
      <nav aria-label="Research entry points" className="flex flex-wrap gap-2 sm:grid sm:grid-cols-3">
        {[{icon:ChartNoAxesCombined,text:"MARKET DATA",detail:"Prices & technicals",href:"#available-stocks"},{icon:Landmark,text:"FUNDAMENTALS",detail:"Choose a stock to research",href:"#available-stocks"},{icon:Newspaper,text:"PUBLISHER NEWS",detail:"Market briefing",href:"/news"}].map(({icon:Icon,text,detail,href}) => <Link key={text} href={href} className="research-entry"><Icon size={16} className="shrink-0 text-primary"/><span><span className="block text-[10px] font-semibold tracking-wide">{text}</span><span className="mt-1 hidden text-[11px] text-muted-foreground sm:block">{detail}</span></span></Link>)}
      </nav>
    </section>
    <div id="available-stocks" className="scroll-mt-24"><TickerPicker/></div>
    <Link href="/news" className="flex items-start gap-4 rounded-xl border p-5 hover:bg-muted"><span className="rounded-lg bg-muted p-2 text-muted-foreground"><Newspaper size={18}/></span><div className="flex-1"><h2 className="text-sm">What is happening in the market?</h2><p className="mt-1 text-xs leading-5 text-muted-foreground">Open the market briefing, explore financial topics, or read global coverage.</p></div><span className="flex shrink-0 items-center gap-1 text-xs text-primary">Open News <ArrowUpRight size={12}/></span></Link>
  </div>;
}
