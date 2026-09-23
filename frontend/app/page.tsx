import Link from "next/link";

export default function Home() {
  return <>
    <p className="eyebrow">Personalized equity intelligence</p>
    <h1>Know what deserves your attention.</h1>
    <p>Explore Vietnamese equities and, in future releases, follow the changes that matter to you.</p>
    <section><h2>Day 0 foundation</h2>
    <p>Development seeds: TCB, FPT and HPG. Stock data and validation will be connected in Day 1.</p>
    <Link href="/watchlist">View watchlist scaffold →</Link></section>
  </>;
}
