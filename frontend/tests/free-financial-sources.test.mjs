import test from 'node:test';
import assert from 'node:assert/strict';
import {validateFinancialVerification,verificationDimensions} from '../lib/financial-verification.ts';
import {observedIndustryData,industryData} from '../lib/industry-financials.ts';

const dimensions=()=>({SOURCE_VERIFIED:true,ACCOUNTING_VERIFIED:true,POINT_IN_TIME_VERIFIED:false,PUBLICATION_RIGHTS_APPROVED:false,FULLY_VERIFIED:false});
test('reviewed source and accounting verification do not imply point-in-time or publication permission',()=>{
 const d={ticker:'ABC',period_type:'annual',display_scope:'internal_research',is_fixture:false,rows:[{period:'2025',net_profit:100}],verification:{contract:'financial-verification-v1',ticker:'ABC',frequency:'annual',audience:'internal_research',point_in_time_qualified:false,statuses:{VERIFIED:0,PARTIALLY_VERIFIED:1,UNAVAILABLE:0},displayed_metric_ids:['net_profit'],dimension_counts:Object.fromEntries(verificationDimensions.map(k=>[k,Number(dimensions()[k])])),periods:[{period:'2025',metrics:{net_profit:{status:'PARTIALLY_VERIFIED',display_eligible:true,public_display_eligible:false,missing_evidence:['qualified_publication_timestamp','public_display_permission'],dimensions:dimensions()}}}]}};
 assert.doesNotThrow(()=>validateFinancialVerification(d));
 for(const change of [v=>v.periods[0].metrics.net_profit.dimensions.FULLY_VERIFIED=true,v=>v.dimension_counts.SOURCE_VERIFIED=2,v=>v.periods[0].metrics.net_profit.dimensions.SOURCE_VERIFIED=false,v=>v.periods[0].metrics.net_profit.public_display_eligible=true]){
  const bad=structuredClone(d);change(bad.verification);assert.throws(()=>validateFinancialVerification(bad));
 }
});

function observed(){return {contract:'observed-industry-peers-v1',display_scope:'personal_research',industry:{id:'1234',label:'Synthetic category'},period:'2025',frequency:'annual',members:['ABC','DEF'],observed_at:'2026-10-17T00:00:00Z',classification_source:'synthetic://test',taxonomy_version:null,taxonomy_level:null,classification_effective_at:null,historical_aggregation_enabled:false,sector_totals:null,public_display_eligible:false,metrics:{net_profit:{unit:'VND',covered_companies:1,expected_companies:2,comparable_companies:0,missing:{DEF:'no_saved_financial_evidence'},observations:[{ticker:'ABC',value:100,source:'synthetic://test',scope:'consolidated',verification:dimensions(),rank:null,percentile:null,record_hashes:['a'.repeat(64)]}]}}};}
test('private industry observations retain missing coverage and cannot become public or historical totals',()=>{
 const d=observed();assert.throws(()=>observedIndustryData(d,'1234','2025'));
 assert.doesNotThrow(()=>observedIndustryData(d,'1234','2025',true));
 assert.throws(()=>industryData(d,'1234','2025'));
 for(const change of [v=>v.sector_totals=100,v=>v.historical_aggregation_enabled=true,v=>v.classification_effective_at='2026-10-17',v=>v.metrics.net_profit.covered_companies=2,v=>v.metrics.net_profit.comparable_companies=1,v=>v.metrics.net_profit.observations[0].value=Infinity,v=>v.metrics.net_profit.observations[0].rank=1]){
  const bad=observed();change(bad);assert.throws(()=>observedIndustryData(bad,'1234','2025',true));
 }
});
