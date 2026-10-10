"use client";
import {useRouter} from 'next/navigation';
import StockSearch from './StockSearch';
export default function TickerSearch(){const router=useRouter();return <div className="max-w-lg"><StockSearch label="Search ticker" onSelect={symbol=>router.push('/stocks/'+encodeURIComponent(symbol))}/></div>;}
