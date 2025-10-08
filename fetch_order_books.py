"""Fetch order book data for NIFTY 50 companies from NSE India.

This script retrieves the list of NIFTY 50 constituents and then downloads
order book (market depth) information for each symbol using NSE's public API.
The collected data is saved as a JSON file for further analysis.

Usage::

    python fetch_order_books.py --output data/nifty50_order_books.json

The script takes care of setting the required headers and cookies that NSE's
website expects, however NSE may occasionally change their defences. In such a
case, updating the headers or adding additional waits might be necessary.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable, List, Dict, Any

import requests

NSE_BASE_URL = "https://www.nseindia.com"
NSE_NIFTY50_CSV_URL = "https://www1.nseindia.com/content/indices/ind_nifty50list.csv"
NSE_QUOTE_ENDPOINT = "https://www.nseindia.com/api/quote-equity"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class NSEClient:
    """Thin wrapper around :class:`requests.Session` tailored for NSE endpoints."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
            }
        )

    def _bootstrap_cookies(self) -> None:
        """Perform an initial request to obtain cookies from NSE."""
        response = self.session.get(
            NSE_BASE_URL,
            timeout=10,
        )
        response.raise_for_status()

    def get_nifty50_symbols(self) -> List[str]:
        """Return the list of NIFTY 50 trading symbols."""
        self._bootstrap_cookies()
        response = self.session.get(
            NSE_NIFTY50_CSV_URL,
            headers={"Referer": NSE_BASE_URL},
            timeout=10,
        )
        response.raise_for_status()

        decoded_content = response.content.decode("utf-8", errors="ignore")
        csv_reader = csv.DictReader(decoded_content.splitlines())
        symbols = [row["Symbol"].strip() for row in csv_reader if row.get("Symbol")]

        if not symbols:
            raise RuntimeError("Failed to parse NIFTY 50 symbols from NSE CSV.")
        return symbols

    def get_order_book(self, symbol: str) -> Dict[str, Any]:
        """Fetch the market depth for the given symbol."""
        params = {"symbol": symbol}
        headers = {
            "Referer": f"{NSE_BASE_URL}/get-quotes/equity?symbol={symbol}",
            "Accept": "application/json, text/plain, */*",
        }
        response = self.session.get(
            NSE_QUOTE_ENDPOINT,
            params=params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        market_depth = data.get("marketDeptOrderBook") or {}
        return {
            "symbol": symbol,
            "timestamp": data.get("metadata", {}).get("lastUpdateTime"),
            "buy": market_depth.get("buy", []),
            "sell": market_depth.get("sell", []),
        }


def fetch_order_books(limit: int | None = None) -> List[Dict[str, Any]]:
    client = NSEClient()
    symbols = client.get_nifty50_symbols()
    if limit is not None:
        symbols = symbols[:limit]

    order_books: List[Dict[str, Any]] = []
    for symbol in symbols:
        try:
            order_book = client.get_order_book(symbol)
        except requests.HTTPError as exc:
            print(f"Failed to fetch {symbol}: {exc}", file=sys.stderr)
            continue
        order_books.append(order_book)
    return order_books


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/nifty50_order_books.json"),
        help="Output JSON file path.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of symbols to fetch (for testing).",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    order_books = fetch_order_books(limit=args.limit)

    if not order_books:
        print("No order book data fetched. Exiting.", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(order_books, f, ensure_ascii=False, indent=2)

    print(f"Saved order book data for {len(order_books)} symbols to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
