import test from "node:test";
import assert from "node:assert/strict";
import { emptyWatchlist, readWatchlist, followStock, unfollowStock, markReviewed, unreviewedStories, loadWatchlistUpdates } from "../lib/watchlist.ts";

test("browser membership survives serialization, deduplicates and removes review state", () => {
  let state = followStock(followStock(emptyWatchlist(), "XYZ"), "XYZ");
  state = markReviewed(state, "XYZ", [{ story_id: "one" }]);
  assert.deepEqual(readWatchlist(JSON.stringify(state)), state);
  assert.deepEqual(unfollowStock(state, "XYZ"), emptyWatchlist());
  assert.deepEqual(readWatchlist(null), emptyWatchlist());
  assert.throws(() => readWatchlist('{broken'));
  assert.throws(() => readWatchlist('{"symbols":["BAD!"],"seen":{}}'));
});

test("review is explicit, same story stays reviewed and another source is not a new development", () => {
  const state = followStock(emptyWatchlist(), "XYZ");
  const stories = [{ story_id: "one" }, { story_id: "one" }, { story_id: "two" }];
  assert.deepEqual(unreviewedStories(stories), ["one", "two"]);
  const reviewed = markReviewed(state, "XYZ", stories);
  assert.equal(state.seen.XYZ, undefined);
  assert.deepEqual(unreviewedStories(stories, reviewed.seen.XYZ), []);
  assert.deepEqual(unreviewedStories([...stories, { story_id: "three" }], reviewed.seen.XYZ), ["three"]);
  assert.deepEqual(unreviewedStories([], reviewed.seen.XYZ), []);
});

test("monitoring requests only watched symbols and never converts failure to no-change", async () => {
  let sent;
  const data = { stocks: [{ symbol: "XYZ", status: "ready", developments: [] }] };
  const result = await loadWatchlistUpdates(["XYZ"], undefined, async (url, options) => {
    assert.equal(url, "/api/watchlists/monitoring"); sent = JSON.parse(options.body);
    return { ok: true, json: async () => data };
  });
  assert.deepEqual(sent, { symbols: ["XYZ"] }); assert.deepEqual(result, data);
  await assert.rejects(loadWatchlistUpdates(["XYZ"], undefined, async () => ({ ok: false })), /unavailable/);
  await assert.rejects(loadWatchlistUpdates(["XYZ"], undefined, async () => { throw new Error("offline"); }), /offline/);
});
