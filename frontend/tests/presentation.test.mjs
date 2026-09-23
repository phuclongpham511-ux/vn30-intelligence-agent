import test from "node:test";
import assert from "node:assert/strict";
import { englishCompanyName, formatNumber, formatPercent, safeExternalUrl } from "../lib/presentation.ts";
test("raw provider names never become English display names", () => {
  for (const company_name of ["CTCP Sá»¯a Viá»‡t Nam", "CTCP Cao su Viet Nam", "Company raw name", "FPT Corporation"]) {
    assert.equal(englishCompanyName({ company_name }), null);
  }
});
test("verified English metadata works for any ticker without a fixed universe", () => {
  assert.equal(englishCompanyName({ company_name: "TÃªn thÃ´", display_name_en: "Example International Corporation" }), "Example International Corporation");
  assert.equal(englishCompanyName({ display_name_en: "  " }), null);
});
test("missing metrics are not shown as zero", () => {
  for (const value of [null, undefined, NaN, Infinity]) assert.equal(formatNumber(value), "â€”");
  assert.equal(formatNumber(0), "0");
  assert.equal(formatPercent(-.0124, true), "-1.24%");
  assert.equal(formatPercent(.0124, true), "+1.24%");
});
test("external links only accept safe web protocols", () => {
  assert.equal(safeExternalUrl("javascript:alert(1)"), null);
  assert.equal(safeExternalUrl(null), null);
  assert.equal(safeExternalUrl("https://example.com/news"), "https://example.com/news");
});
