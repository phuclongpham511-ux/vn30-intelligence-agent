import TickerPicker from './components/TickerPicker';
import ExploreMarket from './components/ExploreMarket';
export default function Home(){return <div className="page-stack"><ExploreMarket/><div id="explore-stocks" className="scroll-mt-32 border-t pt-6"><TickerPicker/></div></div>;}
