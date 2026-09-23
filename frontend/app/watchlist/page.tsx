import Link from "next/link";
import { Bookmark, ArrowRight, ScanLine } from "lucide-react";
import { Button } from "../components/ui/button";
export default function WatchlistPage() {
  return <div className="page-stack"><div className="eyebrow">Workspace / Watchlist</div><div><h1>Watchlist</h1><p className="mt-2 text-sm text-muted-foreground">Your attention workspace</p></div>
    <section className="panel flex min-h-[360px] flex-col items-center justify-center p-8 text-center"><span className="mb-5 rounded-xl border bg-muted p-4"><Bookmark size={26} className="text-muted-foreground"/></span><h2 className="text-xl">Nothing here yet.</h2>
      <p className="mt-3 max-w-sm text-sm leading-6 text-muted-foreground">Monitoring intelligence will be added in the next section. Watchlist management is not available yet.</p>
      <Button variant="outline" asChild className="mt-6"><Link href="/">Explore available stocks<ArrowRight size={15}/></Link></Button>
    </section>
    <div className="flex items-start gap-3 rounded-xl border border-dashed p-5"><ScanLine size={19} className="shrink-0 text-muted-foreground"/><div><h2 className="text-sm">Built for your attention</h2><p className="mt-1 text-xs leading-5 text-muted-foreground">A future home for the changes that matter across the stocks you follow.</p></div></div>
  </div>;
}
