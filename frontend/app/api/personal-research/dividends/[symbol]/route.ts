import {personalBackend,personalRuntimeEnabled} from '@/lib/personal-financial-server';
export const dynamic='force-dynamic';
export async function GET(_request:Request,context:{params:Promise<{symbol:string}>}){
 if(!personalRuntimeEnabled())return new Response(null,{status:404});
 const {symbol}=await context.params;
 if(!/^[A-Z0-9]{1,20}$/.test(symbol))return new Response(null,{status:404});
 try{
  const response=await fetch(`${personalBackend()}/personal-research/dividends/${symbol}`,{cache:'no-store',signal:AbortSignal.timeout(15000)});
  return new Response(await response.text(),{status:response.status,headers:{'Content-Type':'application/json','Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'}});
 }catch{return Response.json({detail:'Saved dividend evidence unavailable'},{status:503});}
}
