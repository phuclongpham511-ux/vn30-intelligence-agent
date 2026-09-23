import { notFound } from "next/navigation";

export default async function StockPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const normalized = symbol.trim().toUpperCase();
  if (!/^[A-Z0-9]{1,20}$/.test(normalized)) notFound();
  return <><p className="eyebrow">Stock explore · Placeholder</p><h1>{normalized}</h1>
    <p>This route accepts dynamic symbols. This symbol has not been validated against a data provider.</p>
    <section><h2>Market context is coming</h2><p>Price history, fundamentals and news are planned for later development days.</p></section>
  </>;
}
