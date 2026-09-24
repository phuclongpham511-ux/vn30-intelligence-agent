"use client";
import { useEffect, useState } from "react";
import { ThemeProvider, useTheme } from "next-themes";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChartNoAxesCombined, Compass, Bookmark, Layers, PanelLeft, Moon, Sun, Search, Database, ArrowUpRight } from "lucide-react";
import TickerSearch from "../stock/TickerSearch";
import { StockUniverse } from "../stock/StockUniverse";
import { Button } from "../ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "../ui/sheet";

function Navigation({ close }: { close?: () => void }) {
  const path = usePathname();
  return <div className="flex h-full flex-col">
    <Link href="/" onClick={close} className="flex items-center gap-3 px-5 pb-9 pt-7" aria-label="VN30 Intelligence home">
      <span className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground"><ChartNoAxesCombined size={21}/></span>
      <span className="text-base font-semibold tracking-tight">VN30<span className="ml-1 font-normal text-muted-foreground">Intelligence</span></span>
    </Link>
    <div className="eyebrow px-6 pb-3">Workspace</div>
    <nav aria-label="Main navigation" className="space-y-1 px-3">
      {[{href:"/",label:"Explore",icon:Compass},{href:"/watchlist",label:"Watchlist",icon:Bookmark}].map(({href,label,icon:Icon}) => {
        const active = href === "/" ? path === "/" || path.startsWith("/stocks") : path === href;
        return <Link key={href} onClick={close} href={href} aria-current={active ? "page" : undefined} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${active ? "bg-primary/10 font-medium text-primary" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}><Icon size={17}/>{label}{active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary"/>}</Link>;
      })}
    </nav>
    <div className="mx-6 mt-8 border-t pt-6"><div className="eyebrow mb-4">On the horizon</div>
      <div className="flex items-center gap-3 text-muted-foreground"><Layers size={16}/><span className="text-xs">Materiality intelligence</span></div>
      <p className="mt-2 text-xs leading-relaxed text-muted-foreground">A clearer view of what deserves your attention. Coming in Section 2.</p>
    </div>
    <div className="mt-auto p-5"><div className="rounded-lg border bg-card p-3">
      <div className="flex items-center gap-2 text-xs font-medium"><Database size={14}/> Data foundation</div>
      <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">Daily prices. Reported fundamentals. Inspectable evidence.</p>
    </div><div className="mt-4 flex justify-between text-[10px] text-muted-foreground"><span>VN EQUITIES</span><span>RESEARCH</span></div></div>
  </div>;
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const dark = !mounted || resolvedTheme === "dark";
  return <Button variant="ghost" size="icon" aria-label={dark ? "Switch to light mode" : "Switch to dark mode"} onClick={() => setTheme(dark ? "light" : "dark")}>{dark ? <Sun size={17}/> : <Moon size={17}/>}</Button>;
}

function Shell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return <div className="min-h-screen">
    <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-card focus:p-3">Skip to content</a>
    <aside className="fixed inset-y-0 left-0 hidden w-60 border-r bg-[var(--sidebar)] lg:block"><Navigation/></aside>
    <div className="min-w-0 lg:ml-60">
      <header className="sticky top-0 z-30 flex h-[72px] items-center gap-3 border-b bg-background/95 px-4 backdrop-blur-sm md:px-8">
        <Sheet open={open} onOpenChange={setOpen}><SheetTrigger asChild><Button variant="ghost" size="icon" className="lg:hidden" aria-label="Open navigation"><PanelLeft size={19}/></Button></SheetTrigger>
          <SheetContent side="left" className="w-72 gap-0 p-0"><SheetTitle className="sr-only">Navigation</SheetTitle><SheetDescription className="sr-only">Explore and watchlist workspace</SheetDescription><Navigation close={() => setOpen(false)}/></SheetContent>
        </Sheet>
        <div className="min-w-0 flex-1"><TickerSearch/></div>
        <span className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex"><Database size={14}/> Daily data</span>
        <div className="ml-1 border-l pl-2"><ThemeToggle/></div>
      </header>
      <main id="main-content" className="mx-auto max-w-[1600px] p-4 md:p-8">{children}</main>
      <footer className="mx-4 flex flex-wrap justify-between gap-2 border-t py-5 text-[11px] text-muted-foreground md:mx-8"><span>VN30 Intelligence · Vietnamese equities</span><span>Daily market data · Sample news</span></footer>
    </div>
  </div>;
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  return <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange><StockUniverse><Shell>{children}</Shell></StockUniverse></ThemeProvider>;
}
