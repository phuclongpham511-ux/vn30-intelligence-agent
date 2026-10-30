// Synthetic access contracts. Real financial samples are validated separately.
import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture} from './fixtures/fundamental-summary.mjs';
import {financialEngineData} from '../lib/financial-engine-data.ts';
import {localResearchRequest} from '../lib/personal-boundary.mjs';
import {personalRuntimeEnabled} from '../lib/personal-financial-server.ts';

function personal(){
 const d=fixture();Object.assign(d,{source:'vnstock:VCI',display_scope:'personal_research',access_classification:'PERSONAL_RESEARCH',data_confidence:'SOURCE_REPORTED',read_kind:'saved_personal_research',research_authorization_reference:'synthetic-only://test',consolidation:null});
 for(const row of [...d.rows,...d.chart_rows]){row.source=d.source;row.roe=null;}
 d.fundamental_summary.consolidation=null;
 for(const metric of d.fundamental_summary.metrics){
  if(metric.key==='roe'){Object.assign(metric,{value:null,status:'UNQUALIFIED'});continue;}
  if(metric.value!==null)Object.assign(metric,{status:'SOURCE_REPORTED',data_confidence:'SOURCE_REPORTED',access_classification:'PERSONAL_RESEARCH',consolidation:null});
 }
 return d;
}
test('personal source observations require explicit research consumer; UNKNOWN is retained',()=>{
 const d=personal();assert.throws(()=>financialEngineData(d,'ABC','annual',true),/not public data/);
 assert.equal(financialEngineData(d,'ABC','annual',true,false,true).consolidation,null);
 for(const mutate of [x=>x.is_fixture=true,x=>x.source='other',x=>x.read_kind='provider_or_process_cache',x=>x.access_classification='PUBLIC_DISPLAY_APPROVED',x=>x.research_authorization_reference='',x=>x.data_confidence='OFFICIAL_VERIFIED']){
  const bad=structuredClone(d);mutate(bad);assert.throws(()=>financialEngineData(bad,'ABC','annual',true,false,true));
 }
});
test('34-quarter personal histories pass the existing financial-engine contract',()=>{
 const d=fixture(),periods=Array.from({length:34},(_,i)=>`${2018+Math.floor(i/4)}-Q${i%4+1}`),base=d.rows[0];
 d.period_type='quarterly';d.available_period_types=['quarterly'];d.fundamental_summary.frequency='quarterly';d.fundamental_summary.period=periods.at(-1);
 d.rows=periods.map(period=>({...base,period,frequency:'quarterly'}));d.chart_rows=d.rows.map(row=>({...row}));
 const result=financialEngineData(d,'ABC','quarterly');
 assert.equal(result.rows.length,34);assert.equal(result.rows[0].period,'2018-Q1');assert.equal(result.rows.at(-1).period,'2026-Q2');
});
test('personal observation status cannot enter an ordinary public payload',()=>{
 const d=personal();d.display_scope='public';d.read_kind='provider_or_process_cache';
 assert.throws(()=>financialEngineData(d,'ABC','annual',true));
});
test('socket boundary rejects foreign clients, DNS rebinding, foreign origins and forwarded identity',()=>{
 assert.equal(localResearchRequest('127.0.0.1',{host:'127.0.0.1:3431'}),true);
 assert.equal(localResearchRequest('127.0.0.1',{host:'127.0.0.1:3431',origin:'http://127.0.0.1:3431','sec-fetch-site':'same-origin'}),true);
 for(const [peer,headers] of [
  ['192.0.2.1',{host:'127.0.0.1:3431','x-forwarded-for':'127.0.0.1'}],
  ['127.0.0.1',{host:'evil.example:3431'}],
  ['127.0.0.1',{host:'127.0.0.1:3431',origin:'https://evil.example'}],
  ['127.0.0.1',{host:'127.0.0.1:3431','sec-fetch-site':'cross-site'}],
 ])assert.equal(localResearchRequest(peer,headers),false);
});
test('frontend feature flag alone does not open a public production configuration',()=>{
 const saved={...process.env};
 try{
  process.env.WOOFI_PERSONAL_RESEARCH='1';delete process.env.WOOFI_PERSONAL_BOUNDARY;delete process.env.WOOFI_DEPLOYMENT_KIND;
  assert.equal(personalRuntimeEnabled(),false);
  process.env.WOOFI_PERSONAL_BOUNDARY='loopback-custom-server-v1';process.env.WOOFI_DEPLOYMENT_KIND='production';assert.equal(personalRuntimeEnabled(),false);
 }finally{for(const key of ['WOOFI_PERSONAL_RESEARCH','WOOFI_PERSONAL_BOUNDARY','WOOFI_DEPLOYMENT_KIND']){if(saved[key]===undefined)delete process.env[key];else process.env[key]=saved[key];}}
});
