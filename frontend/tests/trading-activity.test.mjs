import test from 'node:test';
import assert from 'node:assert/strict';
import {activityValue,activityNumber,priceLimitTone} from '../lib/tradingActivity.ts';
import {boardRows} from '../lib/quoteMap.ts';
const now=new Date('2026-10-16T09:00:00Z');
const row=(symbol='ABC',volume=1200000,value=84000000000)=>({ticker:symbol,price_unit:'VND',last_price:70000,reference_price:69000,change:1000,change_percent:1.45,source:'SIMULATED acceptance only',session:'closed',trading_date:'2026-10-16',updated_at:'2026-10-16T07:45:00Z',total_volume:999999,total_value:999999,
  trading_activity:{symbol,trading_date:'2026-10-16',observed_at:'2026-10-16T07:45:00Z',session:'trading_day',source:'SIMULATED qualified-contract test, NOT SSI',scope:'regular_matched',cumulative:true,includes_negotiated_trades:false,
    volume:{value:volume,raw_value:String(volume),field:'fixture_matched_shares',unit:'shares',qualification:'qualified'},value:{value,raw_value:String(value),field:'fixture_matched_vnd',unit:'VND',qualification:'qualified'}}});
test('only qualified same-observation/date matched cumulative activity is presentable, preserving genuine zero',()=>{
  assert.equal(activityValue(row(),'volume','fresh',now),1200000);
  assert.equal(activityValue(row('ABC',0,0),'value','fresh',now),0);
  assert.equal(activityValue({...row(),trading_activity:undefined},'volume','fresh',now),null);
  for(const mutate of [r=>r.trading_activity.volume.unit=null,r=>r.trading_activity.cumulative=false,r=>r.trading_activity.includes_negotiated_trades=true,r=>r.trading_activity.symbol='OTHER',r=>r.trading_activity.trading_date='2026-10-15',r=>r.trading_activity.observed_at='2026-10-16T07:46:00Z',r=>r.trading_activity.volume.qualification='unverified_units',r=>r.trading_activity.volume.raw_value=true,r=>r.trading_activity.volume.value=NaN,r=>r.trading_activity.volume.value=-1,r=>r.trading_activity.volume.value=1.5]){
    const copy=row();mutate(copy);assert.equal(activityValue(copy,'volume','fresh',now),null);
  }
  assert.equal(activityValue(row(),'volume','stale',now),null);
  assert.equal(activityValue(row(),'volume','fresh',new Date('2026-10-17T09:00:00Z')),null,'weekend carryover is not today');
});
test('raw numeric sorting handles volume/value independently, nulls last, no formatted-string order or estimated GT',()=>{
  const a=row('A',900,10e9),b=row('B',1000000,2e9),c=row('C');c.trading_activity.value.qualification='unavailable';c.trading_activity.volume.unit=null;
  const data={items:{A:{status:'fresh',snapshot:a},B:{status:'fresh',snapshot:b},C:{status:'fresh',snapshot:c}},session:'closed',as_of:now.toISOString()},stocks=['A','B','C'].map(symbol=>({symbol}));
  assert.deepEqual(boardRows(stocks,data,false,now,'volume').map(r=>r.stock.symbol),['B','A','C']);
  assert.deepEqual(boardRows(stocks,data,false,now,'value').map(r=>r.stock.symbol),['A','B','C']);
  assert.equal(activityValue(c,'value','fresh',now),null,'never substitute latest price times volume');
});
test('formatting large financial values leaves originals untouched and provides VI-friendly units',()=>{
  assert.equal(activityNumber(1250000,'volume','en'),'1.25 M');assert.equal(activityNumber(1250000,'volume','vi'),'1,25 triệu');
  assert.equal(activityNumber(1234567890,'value','vi'),'1,23 tỷ');assert.equal(activityNumber(null,'value','en'),'—');assert.equal(activityNumber(0,'volume','vi'),'0');
});
test('ceiling/floor require exact source-qualified same-date VND limits; stale and percentage assumptions never qualify',()=>{
  const r=row();r.price_limits={symbol:'ABC',trading_date:r.trading_date,observed_at:r.updated_at,source:'SIMULATED limit fixture',unit:'VND',qualification:'qualified',ceiling:70000,floor:60000,ceiling_field:'fixture_ceiling',floor_field:'fixture_floor'};
  assert.equal(priceLimitTone(r,'fresh',now),'ceiling');r.last_price=60000;r.change=-9000;r.change_percent=-9000/69000*100;assert.equal(priceLimitTone(r,'fresh',now),'floor');assert.equal(priceLimitTone(r,'stale',now),null);
  r.price_limits.trading_date='2026-10-15';assert.equal(priceLimitTone(r,'fresh',now),null);delete r.price_limits;assert.equal(priceLimitTone(r,'fresh',now),null);
});
