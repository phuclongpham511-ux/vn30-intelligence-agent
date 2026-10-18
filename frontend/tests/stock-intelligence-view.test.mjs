import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
import {packet,saved,news,discussion,forum} from './fixtures/stock-intelligence.mjs';
const require=createRequire(import.meta.url),exports={};
const code=transformSync(readFileSync(new URL('../app/components/stock/StockIntelligence.tsx',import.meta.url),'utf8'),{filename:'StockIntelligence.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
new Function('require','exports',code)(name=>require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
function render(props={},language='en'){
 return renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:localeTools(language)},React.createElement(exports.StockIntelligenceView,{ticker:'AAA',data:packet(),state:saved(),retry(){},review(){},...props})));
}
test('actual compact renderer separates publication, observation, source status and original evidence',()=>{
 const html=render({data:packet([news,news],[discussion,discussion])});
 assert.equal((html.match(/data-stock-update="news:story"/g)||[]).length,1);
 assert.equal((html.match(/data-stock-update="community:thread"/g)||[]).length,1);
 assert.match(html,/Published/);assert.match(html,/First observed/);assert.match(html,/Last observed/);
 assert.match(html,/2026-10-18T02:00:00Z/);assert.match(html,/2026-10-18T03:00:00Z/);
 assert.match(html,/href="https:\/\/publisher.example\/a"/);assert.match(html,/F319/);
 assert.match(html,/Replies unavailable/);assert.match(html,/0 views/);assert.doesNotMatch(html,/0 replies|sentiment score|FOMO score/);
 assert.match(html,/Stored ticker match; detailed proof unavailable/);assert.match(html,/DEMO/);
 assert.match(html,/<details[^>]*><summary[^>]*>Community context/);assert.match(html,/unverified/);
});
test('review controls are explicit and opening/SSR never changes browser reviews',()=>{
 let reviews=0;const html=render({review(){reviews++;}});
 assert.match(html,/aria-label="Mark reviewed: AAA reports earnings"/);assert.equal(reviews,0);
 assert.match(html,/1 unreviewed loaded stories/);assert.match(html,/Last recorded review/);
 assert.doesNotMatch(render({storageError:true}),/aria-label="Mark reviewed:/);
 assert.match(render({storageError:true}),/Unread counts are unknown/);
 assert.doesNotMatch(render({state:{...saved(),symbols:['BBB']}}),/aria-label="Mark reviewed:/);
 assert.match(render({state:{...saved(),symbols:['BBB']}}),/Follow this stock/);
});
test('loading, error, empty, wrong-ticker and stale coverage remain distinct',()=>{
 assert.match(render({data:null}),/Loading company research/);
 const failed=render({error:true});assert.match(failed,/Unread counts are unknown/);assert.doesNotMatch(failed,/No matching stored|data-stock-update=/);
 assert.match(render({data:packet([],[])}),/does not establish that no development occurred/);
 assert.match(render({ticker:'BBB'}),/Company research is unavailable/);
 const stale={...packet(),community_sources:[{...forum,status:'stale'}]};
 assert.match(render({data:stale}),/Fetch overdue/);assert.match(render({data:stale}),/Coverage incomplete/);
 assert.match(render({data:stale}),/Source status at read/);
});
test('overview preview is bounded and both languages retain coherent research navigation',()=>{
 const many=Array.from({length:9},(_,index)=>({...news,id:'news:story'+index,entity_id:'story'+index}));
 assert.equal((render({preview:true,data:packet(many,[])}).match(/data-stock-update="news:/g)||[]).length,3);
 assert.equal((render({data:packet(many,[])}).match(/data-stock-update="news:/g)||[]).length,6);
 const vi=render({},'vi');assert.match(vi,/Cập nhật nghiên cứu doanh nghiệp/);assert.match(vi,/AAA reports earnings/);
 for(const href of ['#stock-fundamentals','#stock-actions','#stock-news','/watchlist'])assert.ok(vi.includes(`href="${href}"`));
 assert.match(vi,/72 giờ/);assert.match(vi,/24 giờ/);
});
