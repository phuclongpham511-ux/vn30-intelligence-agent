import test from 'node:test';
import assert from 'node:assert/strict';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {transformSync} from 'next/dist/build/swc/index.js';
import {dailyBriefing,reviewBriefingItem} from '../lib/dailyBriefing.ts';
import {emptyWatchlist,reviewUpdates,readWatchlist,isUnread} from '../lib/watchlist.ts';
import {LanguageContext,localeTools} from '../lib/i18n.ts';

// All evidence in this file is synthetic, not a live market observation.
const at='2026-10-16T06:00:00Z';
const source={source_id:'publisher',name:'Publisher',enabled:true,status:'healthy',last_success_at:at};
const communitySource={...source,source_id:'forum',name:'Forum'};
const news=(id='story',time='2026-10-16T02:00:00Z')=>({
  id:'news:'+id,entity_id:id,revision:'v1',revision_members:{article:'v1'},kind:'news',title:'Original issuer report',occurred_at:'2026-10-16T05:00:00Z',url:'https://publisher.example/'+id,
  evidence:[{id:'article',title:'Original issuer report',url:'https://publisher.example/'+id,source_name:'Publisher',published_at:time,first_seen_at:'2026-10-16T05:00:00Z'}]
});
const community=(id='discussion')=>({id:'community:'+id,entity_id:id,revision:'v1',kind:'community',title:'Original discussion',occurred_at:'2026-10-16T03:00:00Z',url:'https://forum.example/'+id,
  evidence:{id,source_id:'forum',published_at:'2026-10-16T03:00:00Z',is_fixture:true}});
const page=items=>({items,has_more:false,truncated:false});
const row=(symbol,items=[],discussions=[])=>({symbol,status:'ready',news:page(items),community:page(discussions),technical:{items:[{id:'technical:ignored'}]}});
const packet=stocks=>({as_of:at,offset:0,page_size:12,stocks,news_sources:[source],community_sources:[communitySource]});
const saved=(symbols=['AAA','BBB','QUIET'])=>({...emptyWatchlist(),symbols});

test('A/F: one shared Story, separate domains, three-item cap, quiet and unrelated stocks isolated',()=>{
  const state=saved(),shared=news();
  const data=packet([row('AAA',[shared,news('older','2026-10-15T22:00:00Z'),news('oldest','2026-10-15T21:00:00Z')],[community()]),row('BBB',[shared]),row('QUIET'),row('FOREIGN',[news('foreign')])]);
  const before=JSON.stringify({state,data});
  const brief=dailyBriefing(data,state);
  assert.equal(brief.total,4); assert.equal(brief.items.length,3);
  assert.deepEqual(brief.items.map(e=>e.id),['community:discussion','news:story','news:older']);
  assert.deepEqual(brief.items[1].symbols,['AAA','BBB']);
  assert.equal(brief.items[0].fixture,true);
  assert.equal(JSON.stringify({state,data}),before,'opening projection must not mutate evidence or reviews');
  assert.equal(brief.items[1].item,shared,'source evidence retained, no generated summary');
});

test('B/C/D: explicit reviews survive reload; unchanged rechecks stay quiet, known correction reopens',()=>{
  const item=news(),data=packet([row('AAA',[item])]);
  let state=saved(['AAA']);
  state=readWatchlist(JSON.stringify(reviewBriefingItem(state,state,dailyBriefing(data,state).items[0],at)));
  assert.equal(dailyBriefing(data,state).total,0);
  const rechecked={...item,revision:'new-publisher-anchor',source_count:2,revision_members:{article:'v1',newPublisher:'copy'},evidence:[{...item.evidence[0],last_seen_at:at}]};
  assert.equal(dailyBriefing(packet([row('AAA',[rechecked])]),state).total,0);
  const correction={...rechecked,revision_members:{article:'v2',newPublisher:'copy'}};
  const corrected=dailyBriefing(packet([row('AAA',[correction])]),state);
  assert.equal(corrected.total,1); assert.equal(corrected.items[0].corrected,true);
  assert.equal(corrected.items[0].time,item.evidence[0].published_at,'correction never renews publication age');
});

test('explicit brief review affects displayed pairs only, not hidden items or unrelated ticker receipts',()=>{
  const item=news(),other=news('hidden'),state=saved();
  const data=packet([row('AAA',[item,other]),row('BBB',[item]),row('QUIET')]);
  const entry=dailyBriefing(data,state).items.find(e=>e.id===item.id);
  const next=reviewBriefingItem(state,state,entry,at);
  assert.equal(isUnread(next,'AAA',item),false); assert.equal(isUnread(next,'BBB',item),false);
  assert.equal(isUnread(next,'AAA',other),true); assert.equal(next.receipts.QUIET,undefined);
  const removed={...state,symbols:['BBB']};
  assert.equal(reviewBriefingItem(removed,state,entry,at).receipts.AAA,undefined);
  const concurrent=reviewUpdates(state,'AAA',[{...item,revision_members:{article:'v2'}}],at);
  assert.deepEqual(reviewBriefingItem(concurrent,state,entry,at).receipts.AAA,concurrent.receipts.AAA);
});

