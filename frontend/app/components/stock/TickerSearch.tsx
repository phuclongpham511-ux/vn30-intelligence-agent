"use client";
import {useRouter} from 'next/navigation';
import {useStocks} from './StockUniverse';
import StockSearch from './StockSearch';
export default function TickerSearch(){const {stocks,loading,error}=useStocks();const router=useRouter();return <div className="max-w-lg"><StockSearch stocks={stocks} label="Search ticker" disabled={loading||!!error} placeholder={loading?"Loading equity metadata…":error?"Equity search unavailable":"Search ticker or company"} onSelect={symbol=>router.push('/stocks/'+symbol)}/></div>;}
