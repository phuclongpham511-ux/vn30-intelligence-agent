// Local development only. The stable Supervisor, releases and databases are not inputs.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import http from 'node:http';
import {spawn, execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';

export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const frontendPort = 3102;
export const backendPort = 8102;
export function cleanEnvironment(input) {
  const keep = new Set(['path','systemroot','windir','comspec','pathext','temp','tmp','appdata','localappdata','userprofile','home','lang']);
  return Object.fromEntries(Object.entries(input).filter(([key]) => keep.has(key.toLowerCase())));
}
export function localRequest(peer, headers, port) {
  return peer === '127.0.0.1' && headers.host === `127.0.0.1:${port}` &&
    (!headers.origin || headers.origin === `http://127.0.0.1:${port}`) &&
    (!headers['sec-fetch-site'] || ['same-origin','none'].includes(headers['sec-fetch-site']));
}
export async function assertFree(port) {
  const probe = net.createServer();
  await new Promise((resolve, reject) => {
    probe.once('error', reject);
    probe.listen(port, '127.0.0.1', () => probe.close(resolve));
  });
}
export function prepareFrontend(runtime, source = root) {
  const dir = path.join(runtime, 'frontend');
  fs.mkdirSync(dir);
  const frontend = path.join(source, 'frontend');
  fs.symlinkSync(path.join(frontend,'node_modules'),path.join(dir,'node_modules'),'junction');
  for (const name of ['package.json','tsconfig.json','postcss.config.mjs']) {
    fs.copyFileSync(path.join(frontend, name), path.join(dir, name));
  }
  return dir;
}

export function mirrorSource(source, destination) {
  // Next's route watcher does not discover junction-linked app directories on
  // Windows. Mirror only frontend source; Next writes generated files here, never
  // into the worktree. No manual snapshots or rebuilds are needed after edits.
  const previous = new Map();
  function sync() {
    const seen = new Set();
    function walk(relative) {
      const input = path.join(source,relative);
      if(!fs.existsSync(input))return;
      for(const entry of fs.readdirSync(input,{withFileTypes:true})) {
        if(entry.isSymbolicLink() || entry.name==='.local' || entry.name.startsWith('.env') || /\.(sqlite.*|db|pdf)$/i.test(entry.name))continue;
        const name=path.join(relative,entry.name);
        if(entry.isDirectory()){walk(name);continue;}
        if(!entry.isFile())continue;
        const file=path.join(source,name),target=path.join(destination,name),stat=fs.statSync(file);
        const stamp=`${stat.mtimeMs}:${stat.size}`;
        seen.add(name);
        if(previous.get(name)!==stamp){fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(file,target);previous.set(name,stamp);}
      }
    }
    for(const folder of ['app','lib','public','tests'])walk(folder);
    // Remove only files this mirror created after their source was deleted.
    for(const name of previous.keys())if(!seen.has(name)){fs.unlinkSync(path.join(destination,name));previous.delete(name);}
  }
  sync();
  return sync;
}

export async function run() {
  if (process.argv.length > 2) throw Error('Usage: node scripts/dev.mjs (fixed isolated ports 3102/8102)');
  await assertFree(frontendPort);
  await assertFree(backendPort);
  const venvPython = path.join(root,'.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
  const python = process.env.WOOFI_DEV_PYTHON || (fs.existsSync(venvPython)?venvPython:'python');
  const environment = cleanEnvironment(process.env);
  const runtimeBase = path.join(environment.LOCALAPPDATA || environment.LocalAppData || os.tmpdir(), 'Woofi', 'Development');
  fs.mkdirSync(runtimeBase, {recursive:true});
  const runtime = fs.mkdtempSync(path.join(runtimeBase, 'run-'));
  const manifest = {contract:'woofi-development-v1', run_id:randomUUID(),
    source:fs.realpathSync(root), source_sha:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),
    branch:execFileSync('git',['branch','--show-current'],{cwd:root,encoding:'utf8'}).trim(),
    source_mode:'live worktree (including uncommitted edits)',
    source_dirty:Boolean(execFileSync('git',['status','--porcelain'],{cwd:root,encoding:'utf8'}).trim()),
    data:'SYNTHETIC DEMO ONLY', backend:`http://127.0.0.1:${backendPort}`,
    frontend:`http://127.0.0.1:${frontendPort}`, database:path.join(runtime,'development.sqlite'),
    started_at:new Date().toISOString(), frontend_hot_reload:true, backend_reload:'restart this command'};
  fs.writeFileSync(path.join(runtime,'identity.json'),JSON.stringify(manifest,null,2));
  const dir = prepareFrontend(runtime);
  const sync = mirrorSource(path.join(root,'frontend'),dir);
  for (const key of Object.keys(process.env)) delete process.env[key];
  Object.assign(process.env, environment, {NODE_ENV:'development', NEXT_TELEMETRY_DISABLED:'1',
    BACKEND_URL:manifest.backend, WOOFI_DEVELOPMENT:'1', WOOFI_DEV_LABEL:`${manifest.branch} · ${manifest.source_sha.slice(0,7)}${manifest.source_dirty?' + WIP':''}`});
  const require = createRequire(path.join(root,'frontend','package.json'));
  const next = require('next');
  const app = next({dev:true, webpack:true, dir, hostname:'127.0.0.1', port:frontendPort,
    conf:{experimental:{externalDir:true}}});
  let stopping = false;
  let backend;
  let mirrorTimer;
  const server = http.createServer(async (req,res) => {
    if (!localRequest(req.socket.remoteAddress, req.headers, frontendPort)) {
      res.writeHead(403); res.end('Local development only'); return;
    }
    res.setHeader('X-Woofi-Development-Run',manifest.run_id);
    res.setHeader('Cache-Control','no-store');
    if(req.url === '/__woofi_dev__/identity') {
      res.setHeader('Content-Type','application/json');res.end(JSON.stringify(manifest));return;
    }
    await app.getRequestHandler()(req,res);
  });
  server.on('upgrade',(req,socket,head)=>{
    if(!localRequest(req.socket.remoteAddress,req.headers,frontendPort)){socket.destroy();return;}
    app.getUpgradeHandler()(req,socket,head);
  });
  async function stop(code=0) {
    if(stopping)return; stopping=true;
    clearInterval(mirrorTimer);
    console.log('Stopping this development pair only…');
    // EOF is the child-owned graceful shutdown command; never target a remembered PID.
    backend?.stdin.end();
    server.close(); server.closeAllConnections();
    await app.close();
    if(backend?.pid && backend.exitCode===null) await new Promise(resolve=>backend.once('exit',resolve));
    process.exit(code);
  }
  process.on('SIGINT',()=>void stop()); process.on('SIGTERM',()=>void stop());
  process.stdin.setEncoding('utf8');
  process.stdin.on('data',text=>{if(text.trim()==='stop')void stop();});
  try {
    backend=spawn(python,['-m','scripts.dev_backend',runtime],{cwd:root,
      env:{...environment,PYTHONUNBUFFERED:'1',PYTHONDONTWRITEBYTECODE:'1'},stdio:['pipe','inherit','inherit'],windowsHide:true});
    backend.stdin.on('error',error=>{if(!stopping){console.error(error.message);void stop(1);}});
    backend.on('error',error=>{console.error(error.message);void stop(1);});
    backend.on('exit',code=>{if(!stopping){console.error(`Development backend exited (${code})`);void stop(1);}});
    let identity;
    for(let attempt=0;attempt<60&&!stopping;attempt++) {
      try { const response=await fetch(`${manifest.backend}/__woofi_dev__/identity`,{signal:AbortSignal.timeout(1000)});
        if(response.ok){identity=await response.json();break;}
      } catch {}
      await new Promise(resolve=>setTimeout(resolve,500));
    }
    if(stopping)return;
    if(identity?.run_id!==manifest.run_id || identity.source!==manifest.source || identity.source_sha!==manifest.source_sha)
      throw Error('Matching development backend identity not verified');
    await app.prepare();
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(frontendPort,'127.0.0.1',resolve);});
    mirrorTimer=setInterval(()=>{try{sync();}catch(error){console.error('Source mirror failed:',error.message);void stop(1);}},500);
    console.log(`Woofi DEVELOPMENT · DEMO DATA\n${manifest.frontend}/news\n${manifest.source}\n${manifest.branch} @ ${manifest.source_sha}\nRuntime: ${runtime}\nCtrl+C stops this pair. Backend changes: restart this command.`);
  } catch(error) {console.error(error);await stop(1);}
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  run().catch(error=>{console.error(error.message);process.exitCode=1;});
}
