import {NextRequest} from 'next/server';
export async function GET(request:NextRequest,context:{params:Promise<{path?:string[]}>}){
 const {path=[]}=await context.params;
 if(path.length<1||path.length>2||path[0]!=='industries')return new Response(null,{status:404});
 try{
  const response=await fetch(`${process.env.BACKEND_URL||'http://127.0.0.1:8000'}/financial-intelligence/${path.map(encodeURIComponent).join('/')}${request.nextUrl.search}`,{cache:'no-store',signal:AbortSignal.timeout(15000)});
  return new Response(await response.text(),{status:response.status,headers:{'Content-Type':'application/json','Cache-Control':'private, no-store'}});
 }catch{return Response.json({detail:'Industry data unavailable'},{status:502});}
}
