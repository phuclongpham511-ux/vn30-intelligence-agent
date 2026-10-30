import {NextRequest} from 'next/server';
import {privateFinancialRequest,attachFinancialUpdates} from '@/lib/watchlist-financial-server';

export async function POST(request:NextRequest) {
  const base=process.env.BACKEND_URL||'http://127.0.0.1:8000';
  try {
    const body=await request.text();
    if(body.length>8000)return Response.json({detail:'Watchlist request too large'},{status:413});
    const response=await fetch(`${base}/watchlists/intelligence`,{method:'POST',
      headers:{'Content-Type':'application/json'},body,cache:'no-store',
      signal:AbortSignal.any([request.signal,AbortSignal.timeout(15000)])});
    if(response.ok&&privateFinancialRequest(request)&&JSON.parse(body).community_groups!==true){
      const core=await response.json();
      const data=await attachFinancialUpdates(core,core.stocks.map((row:{symbol:string})=>row.symbol),request.signal);
      return Response.json(data,{headers:{'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'}});
    }
    return new Response(await response.text(),{status:response.status,
      headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
  } catch {
    return Response.json({detail:'Watchlist updates are temporarily unavailable. Please retry.'},{status:502});
  }
}
