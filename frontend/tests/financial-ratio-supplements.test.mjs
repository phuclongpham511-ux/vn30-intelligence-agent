import {test} from 'node:test';
import assert from 'node:assert/strict';
import {financialRatioSupplements} from '../lib/financial-ratio-supplements.mjs';
const evidence={formula:'Python calculation',reason:null,inputs:[{source:'saved',value:0}]};
const engine={ticker:'ABC',period_type:'annual',is_fixture:false,display_scope:'personal_research',rows:[{period:'2025',free_cash_flow:0,cash_conversion:2,calculations:{free_cash_flow:evidence,cash_conversion:evidence}},{period:'2024',free_cash_flow:null,cash_conversion:99,calculations:{cash_conversion:{...evidence,reason:'missing_input'}}}]};
test('preserves Python values, zero, evidence and missing periods without recomputing',()=>{
 const rows=financialRatioSupplements(engine,'ABC','annual');
 assert.equal(rows.length,2);assert.equal(rows[0].values['2025'],0);assert.equal(rows[0].unit,'VND');
 assert.equal(rows[1].values['2024'],null);assert.equal(rows[1].values['2025'],2);
 assert.equal(rows[0].evidence['2025'],evidence);assert.equal(rows[0].metric_id,'woofi_free_cash_flow');
});
test('rejects wrong ticker/frequency, fixtures and public scope',()=>{
 assert.deepEqual(financialRatioSupplements(engine,'XYZ','annual'),[]);
 assert.deepEqual(financialRatioSupplements(engine,'ABC','quarterly'),[]);
 for(const override of [{is_fixture:true},{display_scope:'public'}])assert.deepEqual(financialRatioSupplements({...engine,...override},'ABC','annual'),[]);
});
test('unproven calculations and all-missing series stay absent',()=>{
 assert.deepEqual(financialRatioSupplements({...engine,rows:[{period:'2025',free_cash_flow:12,calculations:{}}]},'ABC','annual'),[]);
});
