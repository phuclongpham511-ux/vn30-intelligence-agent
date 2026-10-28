import {NextRequest} from 'next/server';

export async function POST(request:NextRequest) {
  const base=process.env.BACKEND_URL||'http://127.0.0.1:8000';
  try {
    const body=await request.text();
    if(body.length>8000)return Response.json({detail:'Watchlist request too large'},{status:413});
    const response=await fetch(`${base}/watchlists/intelligence`,{method:'POST',
      headers:{'Content-Type':'application/json'},body,cache:'no-store',
      signal:AbortSignal.any([request.signal,AbortSignal.timeout(15000)])});
    return new Response(await response.text(),{status:response.status,
      headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
  } catch {
    return Response.json({detail:'Watchlist updates are temporarily unavailable. Please retry.'},{status:502});
  }
}