test('E: source polling freshness remains independent of publication and response time; missing evidence is incomplete',()=>{
  const item=news(),state=saved(['AAA']),data=packet([row('AAA',[item])]);
  data.news_sources=[{...source,status:'stale',last_success_at:'2026-10-15T01:00:00Z'}];
  const brief=dailyBriefing(data,state);
  assert.equal(brief.incomplete,true); assert.equal(brief.items[0].sourceStatus,'stale');
  assert.equal(brief.items[0].time,item.evidence[0].published_at);
  assert.equal(brief.items[0].sourceCheckedAt,data.news_sources[0].last_success_at);
  data.news_sources=[];
  assert.deepEqual(dailyBriefing(data,state),{items:[],total:0,incomplete:true});
  assert.equal(dailyBriefing(packet([{...row('AAA'),status:'unavailable'}]),state).incomplete,true);
});

test('ordering uses actual publication instants, stable identity ties and explicit first-observed fallback',()=>{
  const a=news('a'),b=news('b','2026-10-16T09:00:00+07:00'),unknown=news('unknown',null);
  const brief=dailyBriefing(packet([row('AAA',[b,unknown,a])]),saved(['AAA']));
  assert.deepEqual(brief.items.map(e=>e.id),['news:unknown','news:a','news:b']);
  assert.equal(brief.items[0].published,false); assert.equal(brief.items[0].time,unknown.occurred_at);
  assert.equal(dailyBriefing(packet([row('AAA',[a])]),saved(['AAA'])).items.length,1,'no filler');
});

test('contradictory shared representatives, unsafe URLs and future timestamps are withheld, not trusted',()=>{
  const a=news(),b={...a,revision:'other'};
  assert.equal(dailyBriefing(packet([row('AAA',[a]),row('BBB',[b])]),saved()).items.length,0);
  for(const item of [{...a,url:'javascript:alert(1)'},{...a,title:'Different title'},news('future','2026-10-17T00:00:00Z')]) {
    const result=dailyBriefing(packet([row('AAA',[item])]),saved(['AAA']));
    assert.equal(result.total,0); assert.equal(result.incomplete,true);
  }
});

const require=createRequire(import.meta.url);
const file='../app/components/WatchlistBriefing.tsx';
const code=transformSync(readFileSync(new URL(file,import.meta.url),'utf8'),{filename:file,module:{type:'commonjs'},jsc:{parser:{syntax:'typescript',tsx:true},transform:{react:{runtime:'automatic'}}}}).code;
const exports={};
new Function('require','exports',code)(name=>require(name.startsWith('@/lib/')?'../lib/'+name.slice(6)+'.ts':name),exports);
const render=(props,language='en')=>renderToStaticMarkup(React.createElement(LanguageContext.Provider,{value:{...localeTools(language),setLanguage(){}}},React.createElement(exports.default,props)));

test('EN/VI markup preserves originals, safe source/research links, fixture/unverified labels and responsive wrapping',()=>{
  const props={data:packet([row('AAA',[news()],[community()])]),state:saved(['AAA']),storageError:false,review(){}};
  for(const language of ['en','vi']) {
    const html=render(props,language);
    assert.match(html,/Original issuer report/); assert.match(html,/Original discussion/);
    assert.match(html,/href="https:\/\/publisher.example\/story" target="_blank" rel="noopener noreferrer"/);
    assert.match(html,/href="\/stocks\/AAA"/); assert.match(html,/href="#watchlist-evidence-AAA"/);
    assert.match(html,/flex-wrap/); assert.match(html,/break-words/);
    assert.match(html,language==='vi'?/Đọc trước/:/Read first/);
    assert.match(html,language==='vi'?/Chưa xác minh/:/Unverified/);
    assert.match(html,language==='vi'?/Dữ liệu mẫu/:/Fixture/);
    assert.doesNotMatch(html,/importance score<\/h|BUY|SELL|HOLD/);
  }
});

test('quiet, unreadable storage and overdue coverage remain distinct without enabled review actions',()=>{
  const state=saved(['AAA']),data=packet([row('AAA')]);
  assert.match(render({state,data,storageError:false,review(){}}),/No unreviewed reporting or discussion in the loaded page/);
  const unknown=render({state,data:packet([row('AAA',[news()])]),storageError:true,review(){}});
  assert.match(unknown,/Unread counts are unknown/); assert.doesNotMatch(unknown,/data-briefing-item|Mark this update reviewed|No unreviewed reporting/);
  const stale={...data,news_sources:[{...source,status:'stale'}],stocks:[row('AAA',[news()])]};
  const html=render({state,data:stale,storageError:false,review(){}});
  assert.match(html,/persisted evidence, not a fresh source check/); assert.match(html,/dark:text-amber-300/);
});
