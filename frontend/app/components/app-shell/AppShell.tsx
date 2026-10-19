"use client";
import {useEffect,useState} from 'react';
import {ThemeProvider,useTheme} from 'next-themes';
import {usePathname} from 'next/navigation';
import Link from 'next/link';
import {Moon,Sun,Info,X} from 'lucide-react';
import {Dialog} from 'radix-ui';
import {LanguageProvider,useLocale} from '@/lib/i18n';
import TickerSearch from '../stock/TickerSearch';
import {MarketSearchProvider,useMarketSearch} from '../market/MarketSearch';
import {StockUniverse} from '../stock/StockUniverse';
import {Button} from '../ui/button';

export function BrandLogo({compact=false}: {compact?:boolean}) {
  const {t}=useLocale();
  return <Link href="/" aria-label={t('Woofi home')} className={compact?'relative block h-8 w-20 shrink-0 overflow-hidden':'relative block h-16 w-40 overflow-hidden'}>
    {/* The original asset is untouched; only surrounding canvas padding is outside the frame. */}
    <img src="/assets/woofi-logo.png" alt="Woofi" width={1448} height={1086} className="absolute left-0 top-1/2 h-auto w-full -translate-y-1/2 object-contain"/>
  </Link>;
}
export function AboutWoofi({compact=false}: {compact?:boolean}) {
  const {t}=useLocale();
  return <Dialog.Root><Dialog.Trigger asChild><button type="button" aria-label={t('About Woofi')} className={compact?'flex size-9 shrink-0 items-center justify-center rounded hover:bg-muted':'flex items-center gap-2 rounded px-3 py-2 text-xs text-muted-foreground hover:bg-muted'}><Info size={16}/>{!compact&&t('About Woofi')}</button></Dialog.Trigger>
    <Dialog.Portal><Dialog.Overlay className="fixed inset-0 z-50 bg-black/50"/><Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-[calc(100%_-_2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border bg-card p-6 shadow-lg">
      <Dialog.Title className="pr-8 text-lg font-semibold">{t('About Woofi')}</Dialog.Title><Dialog.Description className="mt-3 text-sm leading-6 text-muted-foreground">{t('Woofi brings together Vietnam market data, company information, publisher news and public investor discussions, with source evidence you can inspect.')}</Dialog.Description>
      <Dialog.Close aria-label={t('Close')} className="absolute right-4 top-4 rounded p-1 hover:bg-muted"><X size={17}/></Dialog.Close>
    </Dialog.Content></Dialog.Portal>
  </Dialog.Root>;
}
export function PrimaryNavigation({path}:{path:string}) {
  const {t,language}=useLocale();
  return <nav aria-label={t('Main navigation')} className="woofi-primary-nav">
    {([{href:'/',label:'Market'},{href:'/news',label:'News'},{href:'/watchlist',label:language==='vi'?'Follow':'Watchlist'}] as const).map(({href,label})=>{
      const active=href==='/'?path==='/'||path.startsWith('/stocks/')||path.startsWith('/indices/'):path===href||path.startsWith(href+'/');
      return <Link key={href} href={href} aria-current={active?'page':undefined}>{t(label)}</Link>;
    })}
  </nav>;
}
function ThemeToggle() {
  const {resolvedTheme,setTheme}=useTheme();const {t}=useLocale();const [mounted,setMounted]=useState(false);useEffect(()=>setMounted(true),[]);const dark=!mounted||resolvedTheme==='dark';
  return <Button variant="ghost" size="icon" aria-label={t(dark?'Switch to light mode':'Switch to dark mode')} onClick={()=>setTheme(dark?'light':'dark')}>{dark?<Sun size={17}/>:<Moon size={17}/>}</Button>;
}
function Shell({children}: {children:React.ReactNode}) {
  const {t,language,setLanguage}=useLocale();
  const path=usePathname(),market=path==='/'||path.startsWith('/stocks/')||(process.env.NEXT_PUBLIC_WOOFI_VALIDATION==='replay'&&path==='/demo/market');
  const {setQuery}=useMarketSearch();
  useEffect(()=>{
    const controller=new AbortController();
    let busy=false;
    const refresh=async()=>{if(busy)return;busy=true;try{await fetch('/api/ingestion/refresh',{method:'POST',cache:'no-store',signal:controller.signal});}catch{}finally{busy=false;}};
    void refresh();
    const timer=setInterval(()=>{void refresh();},5*60*1000);
    return ()=>{controller.abort();clearInterval(timer);};
  },[]);
  return <div className={market?'market-shell min-h-screen':'min-h-screen'}><a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-card focus:p-3">{t('Skip to content')}</a>
    <div className="min-w-0">
    {process.env.NEXT_PUBLIC_WOOFI_VALIDATION==='replay'&&<div className="market-validation">SIMULATED UI VALIDATION — NOT LIVE SSI</div>}
    <header className="market-app-header woofi-app-header">
      <div className="market-brand"><BrandLogo compact/></div><PrimaryNavigation path={path}/><div className="market-global-search"><TickerSearch onQueryChange={path==='/'?setQuery:undefined}/></div>
      <select aria-label={t('Language')} value={language} onChange={e=>setLanguage(e.target.value as 'en'|'vi')} className="h-9 w-14 shrink-0 rounded border bg-background px-1 text-xs"><option value="vi">VI</option><option value="en">EN</option></select>
      <ThemeToggle/>
    </header><main id="main-content" className={market?'market-canvas':'mx-auto max-w-[1600px] p-4 md:p-8'}>{children}</main><footer className="mx-4 flex flex-wrap items-center justify-between gap-2 border-t py-5 text-[11px] text-muted-foreground md:mx-8"><span>{t('Woofi · Vietnamese equities')}</span><span>{t('Daily market data · Publisher news')}</span><AboutWoofi/></footer>
    </div></div>;
}
function InternalShell({children}: {children:React.ReactNode}) {
  const {t,language,setLanguage}=useLocale();
  return <div className="market-shell min-h-screen"><header className="flex flex-wrap items-center justify-between gap-2 border-b p-3"><strong>{t('Internal provisional SSI data')}</strong><div className="flex items-center gap-2"><select aria-label={t('Language')} value={language} onChange={e=>setLanguage(e.target.value as 'en'|'vi')}><option value="vi">VI</option><option value="en">EN</option></select><ThemeToggle/></div></header><main id="main-content" className="market-canvas">{children}</main></div>;
}
export default function AppShell({children}: {children:React.ReactNode}) {
  const path=usePathname();
  // The internal saved-evidence route must not mount Shell's ingestion refresh,
  // global ticker search, universe or market acquisition consumers, even on 404.
  if(path==='/internal/ssi-market')return <ThemeProvider storageKey="woofi.ssi-provisional.theme.v1" attribute="class" defaultTheme="dark" enableSystem={false}><LanguageProvider><InternalShell>{children}</InternalShell></LanguageProvider></ThemeProvider>;
  return <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange><LanguageProvider><MarketSearchProvider><StockUniverse enabled={false}><Shell>{children}</Shell></StockUniverse></MarketSearchProvider></LanguageProvider></ThemeProvider>;
}
