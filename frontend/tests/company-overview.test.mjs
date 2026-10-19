import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
const require=createRequire(import.meta.url);
function component(file,overrides={}) {
 const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
 const exports={};new Function('require','exports',code)(name=>overrides[name]||require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);return exports.default;
}
const Overview=component('../app/components/stock/CompanyOverview.tsx');
const security={symbol:'DEMO123456789',exchange:'HOSE',company_name:'Tên doanh nghiệp gốc',display_name_en:'Original English issuer',source:'Recorded source identity'};
const render=(Component,props,language='en')=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools(language)},React.createElement(Component,props)));
test('company overview reuses identity and source receipts with honest unsupported profile fields',()=>{
 const html=render(Overview,{security,syncedAt:'2026-10-16T07:00:00Z'});
 assert.match(html,/DEMO123456789/);assert.match(html,/HOSE/);assert.match(html,/Recorded source identity/);
 assert.match(html,/Business description/);assert.match(html,/Not qualified for display/);
 assert.match(html,/Synchronization time is not an issuer publication date/);
 assert.match(html,/datetime="2026-10-16T07:00:00Z"/i);
 assert.match(html,/href="#stock-fundamentals"/);
 assert.doesNotMatch(html,/0 VND|0%|PE =|P\/E =|<script/);
});
test('company overview never activates raw unqualified description or industry and does not fake missing source times',()=>{
 const html=render(Overview,{security:{...security,source:undefined,industry:'UNQUALIFIED INDUSTRY',business_description:'UNQUALIFIED BUSINESS'},syncedAt:null},'vi');
 assert.match(html,/Tổng quan doanh nghiệp/);assert.match(html,/Chưa đủ điều kiện hiển thị/);assert.match(html,/Chưa có dữ liệu/);
 assert.doesNotMatch(html,/UNQUALIFIED INDUSTRY|UNQUALIFIED BUSINESS|datetime=/);
 const invalid=render(Overview,{security:{...security,last_synced_at:'invalid'},syncedAt:null});
 assert.doesNotMatch(invalid,/datetime=/);assert.match(invalid,/Unavailable/);
});
test('company facts prefer per-record sync receipt without altering original source text',()=>{
 const html=render(Overview,{security:{...security,last_synced_at:'2026-10-15T08:00:00Z'},syncedAt:'2026-10-16T07:00:00Z'},'vi');
 assert.match(html,/datetime="2026-10-15T08:00:00Z"/i);assert.doesNotMatch(html,/datetime="2026-10-16/);
 assert.match(html,/Recorded source identity/);
});
test('stock header preserves full ticker, language-specific original issuer name and missing-name behavior',()=>{
 const Header=component('../app/components/stock/StockHeader.tsx',{'./LivePrice':{LivePrices:({children})=>children,LivePrice:()=>null},'./FollowStock':{__esModule:true,default:()=>null}});
 const en=render(Header,{stock:security}),vi=render(Header,{stock:security},'vi');
 assert.match(en,/Original English issuer/);assert.match(vi,/Tên doanh nghiệp gốc/);
 assert.equal((en.match(/DEMO123456789/g)||[]).length,2);assert.match(en,/HOSE/);
 assert.match(render(Header,{stock:{symbol:'XYZ',exchange:null,company_name:null}}),/Company name unavailable/);
});
