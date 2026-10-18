import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
import {provisionalSsiEnabled,provisionalSsiLocalHost,provisionalMarketRecord,provisionalBoardRecords,provisionalFreshness,sortProvisionalRows} from '../lib/provisionalMarket.ts';
import {activityValue} from '../lib/tradingActivity.ts';
import {resolvePriceState} from '../lib/priceState.ts';

const require=createRequire(import.meta.url);
const saved=JSON.parse(readFileSync(new URL('../app/internal/ssi-market/saved-acb.json',import.meta.url),'utf8'));
const now=new Date('2026-10-18T08:00:00Z'),stock={symbol:'ACB',exchange:'HOSE'};
const clone=()=>structuredClone(saved);
const flagNames=['NODE_ENV','NEXT_PUBLIC_WOOFI_SSI_PROVISIONAL','NEXT_PUBLIC_WOOFI_VALIDATION'];
function flags(values=['development','1','replay']) {const before=flagNames.map(k=>process.env[k]);flagNames.forEach((k,i)=>values[i]===undefined?delete process.env[k]:process.env[k]=values[i]);return()=>flagNames.forEach((k,i)=>before[i]===undefined?delete process.env[k]:process.env[k]=before[i]);}
function load(file,extra={}) {
 const code=transformSync(readFileSync(new URL('../'+file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 const exports={};new Function('require','exports',code)(name=>extra[name]??(name==='./LivePrice'?{useLivePrices:()=>({data:null,failed:false})}:name==='./TradingActivity'?{__esModule:true,default:()=>null}:name==='./ProvisionalEvidence'?load('app/components/stock/ProvisionalEvidence.tsx'):require(name.startsWith('@/lib/')?'../lib/'+name.slice(6)+'.ts':name)),exports);return exports;
}
const view=load('app/components/stock/QuoteMap.tsx').QuoteMapView;
const render=(language='en',props={})=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools(language)},React.createElement(view,{stocks:[stock],data:{items:{},session:'unknown',as_of:now.toISOString()},scope:'page',now,internalProvisional:[saved],...props})));

