import { notFound } from "next/navigation";
import Explore from "../../components/Explore";
export default async function StockPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const ticker = symbol.trim().toUpperCase();
  if (!/^[A-Z0-9]{1,20}$/.test(ticker)) notFound();
  return <Explore ticker={ticker}/>;
}
