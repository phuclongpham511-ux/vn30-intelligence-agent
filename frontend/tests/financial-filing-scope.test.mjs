// Synthetic scope contracts only; real issuer filing evidence is tested separately.
import test from 'node:test';
import assert from 'node:assert/strict';
import {financialEngineData} from '../lib/financial-engine-data.ts';
import {fixture} from './fixtures/fundamental-summary.mjs';

test('public financial consumers reject internal filing data without an explicit offline opt-in',()=>{
 const data=fixture();Object.assign(data,{display_scope:'internal_research',read_kind:'saved_filing_review',internal_authorization_reference:'synthetic-only://review'});
 assert.throws(()=>financialEngineData(data,'ABC','annual',true),/not public data/);
 assert.equal(financialEngineData(data,'ABC','annual',true,true),data);
 for(const change of [d=>d.internal_authorization_reference='',d=>d.is_fixture=true,d=>d.read_kind='provider_or_process_cache',d=>d.display_scope='unsupported']){
  const invalid=structuredClone(data);change(invalid);
  assert.throws(()=>financialEngineData(invalid,'ABC','annual',true,true));
 }
 delete data.display_scope;
 assert.throws(()=>financialEngineData(data,'ABC','annual',true,true),/Missing internal/);
});

test('legacy public payloads and default public rendering retain their existing gates',()=>{
 const data=fixture();assert.equal(financialEngineData(data,'ABC','annual',true),data);
 data.display_scope='public';assert.equal(financialEngineData(data,'ABC','annual',true),data);
 data.fundamental_summary.metrics[0].status='UNQUALIFIED';
 assert.throws(()=>financialEngineData(data,'ABC','annual',true),/Unsafe financial qualification/);
});
