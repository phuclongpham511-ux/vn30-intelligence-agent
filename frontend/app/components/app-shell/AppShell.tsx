"use client";
import {useEffect,useState} from 'react';
import {ThemeProvider,useTheme} from 'next-themes';
import {usePathname} from 'next/navigation';
import Link from 'next/link';
import {Newspaper,Compass,Bookmark,PanelLeft,Moon,Sun,Info,X} from 'lucide-react';
import {Dialog} from 'radix-ui';
import {LanguageProvider,useLocale} from '@/lib/i18n';
import TickerSearch from '../stock/TickerSearch';
import {StockUniverse} from '../stock/StockUniverse';
import {Button} from '../ui/button';
import {Sheet,SheetContent,SheetTrigger,SheetTitle,SheetDescription} from '../ui/sheet';

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
function Navigation({close}: {close?:()=>void}) {
  const path=usePathname();const {t}=useLocale();
  return <div className="flex h-full flex-col"><div onClick={close} className="px-6 pb-5 pt-4"><BrandLogo/></div><div className="eyebrow px-6 pb-3">{t('Workspace')}</div>
    <nav aria-label={t('Main navigation')} className="space-y-1 px-3">{[{href:'/',label:'Explore',icon:Compass},{href:'/news',label:'News',icon:Newspaper},{href:'/watchlist',label:'Watchlist',icon:Bookmark}].map(({href,label,icon:Icon})=>{
      const active=href==='/'?path==='/'||path.startsWith('/stocks')||path.startsWith('/indices'):path===href;
      return <Link key={href} onClick={close} href={href} aria-current={active?'page':undefined} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${active?'bg-primary/10 font-medium text-primary':'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><Icon size={17}/>{t(label as 'Explore'|'News'|'Watchlist')}{active&&<span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary"/>}</Link>;
    })}</nav><div className="mt-auto border-t p-3"><AboutWoofi/></div>
  </div>;
}
function ThemeToggle() {
  const {resolvedTheme,setTheme}=useTheme();const {t}=useLocale();const [mounted,setMounted]=useState(false);useEffect(()=>setMounted(true),[]);const dark=!mounted||resolvedTheme==='dark';
  return <Button variant="ghost" size="icon" aria-label={t(dark?'Switch to light mode':'Switch to dark mode')} onClick={()=>setTheme(dark?'light':'dark')}>{dark?<Sun size={17}/>:<Moon size={17}/>}</Button>;
}
function Shell({children}: {children:React.ReactNode}) {
  const [open,setOpen]=useState(false);const {t,language,setLanguage}=useLocale();
  useEffect(()=>{
    const controller=new AbortController();
    let busy=false;
    const refresh=async()=>{if(busy)return;busy=true;try{await fetch('/api/ingestion/refresh',{method:'POST',cache:'no-store',signal:controller.signal});}catch{}finally{busy=false;}};
    void refresh();
    const timer=setInterval(()=>{void refresh();},5*60*1000);
    return ()=>{controller.abort();clearInterval(timer);};
  },[]);
  return <div className="min-h-screen"><a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-card focus:p-3">{t('Skip to content')}</a>
    <aside className="fixed inset-y-0 left-0 hidden w-60 border-r bg-[var(--sidebar)] lg:block"><Navigation/></aside><div className="min-w-0 lg:ml-60">
    <header className="sticky top-0 z-30 flex min-h-[72px] flex-wrap items-center gap-2 border-b bg-background/95 px-3 py-2 backdrop-blur-sm sm:flex-nowrap sm:py-0 md:px-8">
      <Sheet open={open} onOpenChange={setOpen}><SheetTrigger asChild><Button variant="ghost" size="icon" className="lg:hidden" aria-label={t('Open navigation')}><PanelLeft size={19}/></Button></SheetTrigger><SheetContent side="left" className="w-72 gap-0 p-0"><SheetTitle className="sr-only">{t('Navigation')}</SheetTitle><SheetDescription className="sr-only">{t('Explore, news and watchlist workspace')}</SheetDescription><Navigation close={()=>setOpen(false)}/></SheetContent></Sheet>
      <div className="mr-auto sm:mr-0 lg:hidden"><BrandLogo compact/></div><div className="order-last w-full min-w-0 sm:order-none sm:w-auto sm:flex-1"><TickerSearch/></div>
      <select aria-label={t('Language')} value={language} onChange={e=>setLanguage(e.target.value as 'en'|'vi')} className="h-9 w-14 shrink-0 rounded border bg-background px-1 text-xs"><option value="vi">VI</option><option value="en">EN</option></select>
      <ThemeToggle/>
    </header><main id="main-content" className="mx-auto max-w-[1600px] p-4 md:p-8">{children}</main><footer className="mx-4 flex flex-wrap justify-between gap-2 border-t py-5 text-[11px] text-muted-foreground md:mx-8"><span>{t('Woofi · Vietnamese equities')}</span><span>{t('Daily market data · Publisher news')}</span></footer>
    </div></div>;
}
export default function AppShell({children}: {children:React.ReactNode}) {
  return <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange><LanguageProvider><StockUniverse enabled={false}><Shell>{children}</Shell></StockUniverse></LanguageProvider></ThemeProvider>;
}
