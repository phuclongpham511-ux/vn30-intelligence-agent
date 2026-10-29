// The canonical Supervisor still owns this frontend role and its lifecycle.
import {createServer} from 'node:http';
import {spawn} from 'node:child_process';
import {resolve} from 'node:path';
import next from 'next';
import {readSnapshotConfiguration} from '../lib/canonical-financial-snapshots.mjs';
import {localResearchRequest} from '../lib/personal-boundary.mjs';

const financial=readSnapshotConfiguration();
if(!financial){
 const child=spawn(process.execPath,[resolve('node_modules/next/dist/bin/next'),'start','--hostname','127.0.0.1',...process.argv.slice(2)],{stdio:'inherit'});
 child.on('exit',code=>process.exit(code??1));
}else{
 if(process.env.APP_ENV!=='production'||process.env.BACKEND_URL!=='http://127.0.0.1:8000'||process.argv.slice(2).join(' ')!=='--port 3000')throw Error('Canonical loopback configuration required');
 process.env.WOOFI_PERSONAL_BOUNDARY='canonical-loopback-custom-server-v1';
 process.env.WOOFI_DEPLOYMENT_KIND='canonical-personal';
 const app=next({dev:false,dir:process.cwd(),hostname:'127.0.0.1',port:3000});
 await app.prepare();
 const handle=app.getRequestHandler();
 const server=createServer((request,response)=>{
  if(!localResearchRequest(request.socket.remoteAddress,request.headers,3000)){
   response.writeHead(403,{'Cache-Control':'no-store'});response.end('Local workspace only');return;
  }
  response.setHeader('Cache-Control','private, no-store');
  response.setHeader('X-Robots-Tag','noindex, nofollow');
  handle(request,response);
 });
 server.on('error',error=>{console.error(error);process.exitCode=1;app.close();});
 server.listen(3000,'127.0.0.1',()=>console.log('Woofi local financial scope: '+financial.config.scope));
 let stopping=false;
 for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{if(stopping)return;stopping=true;server.close(async()=>{await app.close();process.exit(0);});});
}
