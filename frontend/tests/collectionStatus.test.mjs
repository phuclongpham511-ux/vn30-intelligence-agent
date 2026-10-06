import test from "node:test";
import assert from "node:assert/strict";
import { collectionLabels, fetchTime, newsFreshness } from "../lib/collectionStatus.ts";

test("freshness summary counts enabled healthy feeds and retains honest last success", () => {
  const rows = [
    { enabled: true, status: "healthy", last_success_at: "2026-10-06T05:00:00Z" },
    { enabled: true, status: "error", last_success_at: "2026-10-05T05:00:00Z" },
    { enabled: true, status: "stale", last_success_at: null },
    { enabled: false, status: "disabled", last_success_at: "2026-10-07T05:00:00Z" },
  ];
  assert.deepEqual(newsFreshness(rows), { healthy: 1, enabled: 3, lastSuccess: "2026-10-06T05:00:00Z" });
  assert.equal(collectionLabels.error, "Last attempt failed");
  assert.equal(collectionLabels.stale, "Fetch overdue");
  assert.equal(collectionLabels.not_attempted, "Never checked");
});

test("missing or malformed successful-fetch timestamps never render a valid update", () => {
  assert.equal(fetchTime(null), "Unavailable");
  assert.equal(fetchTime("invalid"), "Unavailable");
  assert.equal(newsFreshness([{ enabled: true, status: "not_attempted", last_success_at: null }]).lastSuccess, null);
  assert.equal(newsFreshness([{ enabled: true, status: "error", last_success_at: "invalid" }]).healthy, 0);
  assert.notEqual(fetchTime("2026-10-06T05:00:00Z"), "Unavailable");
});
