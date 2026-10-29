import {canonicalFinancialEnabled} from '@/lib/canonical-financial-snapshots.mjs';
import { notFound } from "next/navigation";
import Explore from "../../components/Explore";
import {personalRuntimeEnabled} from '@/lib/personal-financial-server';
export const dynamic='force-dynamic';
export default async function StockPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const ticker = symbol.trim().toUpperCase();
  if (!/^[A-Z0-9]{1,20}$/.test(ticker)) notFound();
  return <Explore key={ticker} ticker={ticker} personalResearch={personalRuntimeEnabled()&&!canonicalFinancialEnabled()} personalFinancials={personalRuntimeEnabled()}/>;
}
