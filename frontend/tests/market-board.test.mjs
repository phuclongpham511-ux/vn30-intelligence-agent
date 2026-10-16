import test from 'node:test';
import assert from 'node:assert/strict';
import {boardRows,boardColumns,boardPageSize,boardDefaultGroup} from '../lib/quoteMap.ts';

const now=new Date('2026-10-16T09:00:00Z');
const item=(symbol,change=1,status='fresh')=>({status,snapshot:{ticker:symbol,last_price:20000,
  reference_price:19900,change:100,change_percent:change,total_volume:null,source:'SSI:FastConnect:ohlc:1m',
  trading_date:'2026-10-16',updated_at:'2026-10-16T07:45:00Z',session:'closed'}});
const stocks=['OLD','ZERO','UP','DOWN','MISS','NOREF'].map(symbol=>({symbol}));
const data={items:{OLD:item('OLD',9,'stale'),ZERO:item('ZERO',0),UP:item('UP',3),DOWN:item('DOWN',-2),NOREF:item('NOREF',null)},session:'closed',as_of:now.toISOString()};

test('default uses a qualified index and a single supported bounded page, not alphabetical universe page one',()=>{
  assert.equal(boardDefaultGroup,'VN30');assert.equal(boardPageSize,30);assert.ok(boardPageSize<=50);
});
test('board orders observed percentages and keeps stale/missing/unreferenced rows separate',()=>{
  const original=JSON.stringify(data),rows=boardRows(stocks,data,false,now,'change');
  assert.deepEqual(rows.map(r=>r.stock.symbol),['UP','ZERO','DOWN','OLD','NOREF','MISS']);
  assert.equal(rows.find(r=>r.stock.symbol==='MISS').row,null);
  assert.equal(rows.find(r=>r.stock.symbol==='NOREF').row.change_percent,null);
  assert.equal(rows.find(r=>r.stock.symbol==='OLD').tone,'neutral');
  assert.equal(JSON.stringify(data),original);
});
test('sort modes never replace values, missing numbers sort last and all identities remain accessible',()=>{
  assert.deepEqual(boardRows(stocks,data,false,now,'ticker').map(r=>r.stock.symbol),['DOWN','MISS','NOREF','OLD','UP','ZERO']);
  assert.deepEqual(boardRows(stocks,data,false,now,'fallers').slice(0,3).map(r=>r.stock.symbol),['DOWN','ZERO','UP']);
  const prices={...data,items:{...data.items,UP:item('UP',3)}};prices.items.UP.snapshot.last_price=1000;
  assert.equal(boardRows(stocks,prices,false,now,'price')[0].stock.symbol,'DOWN');
  assert.equal(boardRows(stocks,data,true,now,'change').filter(r=>r.status==='fresh').length,0);
});
test('dense columns are balanced contiguous slices without duplicating or losing a stock',()=>{
  for(const length of [1,2,3,10,29,30]){
    const rows=Array.from({length},(_,symbol)=>({stock:{symbol:String(symbol)}}));
    const columns=boardColumns(rows);
    assert.deepEqual(columns.flat(),rows);
    assert.ok(Math.max(...columns.map(c=>c.length))-Math.min(...columns.map(c=>c.length))<=1);
    assert.ok(columns.length<=3);
  }
  assert.deepEqual(boardColumns([]),[]);
});