test('provisional activation requires development, explicit opt-in and isolated replay; production cannot enable it',()=>{
 assert.equal(provisionalSsiEnabled({}),false);
 for(const nodeEnv of ['production','test',undefined])assert.equal(provisionalSsiEnabled({nodeEnv,flag:'1',validation:'replay'}),false);
 assert.equal(provisionalSsiEnabled({nodeEnv:'development',flag:'0',validation:'replay'}),false);
 assert.equal(provisionalSsiEnabled({nodeEnv:'development',flag:'1',validation:'live'}),false);
 assert.equal(provisionalSsiEnabled({nodeEnv:'development',flag:'1',validation:'replay'}),true);
 for(const host of ['127.0.0.1:3410','localhost:3410','[::1]:3410'])assert.equal(provisionalSsiLocalHost(host,null),true);
 for(const host of [null,'woofi.example','localhost.evil:3410','127.0.0.1:3410.evil'])assert.equal(provisionalSsiLocalHost(host,null),false);
 assert.equal(provisionalSsiLocalHost('127.0.0.1:3410','public.example'),false);
});
test('saved ACB transport keeps provisional identity, dates, units and receipts without promoting to a live DTO',()=>{
 const p=provisionalMarketRecord(saved,stock,now);assert.ok(p);
 assert.equal(p.bands.reference.value,20600);assert.equal(p.matched.volume.value,5160300);
 assert.equal(p.matched.value.value,106488260000);assert.equal(p.matched.source_timestamp,null);
 assert.equal(provisionalFreshness(p,now),'stale');assert.equal(p.public_display_eligible,false);
 const row={ticker:'ACB',last_price:22000,price_unit:'VND',reference_price:20600,change:1400,change_percent:6.796,trading_date:'2026-10-18',updated_at:now.toISOString(),session:'active',trading_activity:p.matched,price_limits:p.bands};
 assert.equal(activityValue(row,'volume','fresh',now),null);
 assert.equal(resolvePriceState('ACB',row,'fresh',now),'ADVANCING');
});
test('transport rejects mismatched dates, identity, units, receipts, rights promotion and malformed packets',()=>{
 for(const change of [p=>p.key.symbol='OTHER',p=>p.key.exchange='HNX',p=>p.key.trading_date='2026-02-30',p=>p.public_display_eligible=true,p=>p.qualification='QUALIFIED',p=>p.bands.floor.value=23000,p=>p.matched.volume.value=1.5,p=>p.matched.value.unit='thousand VND',p=>p.matched.volume.multiplier=100,p=>p.bands.ceiling.raw_value=true,p=>p.bands.ceiling.normalized_decimal='',p=>p.receipts.master.raw_record.board='HNX',p=>delete p.receipts.identity.raw_record.board,p=>p.receipts.summary.raw_record.tradingDate='2026/10/15',p=>p.receipts.summary.source_timestamp='2026-10-18T09:00:00Z',p=>p.receipts.summary.document_sha256='bad',p=>p.matched.fetched_at='2026-10-19T00:00:00Z']) {const p=clone();change(p);assert.equal(provisionalMarketRecord(p,stock,now),null);}
 assert.equal(provisionalMarketRecord(null,stock,now),null);
});
test('one selected cohort never merges different dates, duplicate snapshots or incompatible quote references',()=>{
 const rows=provisionalBoardRecords([saved],[stock],null,now,true);assert.equal(rows.size,1);
 assert.equal(provisionalBoardRecords([saved],[stock],null,now,false).size,0);
 assert.equal(provisionalBoardRecords([saved,saved],[stock],null,now,true).size,0);
 assert.equal(provisionalBoardRecords([saved],[stock],{items:{ACB:{snapshot:{ticker:'ACB',trading_date:'2026-10-16',price_unit:'VND',reference_price:20000}}}},now,true).size,0);
 const other=clone();other.key.symbol='BBB';for(const r of Object.values(other.receipts))r.raw_record.symbol='BBB';other.key.trading_date='2026-10-15';for(const name of ['master','summary'])other.receipts[name].raw_record.tradingDate='2026/10/15';
 assert.equal(provisionalBoardRecords([saved,other],[stock,{symbol:'BBB',exchange:'HOSE'}],null,now,true).size,0);
 const stale=clone();stale.freshness.status='fresh';assert.equal(provisionalFreshness(stale,now),'stale','a saved status does not refresh source age');
 assert.equal(provisionalBoardRecords({},[stock],null,now,true).size,0);
});
test('provisional KL/GT sorting compares snapshots, keeps missing last and never adds totals',()=>{
 const p=provisionalMarketRecord(saved,stock,now),other=clone();other.matched.volume.value=1;other.matched.value.value=2;
 const records=new Map([['ACB',p],['BBB',other]]),rows=['MISSING','BBB','ACB'].map(symbol=>({stock:{symbol}}));
 for(const sort of ['volume','value'])assert.deepEqual(sortProvisionalRows(rows,records,sort).map(r=>r.stock.symbol),['ACB','BBB','MISSING']);
 assert.equal(records.get('ACB').matched.volume.value,5160300);
});
test('Board displays saved bands and matched totals only in the internal enabled scope; public paths are unchanged',()=>{
 let restore=flags();try {
  for(const language of ['en','vi']) {const html=render(language);assert.match(html,/PROVISIONAL_INTERNAL/);assert.match(html,/NOT_SSI_CERTIFIED/);assert.match(html,/106[,.]49/);assert.match(html,/data-provisional-band="ceiling"/);assert.match(html,/2026-10-16/);assert.doesNotMatch(html,/data-price-state="CEILING"/);}
  assert.doesNotMatch(render('en',{mode:'heatmap'}),/PROVISIONAL_INTERNAL/);
  assert.doesNotMatch(render('en',{scope:'watchlist'}),/PROVISIONAL_INTERNAL/);
 }finally{restore();}
 for(const config of [['production','1','replay'],['development',undefined,'replay'],['development','1',undefined]]){restore=flags(config);try{const html=render();assert.doesNotMatch(html,/PROVISIONAL_INTERNAL|data-provisional-band/);assert.match(html,/data-volume="ACB">—/);}finally{restore();}}
});
test('internal route fails closed before rendering data in production, disabled, external and forwarded contexts',async()=>{
 const NOT_FOUND=Symbol('not-found');let host='127.0.0.1:3410',forwarded=null,forwardedFor=null;
 const page=load('app/internal/ssi-market/page.tsx',{'next/headers':{headers:async()=>({get:k=>k==='host'?host:k==='x-forwarded-host'?forwarded:forwardedFor})},'next/navigation':{notFound:()=>{throw NOT_FOUND;}},'./InternalBoard':{__esModule:true,default:()=>null},'./saved-acb.json':saved}).default;
 for(const config of [['production','1','replay'],['development',undefined,'replay']]){const restore=flags(config);try{await assert.rejects(page(),e=>e===NOT_FOUND);}finally{restore();}}
 const restore=flags();try {assert.ok((await page()).props.packet);host='public.example';await assert.rejects(page(),e=>e===NOT_FOUND);host='127.0.0.1:3410';forwarded='public.example';await assert.rejects(page(),e=>e===NOT_FOUND);forwarded=null;forwardedFor='1.2.3.4';await assert.rejects(page(),e=>e===NOT_FOUND);}finally{restore();}
});
test('the internal shell never mounts ingestion refresh, universe or ticker acquisition consumers',()=>{
 let path='/internal/ssi-market';const blocked=()=>{throw Error('normal acquisition shell mounted');};
 const Shell=load('app/components/app-shell/AppShell.tsx',{
  'next/navigation':{usePathname:()=>path},'next-themes':{ThemeProvider:({children})=>children,useTheme:()=>({resolvedTheme:'dark',setTheme(){}})},
  '../stock/TickerSearch':{__esModule:true,default:blocked},'../market/MarketSearch':{MarketSearchProvider:blocked,useMarketSearch:()=>({setQuery(){}})},
  '../stock/StockUniverse':{StockUniverse:blocked},'../ui/button':{Button:({variant,size,...props})=>React.createElement('button',props)},'../ui/sheet':{},
 }).default;
 const html=renderToStaticMarkup(React.createElement(Shell,null,'Saved observations'));
 assert.match(html,/Saved observations/);assert.match(html,/Internal provisional SSI data/);assert.doesNotMatch(html,/Search ticker|href="\/stocks/);
 path='/';assert.throws(()=>renderToStaticMarkup(React.createElement(Shell,null,'normal')),/normal acquisition shell mounted/);
});
test('invalid internal packets render a scoped rejection, with no financial values or source navigation',()=>{
 const Board=load('app/internal/ssi-market/InternalBoard.tsx',{'../../components/stock/QuoteMap':{QuoteMapView:view}}).default;
 const html=renderToStaticMarkup(React.createElement(Board,{packet:null,asOf:now.toISOString()}));
 assert.match(html,/role="alert"/);assert.match(html,/Provisional market data rejected/);assert.doesNotMatch(html,/106,488|data-quote-row/);
});
