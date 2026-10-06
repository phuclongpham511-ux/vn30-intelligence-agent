import TickerPicker from './components/TickerPicker';
import ExploreMarket from './components/ExploreMarket';
export default function Home(){return <div className="page-stack"><div><div className="eyebrow mb-3">Workspace / Explore</div><h1>Vietnam equities</h1></div><ExploreMarket/><div id="explore-stocks" className="scroll-mt-24"><TickerPicker/></div></div>;}
