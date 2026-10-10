import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {transformSync} from 'next/dist/build/swc/index.js';
import {parseTechnicalResponse,loadTechnical} from '../lib/technical-insights.ts';
import {LanguageContext,localeTools} from '../lib/i18n.ts';
const require=createRequire(import.meta.url);
const exports={};
new Function('require','exports',transformSync(readFileSync(new URL('../app/components/stock/TechnicalInsights.tsx',import.meta.url),'utf8'),{filename:'TechnicalInsights.tsx',module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code)(name=>require(name.startsWith('@/lib/')?`../lib/${name.slice(6)}.ts`:name),exports);
const event=(id)=>({event_id:id,event_type:'unusual_volume',ticker:'XYZ',trading_session:'2026-10-08',eligible:true,is_fixture:false,direction:'up',evidence:[{metric:'volume',value:12345,unit:'shares'}],evidence_refs:['source:receipt']});
export const packet={kind:'provisional_packet',assurance:'PROVISIONAL',safe_to_display_as_verified:false,snapshot_id:'snapshot-1',snapshot_version:1,persisted_at:'2026-10-10T06:30:00Z',last_checked_at:'2026-10-10T06:30:00Z',next_check_due_at:'2026-10-11T06:30:00Z',freshness:'FRESH',packet:{ticker:'XYZ',trading_session:'2026-10-08',packet_id:'packet-1',generated_at:'2026-10-10T06:30:00Z',packet_state:'NO_MEANINGFUL_TECHNICAL_CHANGE',top_insights:[],family_checks:[],limitations:[],data_provenance:{completion_assurance:'PROVISIONAL',source:'SSI:FastConnect'}}};
const diagnostic={kind:'diagnostic',ticker:'XYZ',requested_session:null,readiness_status:'INCOMPLETE_EVIDENCE',reason_codes:['missing_persisted_eod_snapshot'],safe_to_display_as_verified:false};
const render=(data=packet,other={},language='en')=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(exports.TechnicalInsightsView,{ticker:'XYZ',data:parseTechnicalResponse(data,'XYZ'),loading:false,error:false,retry(){},...other})));
test('accepted earlier session is explicit, provisional and honestly empty',()=>{
 const html=render();assert.match(html,/PROVISIONAL/);assert.match(html,/8 Oct 2026/);assert.match(html,/No meaningful technical change/);assert.match(html,/Delayed session review/);assert.doesNotMatch(html,/VERIFIED|same-day coverage/);
});
test('keeps engine ordering and displays at most three supplied insights with inspectable evidence',()=>{
 const data={...packet,packet:{...packet.packet,packet_state:'HAS_INSIGHTS',top_insights:['a','b','c','d'].map(event)}};
 const html=render(data);assert.equal((html.match(/data-insight=/g)||[]).length,3);assert.match(html,/12345/);assert.match(html,/source:receipt/);assert.doesNotMatch(html,/data-insight="d"/);
});
test('missing evidence, retraction, errors and loading never show an old insight',()=>{
 assert.match(render(diagnostic),/not yet accepted/);
 assert.match(render({...diagnostic,requested_session:'2026-10-08',reason_codes:['source_revision_detected']}),/withdrawn/);
 assert.doesNotMatch(render(packet,{error:true}),/No meaningful technical change/);
 assert.match(render(packet,{error:true}),/temporarily unavailable/);
 assert.match(render(packet,{loading:true}),/Loading Technical Insights/);
});
test('rejects wrong ticker, verified assurance, bad timestamps and fixture events',()=>{
 for(const data of [{...packet,assurance:'VERIFIED'},{...packet,safe_to_display_as_verified:true},{...packet,last_checked_at:'invalid'},{...packet,packet:{...packet.packet,ticker:'OTHER'}},{...packet,packet:{...packet.packet,packet_state:'HAS_INSIGHTS',top_insights:[{...event('a'),is_fixture:true}]}}])assert.throws(()=>parseTechnicalResponse(data,'XYZ'));
});
test('corrected versions replace identity, stale source checks stay visibly stale and Vietnamese chrome translates',()=>{
 const corrected={...packet,snapshot_id:'snapshot-2',snapshot_version:2,freshness:'STALE'};
 assert.equal(parseTechnicalResponse(corrected,'XYZ').snapshot_version,2);
 assert.match(render(corrected),/Source check overdue/);assert.match(render(packet,{},'vi'),/Không có thay đổi kỹ thuật đáng chú ý/);assert.match(render(packet),/SSI:FastConnect/);
});
test('an incomplete accepted packet withholds insights and never becomes a no-change result',()=>{
 const data={...packet,packet:{...packet.packet,packet_state:'TECHNICAL_DATA_UNAVAILABLE_OR_INCOMPLETE'}};
 assert.match(render(data),/evidence is incomplete/);assert.doesNotMatch(render(data),/No meaningful technical change/);
});
test('loader uses persisted latest API without guessing a date; failures reject instead of keeping old data',async()=>{
 let url,options;const abort=new AbortController();
 const loaded=await loadTechnical('XYZ',abort.signal,async(u,o)=>{url=u;options=o;return {ok:true,json:async()=>packet};});
 assert.equal(url,'/api/technical/XYZ/daily/operational/latest');assert.equal(options.cache,'no-store');assert.equal(loaded.snapshot_id,'snapshot-1');
 await assert.rejects(loadTechnical('XYZ',abort.signal,async()=>({ok:false})));abort.abort();await assert.rejects(loadTechnical('XYZ',abort.signal,async()=>({ok:true,json:async()=>packet})));
});
