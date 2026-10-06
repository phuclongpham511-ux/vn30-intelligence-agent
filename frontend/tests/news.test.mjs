import test from "node:test";
import assert from "node:assert/strict";
import { emptyNewsFilters, newsQuery, readNewsFilters, newsViewQuery, readNewsView } from "../lib/news.ts";

test("news deep links preserve exact filter values without accepting unrelated URL fields", () => {
  const filters = readNewsFilters("?ticker=xyz&sector=Real%20Estate&source=one&country=VN&topic=Rates&user_id=123");
  const query = new URLSearchParams(newsQuery(filters));
  assert.equal(query.get("ticker"), "XYZ");
  assert.equal(query.get("sector"), "Real Estate");
  assert.equal(query.get("user_id"), null);
  assert.deepEqual(readNewsFilters(query.toString()), { ...filters, ticker: "XYZ" });
});

test("news filters encode reserved characters and clearing restores a market-wide view", () => {
  const filters = { ...emptyNewsFilters, topic: "Oil & Trade", ticker: " abc " };
  const query = new URLSearchParams(newsQuery(filters));
  assert.equal(query.get("topic"), "Oil & Trade");
  assert.equal(query.get("ticker"), "ABC");
  assert.equal(query.get("sector"), null);
  assert.equal(newsQuery(emptyNewsFilters), "");
});

test("legacy deep links migrate to semantic categories and remove the technical financial toggle", () => {
  const query = newsViewQuery({ ...emptyNewsFilters, ticker: "xyz" }, "global", false);
  assert.deepEqual(readNewsView(query), { view: "briefing", financialOnly: false });
  assert.equal(readNewsFilters(query).ticker, "XYZ");
  assert.deepEqual(readNewsView("?view=unknown"), { view: "company", financialOnly: false });
  assert.equal(new URLSearchParams(query).has('financial_only'),false);
  assert.equal(readNewsView('?view=latest').view,'company');
});
