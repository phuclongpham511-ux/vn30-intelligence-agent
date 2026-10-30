// Supported Next custom server: bind before serving any private values.
// No desktop browser, provider access, worker or production process handling.
import {createServer} from 'node:http';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import next from 'next';
import {localResearchRequest} from '../lib/personal-boundary.mjs';
if(process.env.WOOFI_PERSONAL_RESEARCH!=='1')throw Error('Explicit WOOFI_PERSONAL_RESEARCH=1 required');
if(process.env.APP_ENV&&process.env.APP_ENV!=='development')throw Error('Not a development configuration');
if(process.env.BACKEND_URL!=='http://127.0.0.1:8431')throw Error('Existing development backend 8431 required');
if(process.env.WOOFI_PERSONAL_BACKEND!=='http://127.0.0.1:8432')throw Error('Only the isolated saved-evidence backend is permitted');
const dir=resolve(fileURLToPath(new URL('..',import.meta.url)));
process.env.WOOFI_DEPLOYMENT_KIND='personal-development';
process.env.WOOFI_PERSONAL_BOUNDARY='loopback-custom-server-v1';
const app=next({dev:false,dir,hostname:'127.0.0.1',port:3431});
await app.prepare();
const handle=app.getRequestHandler();
const server=createServer((request,response)=>{
 if(!localResearchRequest(request.socket.remoteAddress,request.headers)){
  response.writeHead(403,{'Cache-Control':'no-store'});response.end('Local research only');return;
 }
 response.setHeader('Cache-Control','private, no-store');
 response.setHeader('X-Robots-Tag','noindex, nofollow');
 handle(request,response);
});
server.on('error',error=>{console.error(error);process.exitCode=1;app.close();});
server.listen(3431,'127.0.0.1',()=>console.log('Personal Research: http://127.0.0.1:3431/ · core backend 8431 unchanged · private financial backend 8432'));
let stopping=false;
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{if(stopping)return;stopping=true;server.close(async()=>{await app.close();process.exit(0);});});
