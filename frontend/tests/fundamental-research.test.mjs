import test from 'node:test';
import assert from 'node:assert/strict';
import {financialResearchData,financialChartRows} from '../lib/fundamental-research.ts';
const row=year=>({ticker:'ABC',period:year,currency:'VND',source:'test',revenue:0,net_profit:null,gross_margin:null,net_margin:null,roe:null,revenue_growth_yoy:null,net_profit_growth_yoy:null});
const data={ticker:'ABC',currency:'VND',source:'test',period_type:'annual',financial_identity_guard:false,rows:[row('2023'),row('2025')],changes:[]};
test('financial research ownership and period validation fail closed',()=>{
  assert.equal(financialResearchData(data,'ABC').rows[0].revenue,0);
  for(const mutation of [{ticker:'OTHER'},{currency:'USD'},{rows:[row('2023'),row('2023')]},{rows:[{...row('2025'),source:'other'}]},{rows:[row('2025-Q1')]},{rows:[{...row('2025'),net_profit:Infinity}]}])assert.throws(()=>financialResearchData({...data,...mutation},'ABC'));
});
test('financial issuer protection rejects generic revenue and preserves PAT-only data',()=>{
  assert.throws(()=>financialResearchData({...data,financial_identity_guard:true},'ABC'));
  assert.doesNotThrow(()=>financialResearchData({...data,financial_identity_guard:true,rows:[{...row('2025'),revenue:null,net_profit:10}]},'ABC'));
});
test('chart placeholders break missing-year lines without inventing observations',()=>{
  const rows=financialChartRows(data.rows);
  assert.deepEqual(rows.map(r=>r.period),['2023','2024','2025']);
  assert.equal(rows[1].revenue,null);assert.equal(data.rows.length,2);assert.equal(rows[0].revenue,0);
});
test('comparison output must belong to the displayed metric and exact prior year',()=>{
  const change={metric:'revenue',current_period:'2025',prior_period:'2024',current:0,previous:null,absolute_change:null,growth_yoy:null};
  assert.doesNotThrow(()=>financialResearchData({...data,changes:[change]},'ABC'));
  assert.throws(()=>financialResearchData({...data,changes:[{...change,prior_period:'2023'}]},'ABC'));
  assert.throws(()=>financialResearchData({...data,changes:[{...change,current:10}]},'ABC'));
  assert.throws(()=>financialResearchData({...data,changes:[change,change]},'ABC'));
  assert.throws(()=>financialResearchData({...data,changes:[{...change,current_period:'2023',prior_period:'2022'}]},'ABC'));
  assert.throws(()=>financialResearchData({...data,rows:[row('2024'),row('2025')],changes:[{...change,previous:10}]},'ABC'));
});
