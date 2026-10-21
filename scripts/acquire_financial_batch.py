"""Acquire a bounded batch of private VCI financial packets through vnstock."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.providers.vnstock import sdk
from src.providers.vnstock.financial_packet import fetch_packet
from src.services.financial_batch import acquire_batch


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures', required=True, help='Capture directory under the repository .local directory')
    parser.add_argument('--tickers', nargs='+', required=True)
    parser.add_argument('--refresh', action='store_true', help='Fetch new bounded candidates for existing captures')
    parser.add_argument('--pause-seconds', type=float, default=6.0,
        help='Delay between SDK reads; minimum 6 seconds for the observed guest-tier request cap')
    args = parser.parse_args(argv)
    if args.pause_seconds < 6:
        parser.error('--pause-seconds must be at least 6 for the installed guest-tier limit')
    result = acquire_batch(Path(args.captures), args.tickers,
        fetch_packet=lambda ticker: fetch_packet(ticker, sdk, request_pause_seconds=args.pause_seconds),
        refresh=args.refresh)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if not result['errors'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
