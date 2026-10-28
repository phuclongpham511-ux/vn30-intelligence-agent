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
new Function('require','exports',code)(name=>name==='./ProvisionalEvidence'?{__esModule:true,default:()=>null}:name==='./TradingActivity'?{__esModule:true,default:()=>null}:name==='./LivePrice'?{useLivePrices:()=>({data:null,failed:false})}:
  require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
const stocks=['AAA','ZERO','OLD','MISSING'].map(symbol=>({symbol,company_name:'Tên nguồn '+symbol,display_name_en:'Source name '+symbol,exchange:'HOSE'}));
const data={items:{AAA:quote(),ZERO:quote({ticker:'ZERO',change:0,change_percent:0}),
  OLD:{...quote({ticker:'OLD'}),status:'stale'}},session:'active',as_of:now.toISOString()};
const render=(language='en',props={})=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,
  {value:localeTools(language)},React.createElement(exports.QuoteMapView,{stocks,data,scope:'page',now,...props})));

test('reading guidance follows tile order without changing panel or movement instructions in EN/VI',()=>{
  for(const [language,grid,panel,movement] of [
    ['en','Read left → right across each row, then top → bottom.','Read down each panel, then left → right.','Movement within this selection only · not sectors.'],
    ['vi','Đọc từng hàng từ trái → phải, rồi trên → dưới.','Đọc từng bảng từ trên xuống, rồi trái → phải.','Chỉ biến động trong mẫu đang chọn · không phải ngành.'],
  ]) {
    const footnote=props=>render(language,props).match(/<p class="quote-footnote">([\s\S]*?)<\/p>/)[1];
    assert.ok(footnote({mode:'heatmap'}).includes(grid));
    assert.ok(footnote({mode:'board'}).includes(panel));
    for(const mode of ['board','heatmap'])assert.ok(footnote({mode,organization:'movement'}).includes(movement));
  }
});

test('industry uses the existing board tables only for labeled replay synthetic instruments',()=>{
 const previous=process.env.NEXT_PUBLIC_WOOFI_VALIDATION;
 const stocks=['DEMO01','DEMO02','DEMO03'].map(symbol=>({symbol}));
 const demo={items:Object.fromEntries(stocks.map(s=>[s.symbol,quote({ticker:s.symbol})])),session:'active',as_of:now.toISOString()};
 const props={stocks,data:demo,organization:'industry',industryPreview:{kind:'synthetic',label:'DEMO',categories:{DEMO01:{code:'demo',name:'DEMO Products'},DEMO02:{code:'demo',name:'DEMO Products'}}}};
 try {
  delete process.env.NEXT_PUBLIC_WOOFI_VALIDATION;
  assert.doesNotMatch(render('en',props),/data-industry-demo|value="industry"/);
  process.env.NEXT_PUBLIC_WOOFI_VALIDATION='replay';
  const html=render('en',props);
  assert.match(html,/DEMO Products/);assert.match(html,/Unclassified/);assert.match(html,/2 stocks · DEMO/);
  assert.equal((html.match(/data-quote-row=/g)||[]).length,3);
  assert.match(html,/Trading value|>Value</);assert.match(html,/value="industry"/);
  const heatmap=render('en',{...props,mode:'heatmap'});
  assert.doesNotMatch(heatmap,/data-industry-demo/);
  assert.equal((heatmap.match(/data-quote-tile=/g)||[]).length,3);
 } finally {if(previous===undefined)delete process.env.NEXT_PUBLIC_WOOFI_VALIDATION;else process.env.NEXT_PUBLIC_WOOFI_VALIDATION=previous;}
});

