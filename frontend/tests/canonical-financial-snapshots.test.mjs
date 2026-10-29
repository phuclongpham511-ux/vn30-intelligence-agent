import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {readSnapshotConfiguration,readCanonicalFinancial,canonicalFinancialEnabled} from '../lib/canonical-financial-snapshots.mjs';
import {localResearchRequest} from '../lib/personal-boundary.mjs';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');

test('canonical financial serving requires local release scope, exact digest and real ticker ownership',()=>{
 const cwd=process.cwd(),env={...process.env},root=mkdtempSync(join(tmpdir(),'woofi-financial-contract-'));
 const frontend=join(root,'frontend');mkdirSync(frontend);mkdirSync(join(root,'data'));
 try{
  process.chdir(frontend);
  assert.equal(readSnapshotConfiguration(),null);assert.equal(canonicalFinancialEnabled(),false);
  assert.throws(()=>readCanonicalFinancial('ABC','annual','preferred'));
  const payload=JSON.stringify({ticker:'ABC',period_type:'annual',is_fixture:false,display_scope:'personal_research',rows:[{period:'2025',revenue:0,roe:null}]});
  const filename=hash(payload)+'.json';writeFileSync(join(root,filename),payload);
  const index={contract:'private-financial-projection-v1',engine_commit:'synthetic-test-only',generated_at:'2026-01-01T00:00:00Z',items:{'ABC:annual:preferred':{file:filename,sha256:hash(payload)}}};
  const indexBytes=JSON.stringify(index);writeFileSync(join(root,'index.json'),indexBytes);
  const config={contract:'canonical-local-financial-v1',scope:'VN30',tickers:['ABC',...Array.from({length:29},(_,i)=>'X'+i)],index:join(root,'index.json'),index_sha256:hash(indexBytes)};
  const publish=()=>writeFileSync(join(root,'data/personal-financial-runtime.json'),JSON.stringify(config));publish();
  Object.assign(process.env,{APP_ENV:'production',WOOFI_PERSONAL_BOUNDARY:'canonical-loopback-custom-server-v1',WOOFI_DEPLOYMENT_KIND:'canonical-personal'});
  assert.equal(JSON.parse(readCanonicalFinancial('ABC','annual','preferred')).rows[0].revenue,0);
  assert.equal(JSON.parse(readCanonicalFinancial('ABC','annual','preferred')).rows[0].roe,null);
  assert.equal(readCanonicalFinancial('OUTSIDE','annual','preferred'),null);
  writeFileSync(join(root,filename),payload+' ');assert.throws(()=>readCanonicalFinancial('ABC','annual','preferred'),/changed/);
  writeFileSync(join(root,filename),payload);config.index_sha256='0'.repeat(64);publish();assert.throws(()=>readSnapshotConfiguration(),/index changed/);
  config.tickers=['ABC'];publish();assert.throws(()=>readSnapshotConfiguration(),/Invalid financial release/);
 }finally{
  process.chdir(cwd);
  for(const key of ['APP_ENV','WOOFI_PERSONAL_BOUNDARY','WOOFI_DEPLOYMENT_KIND']){if(env[key]===undefined)delete process.env[key];else process.env[key]=env[key];}
  rmSync(root,{recursive:true});
 }
});
test('canonical socket boundary rejects public clients, foreign origins and alternate ports',()=>{
 assert.equal(localResearchRequest('127.0.0.1',{host:'127.0.0.1:3000'},3000),true);
 for(const [peer,headers,port] of [['192.0.2.1',{host:'127.0.0.1:3000'},3000],['127.0.0.1',{host:'evil.example:3000'},3000],['127.0.0.1',{host:'127.0.0.1:3000',origin:'https://evil.example'},3000],['127.0.0.1',{host:'127.0.0.1:3000','sec-fetch-site':'cross-site'},3000],['127.0.0.1',{host:'127.0.0.1:9000'},9000]])assert.equal(localResearchRequest(peer,headers,port),false);
});
