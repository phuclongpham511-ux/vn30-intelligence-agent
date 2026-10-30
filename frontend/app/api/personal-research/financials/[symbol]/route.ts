import {NextRequest} from 'next/server';
import {personalBackend,personalRuntimeEnabled} from '@/lib/personal-financial-server';
export const dynamic='force-dynamic';
export async function GET(request:NextRequest,context:{params:Promise<{symbol:string}>}){
 if(!personalRuntimeEnabled())return new Response(null,{status:404});
 const {symbol}=await context.params;
 if(!/^[A-Z0-9]{1,20}$/.test(symbol))return new Response(null,{status:404});
 const frequency=request.nextUrl.searchParams.get('frequency')||'annual';
 const evidence=request.nextUrl.searchParams.get('evidence')||'preferred';
 if(!['preferred','provider'].includes(evidence))return new Response(null,{status:400});
 if(!['annual','quarterly','ttm'].includes(frequency))return new Response(null,{status:400});
 try{
  const response=await fetch(`${personalBackend()}/personal-research/financials/${symbol}?frequency=${frequency}&evidence=${evidence}&limit=34`,{cache:'no-store',signal:AbortSignal.timeout(15000)});
  return new Response(await response.text(),{status:response.status,headers:{'Content-Type':'application/json','Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'}});
 }catch{return Response.json({detail:'Personal research evidence unavailable'},{status:503});}
}
