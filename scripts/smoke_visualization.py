"""Opt-in API + live provider smoke. Starts no server. Never run as part of pytest."""
import argparse
import json
import math
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("symbols", nargs="+")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    def request(path, body=None):
        payload = json.dumps(body).encode() if body is not None else None
        req = Request(args.base_url.rstrip("/") + path, data=payload,
                      headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=120) as response:
            return json.load(response)

    for value in args.symbols:
        symbol = value.strip().upper()
        stock = request("/stocks", {"ticker": symbol})
        overview = request(f"/stocks/{symbol}/overview")
        technical = request(f"/stocks/{symbol}/technical-history")
        annual = request(f"/stocks/{symbol}/fundamentals/history")
        assert technical, f"{symbol}: no OHLCV observations"
        assert [row["date"] for row in technical] == sorted({row["date"] for row in technical})
        assert technical[-1]["date"] == overview["market"]["as_of"]
        for field in ("ma20", "ma50", "rsi14"):
            actual, expected = technical[-1][field], overview["market"][field]
            assert actual is not None and expected is not None
            assert math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-8), (symbol, field, actual, expected)
        assert annual and [row["period"] for row in annual] == sorted({row["period"] for row in annual})
        for field in ("revenue", "net_profit", "gross_margin", "net_margin", "roe", "revenue_growth_yoy", "net_profit_growth_yoy"):
            assert annual[-1][field] == overview["fundamentals"][field], (symbol, field)
        # Verify omission propagation without assuming a ticker-specific accounting model.
        for row in annual:
            if row["revenue"] is None:
                assert row["gross_margin"] is None and row["net_margin"] is None
            if row["roe"] is None:
                assert row["roe_change"] is None
        print(json.dumps({"ticker": stock["symbol"], "sessions": len(technical), "as_of": technical[-1]["date"],
                          "periods": [row["period"] for row in annual], "missing_latest": [key for key in ("revenue","gross_margin","net_margin","roe") if annual[-1][key] is None],
                          "latest_matches_snapshot": True, "status": "PASS"}))


if __name__ == "__main__":
    main()
