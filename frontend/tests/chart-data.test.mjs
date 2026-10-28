import test from "node:test";
import assert from "node:assert/strict";
import { rangeDates, technicalSeries, RANGES } from "../lib/chart-data.ts";

test("ranges map to real calendar windows, including leap years", () => {
  for (const range of Object.keys(RANGES)) {
    const result = rangeDates(range, new Date("2024-03-01T12:00:00Z"));
    assert.equal((Date.parse(result.end) - Date.parse(result.start)) / 86400000, RANGES[range]);
  }
  assert.equal(rangeDates("3M", new Date("2026-09-23T18:00:00Z")).end, "2026-09-24");
});
test("OHLCV adapter keeps actual data, sorts dates and colors candle direction", () => {
  const rows = [{date:"2025-01-02",open:12,high:13,low:9,close:10,volume:0},
    {date:"2025-01-01",open:10,high:12,low:9,close:12,volume:20}];
  const result = technicalSeries(rows,"up","down");
  assert.equal(result.candles[0].time,"2025-01-01");
  assert.equal(result.candles[1].close,10);
  assert.equal(result.volume[1].value,0);
  assert.equal(result.volume[1].color,"down");
  assert.equal(rows[0].date,"2025-01-02");
});
