import test from 'node:test';
import assert from 'node:assert/strict';
import {quoteMapCell} from '../lib/quoteMap.ts';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';

// Synthetic presentation cases; no provider read or market-wide claims.
const now=new Date('2026-10-16T07:00:00Z');
const quote=(patch={})=>({status:'fresh',snapshot:{ticker:'AAA',last_price:10200,reference_price:10000,
  change:200,change_percent:2,open:null,high:null,low:null,total_volume:123,total_value:null,
  trading_date:'2026-10-16',updated_at:'2026-10-16T06:59:59Z',source:'SSI:fixture',session:'active',...patch}});

test('map retains exact provider observations and never computes a substitute financial value',()=>{
  const item=quote(); const before=JSON.stringify(item); const cell=quoteMapCell('AAA',item,false,now);
  assert.equal(cell.row,item.snapshot); assert.equal(cell.row.change_percent,2);
  assert.equal(cell.tone,'up'); assert.equal(cell.status,'fresh'); assert.equal(JSON.stringify(item),before);
});
test('direction and missing movement are distinct, including an observed zero',()=>{
  assert.equal(quoteMapCell('AAA',quote({change:-50,change_percent:-.5}),false,now).tone,'down');
  assert.equal(quoteMapCell('AAA',quote({change:0,change_percent:0}),false,now).tone,'unchanged');
  assert.equal(quoteMapCell('AAA',quote({change:null,change_percent:null}),false,now).tone,'neutral');
  assert.equal(quoteMapCell('AAA',quote({change:null,change_percent:null}),false,now).row.change_percent,null);
});
test('stale, failed, previous-day and future source timestamps cannot color a current map tile',()=>{
  for(const item of [{...quote(),status:'stale'},quote({updated_at:'2026-10-16T06:55:00Z'}),
    quote({trading_date:'2026-10-15'}),quote({updated_at:'2026-10-16T07:01:00Z'})]) {
    const cell=quoteMapCell('AAA',item,false,now); assert.equal(cell.status,'stale');
    assert.equal(cell.tone,'neutral'); assert.ok(cell.row,'retain source age/value for inspection');
  }
  assert.equal(quoteMapCell('AAA',quote(),true,now).status,'stale');
  assert.equal(quoteMapCell('AAA',quote(),true,now).tone,'neutral');
});
test('same-day closed-session quote remains an honest closed snapshot, not assumed stale by elapsed wall time',()=>{
  const cell=quoteMapCell('AAA',quote({updated_at:'2026-10-16T07:45:00Z',session:'closed'}),false,new Date('2026-10-16T11:00:00Z'));
  assert.equal(cell.status,'fresh');assert.equal(cell.row.session,'closed');
});
test('missing, nonfinite, invalid price and foreign ticker cannot masquerade as a valid tile',()=>{
  for(const item of [undefined,{status:'unavailable',snapshot:null},quote({last_price:NaN}),quote({last_price:0}),quote({ticker:'BBB'})]) {
    const cell=quoteMapCell('AAA',item,false,now);assert.equal(cell.status,'unavailable');
    assert.equal(cell.row,null);assert.equal(cell.tone,'neutral');
  }
});

const require=createRequire(import.meta.url);
const file='../app/components/stock/QuoteMap.tsx';
const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},
  jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
const exports={};
new Function('require','exports',code)(name=>name==='./LivePrice'?{useLivePrices:()=>({data:null,failed:false})}:
  require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
const stocks=['AAA','ZERO','OLD','MISSING'].map(symbol=>({symbol,company_name:'Tên nguồn '+symbol,display_name_en:'Source name '+symbol,exchange:'HOSE'}));
const data={items:{AAA:quote(),ZERO:quote({ticker:'ZERO',change:0,change_percent:0}),
  OLD:{...quote({ticker:'OLD'}),status:'stale'}},session:'active',as_of:now.toISOString()};
const render=(language='en',props={})=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,
  {value:localeTools(language)},React.createElement(exports.QuoteMapView,{stocks,data,scope:'page',now,...props})));

test('rendered map keeps all scoped identities, one research link each, missing distinct from zero and original source evidence',()=>{
  const html=render();
  assert.equal((html.match(/data-quote-tile=/g)||[]).length,4);
  assert.equal((html.match(/href="\/stocks\//g)||[]).length,4);
  assert.match(html,/data-quote-tile="ZERO" data-tone="unchanged" data-status="fresh"/);
  assert.match(html,/data-quote-tile="OLD" data-tone="neutral" data-status="stale"/);
  assert.match(html,/data-quote-tile="MISSING" data-tone="neutral" data-status="unavailable"/);
  assert.match(html,/SSI:fixture/);assert.match(html,/datetime="2026-10-16T06:59:59Z"/i);
  assert.match(html,/Reference price/);assert.match(html,/10,000 VND/);assert.match(html,/\+200 VND/);
  assert.match(html,/Only the equities on this loaded page/);assert.match(html,/not market value, money flow or strength/);
  assert.doesNotMatch(html,/\bNaN\b|\bInfinity\b|Mark.*reviewed|review update/i);
});
test('VI and EN translate map scope, freshness and session while preserving exact source identity',()=>{
  const vi=render('vi'),en=render();
  assert.match(vi,/Bản đồ giá · trang hiện tại/);assert.match(vi,/Dữ liệu thị trường quá hạn/);
  assert.match(vi,/Đang trong phiên giao dịch|Phiên giao dịch đang diễn ra/);
  assert.match(vi,/Tên nguồn AAA/);assert.match(en,/Source name AAA/);
  assert.match(vi,/SSI:fixture/);assert.match(vi,/10\.200/);
  const watched=render('en',{scope:'watchlist'});
  assert.match(watched,/Only your followed stocks/);assert.doesNotMatch(watched,/Only the equities on this loaded page/);
});
test('unavailable batch keeps the scoped stocks navigable without filling price, percentage or source',()=>{
  const html=render('en',{data:null});
  assert.equal((html.match(/data-status="unavailable"/g)||[]).length,4);
  assert.equal((html.match(/href="\/stocks\//g)||[]).length,4);
  assert.doesNotMatch(html,/0%|SSI:fixture|<time/);
});
