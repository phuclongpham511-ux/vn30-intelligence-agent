import test from 'node:test';
import assert from 'node:assert/strict';
import {industryData} from '../lib/industry-financials.ts';
const fixture=()=>({contract:'industry-financials-v1',industry:{id:'sample',model:'non_financial',name_en:'Sample',name_vi:'Mẫu'},taxonomy:{name:'Test',version:'1',source_reference:'synthetic://test'},period:'2025',frequency:'annual',membership_on:'2025-12-31',report_scope:'consolidated',expected_companies:2,represented_companies:1,missing_tickers:['DEF'],point_in_time_qualified:false,limitations:[],metrics:{revenue:{value:100,unit:'VND',status:'PARTIAL',included_companies:1,expected_companies:2,coverage:.5,method:'Observed sum',excluded:{DEF:'missing_observation'},peers:[{ticker:'ABC',value:100,rank:1,percentile:.5,contribution:1,sources:['test'],revisions:['a'.repeat(64)]}]}}});
test('industry contract retains coverage and never promotes a demonstration to public evidence',()=>{
 assert.equal(industryData(fixture(),'sample','2025').metrics.revenue.coverage,.5);
 const data=fixture();data.is_fixture=true;
 assert.throws(()=>industryData(data,'sample','2025'),/Demo/);
 assert.doesNotThrow(()=>industryData(data,'sample','2025',true));
});
test('industry parser rejects malformed coverage, nonfinite values, duplicate peers and wrong ownership',()=>{
 for(const mutate of [d=>d.industry.id='wrong',d=>d.period='2024',d=>d.metrics.revenue.value=Infinity,d=>d.metrics.revenue.coverage=1,d=>d.metrics.revenue.status='COMPLETE',d=>d.metrics.revenue.peers.push(d.metrics.revenue.peers[0]),d=>d.metrics.revenue.peers[0].rank=0,d=>d.metrics.revenue.status='UNAVAILABLE']){
  const data=fixture();mutate(data);assert.throws(()=>industryData(data,'sample','2025'));
 }
});
