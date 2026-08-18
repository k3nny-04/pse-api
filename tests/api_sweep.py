"""
api_sweep.py — manual, occasional. NOT part of the pytest suite.

Hits main.py's actual HTTP endpoints (not the scrape functions directly)
against every entry in data/cmpy.json, logging outcomes to CSV, then
prints summary statistics. Exercises the full stack: FastAPI routing,
lookup_cmpy resolution, exception -> status code mapping, and JSON
serialization — not just the underlying scraper.

Requires the API server running first:
    uvicorn main:app

Then in a separate terminal:
    python api_sweep.py                                    # full sweep, all entries
    python api_sweep.py --limit 20                         # cheap dry run
    python api_sweep.py --base-url http://127.0.0.1:8000
    python api_sweep.py --api-key your-secret-key           # send x-api-key header
"""

import argparse
import csv
import json
import statistics
import time
from collections import defaultdict
from datetime import datetime
import requests

OUTPUT_CSV = "api_sweep_results.csv"

FIELDNAMES = [
    "timestamp",
    "symbol",
    "endpoint",
    "http_status",
    "elapsed_ms",
    "detail",
]

ENDPOINTS = ("company-info", "stock-data", "chart", "dividends")


def call_endpoint(base_url, symbol, endpoint, headers, params=None):
    url = f"{base_url}/{endpoint}/{symbol}"
    start = time.monotonic()
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        detail = summarize(endpoint, response)
        return response.status_code, elapsed_ms, detail
    except requests.RequestException as e:
        elapsed_ms = round((time.monotonic() - start) * 1000, 1)
        return None, elapsed_ms, str(e)[:200]


def summarize(endpoint, response) -> str:
    if response.status_code != 200:
        try:
            return str(response.json().get("detail", ""))[:200]
        except Exception:
            return response.text[:200]

    try:
        body = response.json()
    except Exception:
        return "non-JSON response"

    if endpoint == "company-info":
        return f"sector={body.get('sector')!r}"
    if endpoint == "stock-data":
        return f"cmpyName={body.get('cmpyName')!r} lastTradedPrice={body.get('lastTradedPrice')}"
    if endpoint == "chart":
        return f"rows={len(body)}"
    if endpoint == "dividends":
        return f"rows={len(body)}"
    return ""


def run_call(writer, rows, base_url, symbol, endpoint, headers, params=None):
    status, elapsed_ms, detail = call_endpoint(base_url, symbol, endpoint, headers, params)

    row = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "endpoint": endpoint,
        "http_status": status,
        "elapsed_ms": elapsed_ms,
        "detail": detail,
    }
    writer.writerow(row)
    rows.append(row)
    print(f"  [{symbol}] {endpoint}: {status} ({elapsed_ms}ms)")


def print_statistics(rows):
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)

    total_companies = len({r["symbol"] for r in rows})
    total_calls = len(rows)
    ok_calls = [r for r in rows if r["http_status"] == 200]
    failed_calls = [r for r in rows if r["http_status"] != 200]

    print(f"Companies swept: {total_companies}")
    print(f"Total calls: {total_calls}")
    print(f"Successful (200): {len(ok_calls)} ({round(len(ok_calls) / total_calls * 100, 1)}%)")
    print(f"Failed (non-200 or no response): {len(failed_calls)} "
          f"({round(len(failed_calls) / total_calls * 100, 1)}%)")

    print("\nPer-endpoint breakdown:")
    for endpoint in ENDPOINTS:
        ep_rows = [r for r in rows if r["endpoint"] == endpoint]
        if not ep_rows:
            continue
        ep_ok = [r for r in ep_rows if r["http_status"] == 200]
        ep_times = [r["elapsed_ms"] for r in ep_rows]

        print(f"\n  {endpoint}:")
        print(f"    calls: {len(ep_rows)}")
        print(f"    success rate: {round(len(ep_ok) / len(ep_rows) * 100, 1)}%")
        print(f"    avg response time: {round(statistics.mean(ep_times), 1)}ms")
        print(f"    median response time: {round(statistics.median(ep_times), 1)}ms")
        print(f"    min / max: {round(min(ep_times), 1)}ms / {round(max(ep_times), 1)}ms")
        if len(ep_times) > 1:
            print(f"    stdev: {round(statistics.stdev(ep_times), 1)}ms")

    if failed_calls:
        print("\nFailure breakdown by HTTP status code:")
        by_status = defaultdict(int)
        for r in failed_calls:
            by_status[r["http_status"]] += 1
        for status, count in sorted(by_status.items(), key=lambda x: (x[0] is None, x[0] or 0)):
            print(f"  {status}: {count}")

    print("\nOverall:")
    all_times = [r["elapsed_ms"] for r in rows]
    print(f"  avg response time (all endpoints): {round(statistics.mean(all_times), 1)}ms")
    print(f"  total elapsed (sum of call times): {round(sum(all_times) / 1000, 1)}s")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="only sweep the first N entries")
    parser.add_argument("--base-url", type=str, default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", type=str, default=None, help="if set, sent as the x-api-key header on every request")
    args = parser.parse_args()

    headers = {"x-api-key": args.api_key} if args.api_key else {}

    with open("../data/cmpy.json", "r", encoding="utf-8") as f:
        cmpy_list = json.load(f)

    items = list(cmpy_list.items())
    if args.limit:
        items = items[: args.limit]

    print(f"Sweeping {len(items)} entries x 4 endpoints against {args.base_url}"
          f" ({'with' if args.api_key else 'without'} x-api-key)")

    today = datetime.now()
    start_date = today.strftime(f"01-01-{today.year}")
    end_date = today.strftime("%m-%d-%Y")

    rows = []
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for symbol, record in items:
            if not record:
                row = {
                    "timestamp": datetime.now().isoformat(),
                    "symbol": symbol,
                    "endpoint": "n/a",
                    "http_status": None,
                    "elapsed_ms": 0,
                    "detail": "cmpy.json entry is null — skipped",
                }
                writer.writerow(row)
                rows.append(row)
                print(f"  [{symbol}] skipped — null record")
                continue

            run_call(writer, rows, args.base_url, symbol, "company-info", headers)
            run_call(writer, rows, args.base_url, symbol, "stock-data", headers)
            run_call(writer, rows, args.base_url, symbol, "chart", headers,
                      params={"start_date": start_date, "end_date": end_date})
            run_call(writer, rows, args.base_url, symbol, "dividends", headers)

    print(f"\nResults written to {OUTPUT_CSV}")
    print_statistics(rows)


if __name__ == "__main__":
    main()