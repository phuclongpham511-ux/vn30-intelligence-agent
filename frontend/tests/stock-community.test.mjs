import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { transformSync } from "next/dist/build/swc/index.js";

// Exercise the actual shared renderer without introducing a DOM testing dependency.
const require = createRequire(import.meta.url);
const source = readFileSync(new URL("../app/components/stock/StockCommunity.tsx", import.meta.url), "utf8");
const compiled = transformSync(source, { filename: "StockCommunity.tsx", module: { type: "commonjs" },
  jsc: { parser: { syntax: "typescript", tsx: true }, transform: { react: { runtime: "automatic" } } },
}).code;
const exports = {};
new Function("require", "exports", compiled)(name => require(name.startsWith("@/lib/")
  ? `../lib/${name.slice(6)}.ts` : name), exports);
const { CommunityDiscussions } = exports;
const thread = { id: "thread-one", title: "Example Company public discussion", url: "https://newf319.com/threads/example.22/",
  replies: null, views: null, source_id: "f319_public", tickers: ["XYZ"], excerpt: "XYZ test support", published_at: "2026-10-06T10:00:00Z" };
const pulse = { window: { label: "Today", start: "2026-10-05T17:00:00Z" }, unique_items: 1, items: [thread], themes: [{id: "levels", label: "Technical levels", summary: "XYZ test support", keywords: [], item_count: 1, source_count: 1, source_ids: ["f319_public"], latest_at: thread.published_at, evidence_ids: [thread.id]}], sources: [{ source_id: "f319_public", enabled: true, name: "F319", url: "https://newf319.com/",
  status: "healthy", last_success_at: "2026-10-06T10:00:00Z" }] };
const render = props => renderToStaticMarkup(React.createElement(CommunityDiscussions,
  { ticker: "XYZ", data: pulse, loading: false, error: false, retry() {}, ...props }));

test('theme hierarchy hides secondary excerpts and legacy generic titles retain grounded evidence', () => {
  const html = render({data:{...pulse,themes:[{...pulse.themes[0],label:'Discussion phrasing'}]}});
  assert.doesNotMatch(html,/Discussion phrasing/);
  assert.match(html,/Example Company public discussion/);
  assert.match(html,/line-clamp-2/);
  assert.match(html,/1 discussion · 1 source/);
  assert.match(html,/<details[^>]*><summary[^>]*>View discussions/);
  assert.match(html,/Investor discussion · unverified/);
});

test("Stock Detail renders matched public evidence, safe original links and unavailable counts", () => {
  const html = render();
  assert.match(html, /Example Company public discussion/);
  assert.match(html, /href="https:\/\/newf319.com\/threads\/example.22\/" target="_blank" rel="noopener noreferrer"/);
  assert.match(html, /Replies unavailable/);
  assert.match(html, /Views unavailable/);
  assert.doesNotMatch(html, /0 replies|0 views|Mark .*reviewed/);
  const unsafe = render({ data: { ...pulse, items: [{ ...thread, url: "javascript:alert(1)" }] } });
  assert.doesNotMatch(unsafe, /javascript:/);
});

test('compact Home pulse shows at most three evidence themes with source links and explicit activity semantics',()=>{
 const data={...pulse,as_of:'2026-10-06T10:30:00Z',themes:Array.from({length:4},(_,n)=>({...pulse.themes[0],id:`theme-${n}`,label:`Observed topic ${n}`,representative_id:thread.id})),sources:[{...pulse.sources[0],status:'stale'}]};
 const html=render({data,compact:true,showHeading:false});
 assert.equal((html.match(/<h3/g)||[]).length,3);
 assert.doesNotMatch(html,/Observed topic 3|All evidence/);
 assert.match(html,/Discussion activity, not sentiment/);assert.match(html,/Sample evaluated/);
 assert.match(html,/Sources need a fresh worker check/);assert.match(html,/F319/);
 assert.equal((html.match(/>Original discussion ↗<\/a>/g)||[]).length,6); // Direct links + bounded disclosed evidence.
 assert.match(html,/Source coverage/);assert.match(html,/Last successful fetch/);
 assert.doesNotMatch(html,/0 replies|0 views|FOMO|sentiment score/);
});

test("Stock Detail distinguishes healthy empty, stale, acquisition error, never checked and read failure", () => {
  assert.match(render({ data: { ...pulse, items: [] } }), /No same-day discussions matched XYZ/);
  for (const [status, message] of [["stale", /may be stale/], ["error", /latest source acquisition failed/],
    ["not_attempted", /has not been checked yet/]]) {
    assert.match(render({ data: { ...pulse, items: [], sources: [{ ...pulse.sources[0], status }] } }), message);
  }
  assert.match(render({ error: true }), /Counts are unknown/);
  assert.match(render({ loading: true }), /Loading Community discussions/);
});

test("Community renderer never auto-reviews and uses only evidence identities for new badges", () => {
  let reviews = 0;
  const review = () => reviews++;
  const unreviewed = render({ review });
  assert.match(unreviewed, /Mark 1 discussion reviewed/);
  assert.match(unreviewed, /Not reviewed yet/);
  assert.equal(reviews, 0);
  assert.doesNotMatch(render({ review, seen: [thread.id], data: { ...pulse,
    items: [{ ...thread, replies: 1000, views: 9999 }] } }), /Mark 1 discussion reviewed|>New</);
  assert.match(render({ review, seen: [thread.id], data: { ...pulse,
    items: [{ ...thread, id: "new-thread" }] } }), /1 new since your Community review/);
});
