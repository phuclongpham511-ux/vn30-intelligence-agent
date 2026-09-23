import TickerPicker from "./components/TickerPicker";
export default function Home() {
  return <><p className="eyebrow">Vietnamese equities · Data foundation</p>
    <h1>Explore the data behind a stock.</h1>
    <p>Daily prices, deterministic market metrics and reported annual fundamentals.</p>
    <TickerPicker />
  </>;
}
