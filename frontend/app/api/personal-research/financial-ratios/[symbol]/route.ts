import {canonicalFinancialEnabled,readCanonicalFinancialRatios} from '@/lib/canonical-financial-snapshots.mjs';
import {NextRequest} from 'next/server';
import {personalRuntimeEnabled} from '@/lib/personal-financial-server';

export const dynamic='force-dynamic';

export async function GET(request:NextRequest,context:{params:Promise<{symbol:string}>}){
 if(!personalRuntimeEnabled()||!canonicalFinancialEnabled())return new Response(null,{status:404});
 const {symbol}=await context.params;
 if(!/^[A-Z0-9]{1,20}$/.test(symbol))return new Response(null,{status:404});
 const frequency=request.nextUrl.searchParams.get('frequency')||'annual';
 if(!['annual','quarterly'].includes(frequency))return new Response(null,{status:400});
 try{
  const body=readCanonicalFinancialRatios(symbol,frequency);
  return new Response(body,{status:body?200:404,headers:{'Content-Type':'application/json','Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'}});
 }catch{return Response.json({detail:'Personal financial ratios unavailable'},{status:503,headers:{'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'}});}
}