test('rendered board retains all identities, exact prices/times and keyboard source controls',()=>{
  const html=render();
  assert.equal((html.match(/data-quote-row=/g)||[]).length,4);
  assert.equal((html.match(/href="\/stocks\//g)||[]).length,4);
  assert.match(html,/data-quote-row="ZERO" data-tone="unchanged" data-status="fresh"/);
  assert.match(html,/data-quote-row="OLD" data-tone="neutral" data-status="stale"/);
  assert.match(html,/data-quote-row="MISSING" data-tone="neutral" data-status="unavailable"/);
  assert.match(html,/datetime="2026-10-16T06:59:59Z"/i);
  assert.match(html,/10,200/);assert.match(html,/\+2%/);
  assert.equal((html.match(/aria-label="Quote source for /g)||[]).length,4);
  assert.match(html,/3\/4 quotes/);assert.match(html,/not synchronized market-wide coverage/);
  assert.doesNotMatch(html,/\bNaN\b|\bInfinity\b|Mark.*reviewed|review update/i);
});
test('VI and EN translate map scope, freshness and session while preserving exact source identity',()=>{
  const vi=render('vi'),en=render();
  assert.match(vi,/Bảng giá/);assert.match(vi,/Dữ liệu thị trường quá hạn/);
  assert.match(vi,/Tên nguồn AAA/);assert.match(en,/Source name AAA/);
  assert.match(vi,/10\.200/);
  const watched=render('en',{scope:'watchlist'});
  assert.match(watched,/Only your followed stocks/);assert.doesNotMatch(watched,/Only the equities on this loaded page/);
});
test('unavailable batch keeps the scoped stocks navigable without filling price, percentage or source',()=>{
  const html=render('en',{data:null});
  assert.equal((html.match(/data-status="unavailable"/g)||[]).length,4);
  assert.equal((html.match(/href="\/stocks\//g)||[]).length,4);
  assert.doesNotMatch(html,/0%|SSI:fixture|<time/);
});


test('heatmap and table keep the same source identities, prices and freshness without a new request',()=>{
  const html=render('en',{mode:'heatmap'});
  assert.equal((html.match(/data-quote-tile=/g)||[]).length,4);
  assert.equal((html.match(/href="\/stocks\//g)||[]).length,4);
  assert.match(html,/heatmap-compact/);assert.equal((html.match(/class="quote-compact-source"/g)||[]).length,4);
  assert.match(html,/data-quote-tile="OLD" data-tone="neutral" data-status="stale"/);
  assert.match(html,/no capitalization weighting/);
});
test('Watchlist retains detailed cells without the workspace density control',()=>{
  const html=render('en',{scope:'watchlist',mode:'heatmap'});
  assert.match(html,/heatmap-detailed/);assert.match(html,/10,200/);
  assert.doesNotMatch(html,/aria-label="Heatmap density"/);
});
test('pending quote request is loading, while a completed empty response is genuinely missing',()=>{
  const pending=render('en',{data:null});
  assert.match(pending,/Loading observed quotes/);assert.doesNotMatch(pending,/No observed quotes for this selection/);
  const empty=render('en',{data:{items:{},session:'unknown',as_of:now.toISOString()}});
  assert.match(empty,/0\/4 quotes/);assert.match(empty,/No observed quotes for this selection/);
});

test('failed initial quote request leaves coverage unknown rather than certifying missing quotes',()=>{
  for(const language of ['en','vi']){
    const html=render(language,{data:null,failed:true});
    assert.match(html,language==='en'?/Quote coverage unavailable/:/Chưa xác định được độ phủ báo giá/);
    assert.doesNotMatch(html,/0\/4 quotes|4 missing|No observed quotes for this selection|4 chưa có/);
    assert.doesNotMatch(html,/Loading observed quotes|0%/);
    assert.equal((html.match(/href="\/stocks\//g)||[]).length,4);
  }
});
test('failed refresh retains old values neutrally but coverage remains unknown for the visible sample',()=>{
  const html=render('en',{failed:true,scopeLabel:'VN100'});
  assert.match(html,/VN100/);assert.match(html,/Visible sample/);assert.match(html,/Quote coverage unavailable/);
  assert.doesNotMatch(html,/3\/4 quotes/);assert.match(html,/10,200/);
  assert.match(html,/data-quote-row="AAA" data-tone="neutral" data-status="stale"/);
});

test('controlled movement view partitions the filtered sample and leaves unavailable request counts unknown',()=>{
  const html=render('en',{organization:'movement',sorting:'ticker'});
  assert.match(html,/Advancing/);assert.match(html,/Declining/);assert.match(html,/Stale \/ Missing/);
  assert.equal((html.match(/data-quote-row=/g)||[]).length,4);
  const filtered=render('en',{organization:'movement',stocks:stocks.slice(0,1)});
  assert.equal((filtered.match(/data-quote-row=/g)||[]).length,1);
  assert.match(filtered,/1<!-- --> stocks|1 stocks/);
  const failed=render('en',{organization:'movement',data:null,failed:true});
  assert.match(failed,/Quote coverage unavailable/);assert.doesNotMatch(failed,/0\/4 quotes|4 missing/);
});
