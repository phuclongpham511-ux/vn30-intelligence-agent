"use client";
import {useLocale} from "@/lib/i18n";
import Link from "next/link";
import { Button } from "./components/ui/button";
export default function NotFound() {
  const {t}=useLocale();
  return <div className="panel mx-auto my-16 max-w-lg p-10 text-center"><p className="eyebrow">{t("404 · Not found")}</p><h1 className="my-4 text-2xl">{t("This page is not available")}</h1><p className="mb-6 text-sm text-muted-foreground">{t("Search for a ticker or return to your workspace.")}</p><Button asChild><Link href="/">{t("Back to Explore")}</Link></Button></div>;
}
