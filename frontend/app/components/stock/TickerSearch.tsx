"use client";
import {useRouter} from 'next/navigation';
import StockSearch from './StockSearch';
export default function TickerSearch({onQueryChange}:{onQueryChange?:(query:string)=>void}){const router=useRouter();return <div data-market-search><StockSearch label="Search ticker" onQueryChange={onQueryChange} onSelect={symbol=>{onQueryChange?.('');router.push('/stocks/'+encodeURIComponent(symbol));}}/></div>;}
