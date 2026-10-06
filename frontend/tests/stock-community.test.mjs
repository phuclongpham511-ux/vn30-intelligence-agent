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
  replies: null, views: null, activity_at: null, last_seen_at: "2026-10-06T10:00:00Z" };
const pulse = { sampled_threads: 1, threads: [thread], source: { name: "F319", url: "https://newf319.com/",
  status: "healthy", last_success_at: "2026-10-06T10:00:00Z" } };
const render = props => renderToStaticMarkup(React.createElement(CommunityDiscussions,
  { ticker: "XYZ", data: pulse, loading: false, error: false, retry() {}, ...props }));

test("Stock Detail renders matched public evidence, safe original links and unavailable counts", () => {
  const html = render();
  assert.match(html, /Example Company public discussion/);
  assert.match(html, /href="https:\/\/newf319.com\/threads\/example.22\/" target="_blank" rel="noopener noreferrer"/);
  assert.match(html, /Replies unavailable/);
  assert.match(html, /Views unavailable/);
  assert.doesNotMatch(html, /0 replies|0 views|Mark .*reviewed/);
  const unsafe = render({ data: { ...pulse, threads: [{ ...thread, url: "javascript:alert(1)" }] } });
  assert.doesNotMatch(unsafe, /javascript:/);
});

test("Stock Detail distinguishes healthy empty, stale, acquisition error, never checked and read failure", () => {
  assert.match(render({ data: { ...pulse, threads: [] } }), /No discussions matched XYZ/);
  for (const [status, message] of [["stale", /may be stale/], ["error", /latest source acquisition failed/],
    ["not_attempted", /has not been checked yet/]]) {
    assert.match(render({ data: { ...pulse, threads: [], source: { ...pulse.source, status } } }), message);
  }
  assert.match(render({ error: true }), /Counts are unknown/);
  assert.match(render({ loading: true }), /Loading Community discussions/);
});

test("Community renderer never auto-reviews and uses only thread identities for new badges", () => {
  let reviews = 0;
  const review = () => reviews++;
  const unreviewed = render({ review });
  assert.match(unreviewed, /Mark 1 discussion reviewed/);
  assert.match(unreviewed, /Not reviewed yet/);
  assert.equal(reviews, 0);
  assert.doesNotMatch(render({ review, seen: [thread.id], data: { ...pulse,
    threads: [{ ...thread, replies: 1000, views: 9999 }] } }), /Mark 1 discussion reviewed|>New</);
  assert.match(render({ review, seen: [thread.id], data: { ...pulse,
    threads: [{ ...thread, id: "new-thread" }] } }), /1 new since your Community review/);
});
