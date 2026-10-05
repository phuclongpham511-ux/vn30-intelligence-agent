import test from "node:test";
import assert from "node:assert/strict";
import { loadCommunity } from "../lib/community.ts";
import { readNewsView, newsViewQuery, emptyNewsFilters } from "../lib/news.ts";

test("community is directly reachable through a separate News view", () => {
  const query = newsViewQuery(emptyNewsFilters, "community", true);
  assert.equal(readNewsView(query).view, "community");
});

test("community query is separate from publisher filtering and failures remain unknown", async () => {
  const original = globalThis.fetch;
  try {
    globalThis.fetch = async url => {
      const query = new URL(url, "http://localhost");
      assert.equal(query.pathname, "/api/community/pulse");
      assert.equal(query.searchParams.get("ticker"), "XYZ");
      assert.equal(query.searchParams.get("topic"), "Earnings");
      assert.equal(query.searchParams.get("financial_only"), null);
      return { ok: true, json: async () => ({ threads: [], source: { status: "not_attempted" } }) };
    };
    const data = await loadCommunity(" xyz ", "Earnings");
    assert.equal(data.source.status, "not_attempted");
    globalThis.fetch = async () => ({ ok: false });
    await assert.rejects(loadCommunity("", ""), /unavailable/);
  } finally { globalThis.fetch = original; }
});
