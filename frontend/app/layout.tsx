import type { Metadata } from "next";
import AppShell from "./components/app-shell/AppShell";
import "./globals.css";
export const metadata: Metadata = {
  title: "Woofi",
  description: "Vietnamese equity data, fundamentals and evidence in one focused workspace.",
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" suppressHydrationWarning><body><AppShell>{children}</AppShell></body></html>;
}
