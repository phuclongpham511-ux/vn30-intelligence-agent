import test from 'node:test';
import assert from 'node:assert/strict';
import {resolvePriceState,priceStateClass} from '../lib/priceState.ts';
const now=new Date('2026-10-16T07:00:00Z');
const row=(patch={})=>({ticker:'DEMO01',last_price:10700,reference_price:10000,change:700,change_percent:7,price_unit:'VND',trading_date:'2026-10-16',updated_at:now.toISOString(),session:'active',source:'DEMO',
  price_limits:{symbol:'DEMO01',trading_date:'2026-10-16',observed_at:null,effectiveness:'trading_day',reference_price:10000,source:'DEMO limits',unit:'VND',qualification:'qualified',ceiling:10700,floor:9300,ceiling_field:'ceiling',floor_field:'floor'},...patch});
const resolve=(r=row(),status='fresh',failed=false)=>resolvePriceState('DEMO01',r,status,now,failed);

test('all nine price states have deterministic meanings and financial tokens',()=>{
  const cases=[['CEILING',row()],['ADVANCING',row({price_limits:undefined})],['REFERENCE',row({last_price:10000,change:0,change_percent:0})],
    ['DECLINING',row({last_price:9800,change:-200,change_percent:-2})],['FLOOR',row({last_price:9300,change:-700,change_percent:-7})],
    ['STALE',row(),'stale'],['UNAVAILABLE',null],['UNKNOWN',row({change:null})],['ERROR',row(),'fresh',true]];
  for(const [state,r,status='fresh',failed=false] of cases){assert.equal(resolve(r,status,failed),state);assert.match(priceStateClass(state),new RegExp('price-'+state.toLowerCase()));}
});
test('missing or mismatched limits preserve qualified direction but cannot establish a limit event',()=>{
  for(const patch of [{symbol:'OTHER'},{trading_date:'2026-10-15'},{unit:'thousand VND'},{qualification:'unverified_units'},
    {source:''},{ceiling_field:''},{reference_price:9900},{floor:11000},{ceiling:10000},{ceiling:10700.01},{ceiling:NaN}]) {
    const r=row();Object.assign(r.price_limits,patch);assert.equal(resolve(r),'ADVANCING');
  }
  assert.equal(resolve(row({price_unit:undefined})),'ADVANCING','limits require explicit compatible quote unit');
  assert.equal(resolve(row({price_unit:'thousand VND'})),'UNKNOWN');
});
test('observation limits need a valid identical source time; daily metadata never borrows tick time',()=>{
  const r=row();delete r.price_limits.effectiveness;r.price_limits.observed_at=now.toISOString();
  assert.equal(resolve(r),'CEILING');
  for(const time of [null,'broken','2026-10-16T06:59:59Z']){r.price_limits.observed_at=time;assert.equal(resolve(r),'ADVANCING');}
  r.price_limits.effectiveness='trading_day';r.price_limits.observed_at=null;assert.equal(resolve(r),'CEILING');
  assert.equal(r.price_limits.observed_at,null);
});
test('same-instrument, day, finite values and consistent reference/changes fail safely',()=>{
  for(const patch of [{ticker:'OTHER'},{last_price:0},{last_price:NaN}])assert.equal(resolve(row(patch)),'UNAVAILABLE');
  for(const patch of [{reference_price:9999},{reference_price:NaN},{change:NaN},{change_percent:-7}])assert.equal(resolve(row(patch)),'UNKNOWN');
  for(const patch of [{trading_date:'2026-10-15'},{updated_at:'2026-10-16T07:01:00Z'},
    {updated_at:'2026-10-15T07:00:00Z',session:'closed'}])assert.equal(resolve(row(patch)),'STALE');
  assert.equal(resolve(row(),'unknown'),'UNKNOWN');assert.equal(resolve(null,'fresh',true),'ERROR');
});
test('resolver never changes original evidence or invents ceiling/floor from a percentage',()=>{
  const r=row({price_limits:undefined});const before=JSON.stringify(r);
  assert.equal(resolve(r),'ADVANCING');assert.equal(JSON.stringify(r),before);
  assert.equal(resolve(row({last_price:10000,change:0,change_percent:0,reference_price:null})),'UNKNOWN');
});
