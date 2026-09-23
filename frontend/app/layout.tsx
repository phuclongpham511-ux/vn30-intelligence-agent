import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "VN30 Intelligence Agent",
  description: "Know what deserves your attention.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>
    <header><Link href="/">VN30 Intelligence</Link><nav><Link href="/watchlist">Watchlist</Link></nav></header>
    <main>{children}</main>
    <footer>Day 0 foundation · No live market data yet</footer>
  </body></html>;
}
