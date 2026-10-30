import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import {cleanEnvironment, localRequest, assertFree, mirrorSource} from '../../scripts/dev.mjs';

test('development child environment excludes credentials, provider flags and production data paths',()=>{
  assert.deepEqual(cleanEnvironment({PATH:'tools',SYSTEMROOT:'windows',DATABASE_URL:'private',
    SSI_API_KEY:'secret',OPENAI_API_KEY:'secret',WOOFI_PERSONAL_SQLITE:'private',NODE_OPTIONS:'preload'}),
    {PATH:'tools',SYSTEMROOT:'windows'});
});
test('local development rejects foreign hosts and cross-origin browser access',()=>{
  assert.equal(localRequest('127.0.0.1',{host:'127.0.0.1:3102'},3102),true);
  for(const headers of [{host:'evil.example:3102'},{host:'127.0.0.1:3102',origin:'https://evil.example'},
    {host:'127.0.0.1:3102','sec-fetch-site':'cross-site'}]) assert.equal(localRequest('127.0.0.1',headers,3102),false);
});
test('occupied development port is refused without stopping its existing owner',async()=>{
  const server=net.createServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  try{await assert.rejects(assertFree(server.address().port),{code:'EADDRINUSE'});assert.equal(server.listening,true);}
  finally{await new Promise(resolve=>server.close(resolve));}
});
test('live mirror follows edits and deletions without copying private files or touching generated/WIP source',()=>{
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'woofi-dev-test-'));
  const source=path.join(temp,'source'),target=path.join(temp,'target');
  fs.mkdirSync(path.join(source,'app'),{recursive:true});fs.mkdirSync(target);
  const file=path.join(source,'app','page.tsx');fs.writeFileSync(file,'first');
  fs.writeFileSync(path.join(source,'app','.env.local'),'secret');
  fs.mkdirSync(path.join(source,'app','.local'));
  fs.writeFileSync(path.join(source,'app','.local','private.json'),'private fixture');
  fs.writeFileSync(path.join(source,'next-env.d.ts'),'existing WIP');
  const sync=mirrorSource(source,target);
  assert.equal(fs.readFileSync(path.join(target,'app','page.tsx'),'utf8'),'first');
  assert.equal(fs.existsSync(path.join(target,'app','.env.local')),false);
  assert.equal(fs.existsSync(path.join(target,'app','.local')),false);
  fs.writeFileSync(file,'second revision');sync();
  assert.equal(fs.readFileSync(path.join(target,'app','page.tsx'),'utf8'),'second revision');
  fs.unlinkSync(file);sync();assert.equal(fs.existsSync(path.join(target,'app','page.tsx')),false);
  assert.equal(fs.readFileSync(path.join(source,'next-env.d.ts'),'utf8'),'existing WIP');
});
