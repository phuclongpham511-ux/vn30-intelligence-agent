import Link from "next/link";
import { CircleAlert, RefreshCw, ArrowLeft } from "lucide-react";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";
export function StockLoading({ ticker }: { ticker: string }) {
  return <div className="page-stack" aria-busy="true" aria-label={`Loading ${ticker} overview`}>
    <span role="status" className="sr-only">Loading {ticker} market data, fundamentals and news.</span>
    <Skeleton className="h-4 w-28"/><div className="flex justify-between gap-4"><div className="flex gap-4"><Skeleton className="size-14 rounded-xl"/><div className="space-y-3"><Skeleton className="h-7 w-28"/><Skeleton className="h-4 w-40"/></div></div><Skeleton className="hidden h-16 w-40 sm:block"/></div>
    <Skeleton className="h-3 w-60"/><Skeleton className="h-[70px] w-full rounded-xl"/>
    <div className="grid gap-4 xl:grid-cols-12"><Skeleton className="h-[426px] rounded-xl xl:col-span-8"/><Skeleton className="h-[426px] rounded-xl xl:col-span-4"/></div>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[0,1,2,3].map(i => <Skeleton key={i} className="h-36 rounded-xl"/>)}</div>
    <div className="grid gap-4 xl:grid-cols-3">{[0,1,2].map(i => <Skeleton key={i} className="h-56 rounded-xl"/>)}</div><Skeleton className="h-44 rounded-xl"/>
  </div>;
}
export function StockError({ ticker, message, retry }: { ticker: string; message: string; retry: () => void }) {
  return <div className="flex min-h-[65vh] items-center justify-center"><div role="alert" className="panel w-full max-w-lg p-8 text-center sm:p-12">
    <span className="mx-auto mb-6 flex size-12 items-center justify-center rounded-xl border bg-muted"><CircleAlert size={22} className="text-muted-foreground"/></span>
    <div className="eyebrow mb-3">Data unavailable</div><h1 className="text-2xl">Could not load {ticker}</h1><p className="mt-3 text-sm leading-6 text-muted-foreground">{message}</p>
    <div className="mt-7 flex flex-wrap justify-center gap-3"><Button onClick={retry}><RefreshCw size={15}/>Retry</Button><Button variant="outline" asChild><Link href="/"><ArrowLeft size={15}/>Back to Explore</Link></Button></div>
    <p className="mt-6 text-[11px] text-muted-foreground">No estimated or fallback numbers are shown.</p>
  </div></div>;
}
