import test from 'node:test';
import assert from 'node:assert/strict';
import {validateFinancialVerification,verificationDimensions} from '../lib/financial-verification.ts';
import {observedIndustryData,industryData} from '../lib/industry-financials.ts';

const dimensions=()=>({SOURCE_VERIFIED:true,ACCOUNTING_VERIFIED:true,REPORTING_METADATA_COMPLETE:true,POINT_IN_TIME_VERIFIED:false,PUBLICATION_RIGHTS_APPROVED:false,FULLY_VERIFIED:false});
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


test('navigation keeps usable financial tasks and hides unrelated empty modules',async()=>{
 const {availableFinancialSections}=await import('../lib/fundamental-research.ts');
 const data={profile:'non_financial',rows:[{period:'2025',revenue:100,net_profit:10,total_assets:200,roe:null,cash_operating:null}],fundamental_summary:{metrics:[]}};
 const sections=availableFinancialSections(data,data.rows);
 assert.ok(sections.includes('performance')&&sections.includes('balance'));
 assert.ok(!sections.includes('profitability')&&!sections.includes('cashflow')&&!sections.includes('valuation'));
 data.rows[0].roe=.1;assert.ok(availableFinancialSections(data,data.rows).includes('profitability'));
});

test('peer distributions require an actual qualified comparison cohort',()=>{
 const data=observed();data.metrics.net_profit.distribution={count:1,minimum:100,median:100,maximum:100};
 assert.throws(()=>observedIndustryData(data,'1234','2025',true));
 data.metrics.net_profit.distribution=null;assert.doesNotThrow(()=>observedIndustryData(data,'1234','2025',true));
});

test('optional new note fields do not weaken existing explicit-null chart contracts',async()=>{
 const {fixture}=await import('./fixtures/fundamental-summary.mjs');
 const {financialEngineData}=await import('../lib/financial-engine-data.ts');
 const data=fixture();data.rows[0].gross_margin=null;
 data.chart_rows=data.rows.map(r=>({...r}));
 delete data.chart_rows[0].gross_margin;
 assert.throws(()=>financialEngineData(data,'ABC','annual',true),/Chart does not match/);
});
