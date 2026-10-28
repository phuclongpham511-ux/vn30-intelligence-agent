import type { Metadata } from "next";
import AppShell from "./components/app-shell/AppShell";
import "./globals.css";
export const metadata: Metadata = {
  title: "Woofi",
  description: "Vietnamese equity data, fundamentals and evidence in one focused workspace.",
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" suppressHydrationWarning><body>
    {process.env.WOOFI_DEVELOPMENT === '1' && <aside style={{padding:'8px 16px',background:'#fef3c7',color:'#422006',fontSize:13}}>
      <strong>DEVELOPMENT · DỮ LIỆU DEMO / SYNTHETIC DATA</strong> · {process.env.WOOFI_DEV_LABEL} · <a href="/__woofi_dev__/identity" style={{textDecoration:'underline'}}>Runtime identity</a>
    </aside>}
    <AppShell>{children}</AppShell></body></html>;
}
