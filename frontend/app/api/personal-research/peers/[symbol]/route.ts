import {personalBackend,personalRuntimeEnabled} from '@/lib/personal-financial-server';
export const dynamic='force-dynamic';
export async function GET(request:Request,context:{params:Promise<{symbol:string}>}){
 if(!personalRuntimeEnabled())return new Response(null,{status:404});
 const {symbol}=await context.params;const query=new URL(request.url).searchParams;
 const frequency=query.get('frequency')||'annual',period=query.get('period')||'';
 if(!/^[A-Z0-9]{1,20}$/.test(symbol)||!['annual','quarterly','ttm'].includes(frequency)||!(frequency==='annual'?/^\d{4}$/:/^\d{4}-Q[1-4]$/).test(period))return new Response(null,{status:400});
 try{
  const response=await fetch(`${personalBackend()}/personal-research/peers/${symbol}?${new URLSearchParams({period,frequency})}`,{cache:'no-store',signal:AbortSignal.timeout(15000)});
  return new Response(await response.text(),{status:response.status,headers:{'Content-Type':'application/json','Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'}});
 }catch{return Response.json({detail:'Saved peer evidence unavailable'},{status:503});}
}
