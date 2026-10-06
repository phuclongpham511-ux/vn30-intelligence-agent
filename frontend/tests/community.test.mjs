import test from "node:test";
import assert from "node:assert/strict";
import { loadCommunity, loadCommunityUpdates, communityEvidence, communitySourceMessage } from "../lib/community.ts";

test("stock discussion evidence preserves its original link and missing lifetime counts", () => {
  const thread={url:'https://newf319.com/threads/example.22/',replies:null,views:null,activity_at:null,last_seen_at:'2026-10-06T10:00:00Z'};
  const evidence=communityEvidence(thread);
  assert.equal(evidence.url,thread.url);
  assert.equal(evidence.replies,'Replies unavailable');
  assert.equal(evidence.views,'Views unavailable');
  assert.equal(evidence.timeLabel,'Observed');
  assert.equal(communityEvidence({...thread,replies:0,views:12}).replies,'0 replies');
  assert.equal(communityEvidence({...thread,url:'javascript:alert(1)'}).url,null);
  assert.match(communitySourceMessage('healthy'),/sample/i);
  assert.match(communitySourceMessage('stale'),/stale/i);
  assert.match(communitySourceMessage('error'),/failed/i);
  assert.match(communitySourceMessage('not_attempted'),/not been checked/i);
});

test("Community monitoring isolates ticker request failures without fabricating empty data",async()=>{
  const requests=[];
  const result=await loadCommunityUpdates(['XYZ','ABC'],undefined,async ticker=>{
    requests.push(ticker);
    if(ticker==='ABC') throw Error('offline');
    return {threads:[{id:'one'}],source:{status:'stale'}};
  });
  assert.deepEqual(requests,['XYZ','ABC']);
  assert.equal(result[0].data.source.status,'stale');
  assert.equal(result[1].data,null);
});
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
