import test from 'node:test';
import assert from 'node:assert/strict';
import {validateFinancialVerification} from '../lib/financial-verification.ts';
import {formatFinancialAmount} from '../lib/financial-format.ts';

function example(){
 return {ticker:'ABC',period_type:'annual',display_scope:'personal_research',is_fixture:false,
  rows:[{period:'2025',revenue:100,roe:null}],
  verification:{contract:'financial-verification-v1',ticker:'ABC',frequency:'annual',audience:'personal_research',point_in_time_qualified:false,
   statuses:{VERIFIED:0,PARTIALLY_VERIFIED:1,UNAVAILABLE:1},displayed_metric_ids:['revenue'],
   periods:[{period:'2025',metrics:{
    revenue:{status:'PARTIALLY_VERIFIED',display_eligible:true,public_display_eligible:false,missing_evidence:['reporting_scope','public_display_permission']},
    roe:{status:'UNAVAILABLE',display_eligible:false,public_display_eligible:false,missing_evidence:['required_source_fields']}}}]}};
}

test('evidence grades retain separate partial and unavailable states without public promotion',()=>{
 assert.doesNotThrow(()=>validateFinancialVerification(example()));
 for(const mutate of [
  d=>d.verification.audience='public',d=>d.verification.ticker='OTHER',
  d=>d.verification.periods[0].metrics.revenue.status='VERIFIED',
  d=>d.verification.periods[0].metrics.revenue.public_display_eligible=true,
  d=>d.verification.periods[0].metrics.roe.display_eligible=true,
  d=>d.verification.statuses.PARTIALLY_VERIFIED=2,
  d=>d.verification.displayed_metric_ids=[]]){
  const d=example();mutate(d);assert.throws(()=>validateFinancialVerification(d));
 }
});

test('small positive and negative source amounts stay distinct from actual zero in both unit scales',()=>{
 const number=(n,d=2)=>new Intl.NumberFormat('en',{maximumFractionDigits:d}).format(n);
 assert.equal(formatFinancialAmount(1000,1e9,2,number),'<0.01');
 assert.equal(formatFinancialAmount(-1000,1e9,2,number),'>−0.01');
 assert.equal(formatFinancialAmount(0,1e9,2,number),'0');
 assert.equal(formatFinancialAmount(1e9,1e9,2,number),'1');
 assert.equal(formatFinancialAmount(.4,1,0,number),'<1');
});
