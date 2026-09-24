import test from "node:test";
import assert from "node:assert/strict";
import { annualChartData, availableSeries, FINANCIAL_LABELS, compactVnd } from "../lib/fundamental-data.ts";

test("annual adapter sorts real years without interpolation or mutation", () => {
  const rows=[{period:"2025",revenue:null,roe:null},{period:"2023",revenue:0,roe:null},{period:"2024-Q1",revenue:50,roe:null}];
  const result=annualChartData(rows);
  assert.deepEqual(result.map(r=>r.period),["2023","2025"]);
  assert.equal(result[1].revenue,null);
  assert.equal(result[0].revenue,0);
  assert.equal(rows[0].period,"2025");
  assert.deepEqual(availableSeries(result,["revenue","roe"]),["revenue"]);
});
test("financial labels and formatting are English and missing stays distinct from zero", () => {
  assert.equal(FINANCIAL_LABELS.net_profit,"Net Profit");
  assert.equal(FINANCIAL_LABELS.revenue_growth_yoy,"Revenue YoY");
  assert.equal(compactVnd(null),"—");
  assert.equal(compactVnd(0),"0");
  assert.equal(compactVnd(1200000000000),"1.2T");
});
