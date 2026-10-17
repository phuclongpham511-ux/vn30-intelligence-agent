import test from 'node:test';
import assert from 'node:assert/strict';
import {boardRows,movementGroups,heatmapBin,sampleObservations} from '../lib/quoteMap.ts';
const now=new Date('2026-10-16T09:00:00Z');
const item=(ticker,value,status='fresh')=>({status,snapshot:{ticker,last_price:10000,reference_price:10000,change:value===null?null:value*100,change_percent:value,source:'SIMULATED TEST — NOT SSI',trading_date:'2026-10-16',updated_at:'2026-10-16T07:45:00Z',session:'closed'}});
const items={UP:item('UP',2),DOWN:item('DOWN',-1),ZERO:item('ZERO',0),OLD:item('OLD',9,'stale'),NOREF:item('NOREF',null)};
const batch={items,session:'closed',as_of:now.toISOString()};
const stocks=Object.keys(items).concat('MISSING').map(symbol=>({symbol}));
test('overview compares one qualified date/session cohort and orders largest declines first',()=>{
  const source={...batch,items:{...items,LOW:item('LOW',-4)}};
  const summary=sampleObservations([...stocks,{symbol:'LOW'}],source,false,now);
  assert.equal(summary.comparable,true);
  assert.deepEqual(summary.decliners.map(r=>r.stock.symbol),['LOW','DOWN']);
  assert.equal(summary.compared,4);assert.equal(summary.available,6);
  assert.equal(summary.stale,1);assert.equal(summary.missing,1);
  assert.equal(sampleObservations(stocks,source,true,now).available,null);
  assert.equal(sampleObservations(stocks,source,true,now).comparable,false);
  assert.equal(sampleObservations([{symbol:'UP'}],source,false,now).comparable,false);
  assert.equal(sampleObservations(stocks,{...source,session:'unknown'},false,now).comparable,false);
  const mixed=structuredClone(source);mixed.items.DOWN.snapshot.session='active';
  assert.equal(sampleObservations(stocks,mixed,false,now).groups.declining.length,0);
  assert.equal(sampleObservations(stocks,mixed,false,now).compared,2);
});
test('movement groups partition the loaded filtered sample and exclude stale/missing movements',()=>{
  const rows=boardRows(stocks,batch,false,now),groups=movementGroups(rows);
  assert.deepEqual(Object.fromEntries(Object.entries(groups).map(([k,v])=>[k,v.map(r=>r.stock.symbol)])),{advancing:['UP'],declining:['DOWN'],unchanged:['ZERO'],unqualified:['OLD','NOREF','MISSING']});
  const filtered=movementGroups(boardRows(stocks.filter(s=>['DOWN','OLD'].includes(s.symbol)),batch,false,now));
  assert.deepEqual(Object.values(filtered).map(r=>r.length),[0,1,0,1]);
  assert.equal(new Set(Object.values(groups).flat()).size,rows.length);
  assert.deepEqual(Object.values(movementGroups(boardRows(stocks,batch,true,now))).map(r=>r.length),[0,0,0,6]);
});
test('five-bin source percentage boundaries stay exact; stale/missing are neutral',()=>{
  for(const [value,expected] of [[-5,'negative-strong'],[-1,'negative-strong'],[-.999,'negative'],[-.01,'negative'],[0,'zero'],[.01,'positive'],[.999,'positive'],[1,'positive-strong'],[5,'positive-strong'],[null,'neutral'],[NaN,'neutral']]){
    const row=boardRows([{symbol:'X'}],{...batch,items:{X:item('X',value)}},false,now)[0];
    assert.equal(heatmapBin(row),expected,String(value));
  }
  for(const row of boardRows(stocks,batch,false,now).filter(r=>r.status!=='fresh'))assert.equal(heatmapBin(row),'neutral');
});
test('organization preserves numeric source values, and sorting compares numbers rather than formatted strings',()=>{
  const source={...batch,items:{A:item('A',2),B:item('B',10),C:item('C',-.5)}};
  source.items.A.snapshot.last_price=9000;source.items.B.snapshot.last_price=100000;
  const identities=['A','B','C'].map(symbol=>({symbol})),before=JSON.stringify(source);
  assert.deepEqual(boardRows(identities,source,false,now).map(r=>r.stock.symbol),['B','A','C']);
  assert.equal(boardRows(identities,source,false,now,'price')[0].stock.symbol,'B');
  movementGroups(boardRows(identities,source,false,now));assert.equal(JSON.stringify(source),before);
});
