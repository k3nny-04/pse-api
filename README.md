# PSE Scraper API

A lightweight FastAPI service that scrapes the Philippine Stock Exchange's public edge endpoints and serves clean, structured JSON — stock snapshots, daily OHLCV charts, dividend history, and company info — for your own apps to consume, without hitting PSE's unofficial site directly from each one.

The branch `local-deploy` is the **no-auth, run-it-yourself** version: no API key required, no Docker needed. Point it at your machine, hit `localhost`, done.

> Built against `edge.pse.com.ph`'s unofficial, undocumented API. Not affiliated with or endorsed by the Philippine Stock Exchange. Use responsibly.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Endpoints](#endpoints)
  - [GET /company-info/{symbol}](#get-company-infosymbol)
  - [GET /stock-data/{symbol}](#get-stock-datasymbol)
  - [GET /chart/{symbol}](#get-chartsymbolstart_datemm-dd-yyyyend_datemm-dd-yyyy)
  - [GET /dividends/{symbol}](#get-dividendssymbol)
  - [GET /dividends](#get-dividends)
- [Error Responses](#error-responses)
- [Repo Structure](#repo-structure)
- [Reliability, Measured](#reliability-measured)
- [Notes](#notes)

---

## Quick start

```bash
# 1. Clone the repo and switch to this branch
git clone https://github.com/<your-username>/pse-api.git
cd pse-api
git checkout local-deploy

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run it
uvicorn main:app --reload
```

The API is now live at `http://127.0.0.1:8000`. Interactive docs (Swagger UI) are auto-generated at `http://127.0.0.1:8000/docs` — a good place to poke around before wiring up a real client.

---

## Endpoints

All routes are ticker-symbol-based — pass a PSE symbol like `AREIT`, `SM`, `JFC`; the service resolves it to PSE's internal IDs for you.

### `GET /company-info/{symbol}`
Company profile — overview, sector, sub-sector, website.

```bash
curl http://127.0.0.1:8000/company-info/AREIT
```

### `GET /stock-data/{symbol}`
Current snapshot — last traded price, open/high/low, previous close, change, volume, 52-week range, and trading status (Open / Suspended / Halted).

```bash
curl http://127.0.0.1:8000/stock-data/AREIT
```

### `GET /chart/{symbol}?start_date=MM-DD-YYYY&end_date=MM-DD-YYYY`
Daily OHLCV bars for a date range — one row per trading day (open, high, low, close, value).

| Param | Format | Required |
|---|---|---|
| `start_date` | `MM-DD-YYYY` | yes |
| `end_date` | `MM-DD-YYYY` | yes |

```bash
curl "http://127.0.0.1:8000/chart/AREIT?start_date=07-01-2026&end_date=08-01-2026"
```

`end_date` must not fall before `start_date` — the API rejects that with a `422`.

### `GET /dividends/{symbol}`
Dividend history for one company — type, rate, ex-dividend/record/payment dates.

```bash
curl http://127.0.0.1:8000/dividends/AREIT
```

### `GET /dividends`
Dividend announcements across **all** listed companies for the current year, paginated internally. Slower than the other endpoints since it walks multiple PSE pages per call.

```bash
curl http://127.0.0.1:8000/dividends
```

---

## Error responses

Every failure returns a JSON body with a `detail` message and an HTTP status that reflects what went wrong:

| Status | Meaning |
|---|---|
| `404` | Ticker symbol not recognized |
| `422` | Bad request — invalid date format, or `end_date` before `start_date` |
| `502` | PSE unreachable, or returned something the parser couldn't handle |

---

## Repo structure

```
pse-api/
├── main.py                  # FastAPI app — routes, error → status mapping
├── requirements.txt
├── data/
│   ├── cmpy.json             # symbol → PSE company/security ID lookup table
│   └── listed_company_directory.csv
├── models/
│   ├── company.py            # CompanyData
│   ├── stock.py               # StockData + field label mapping
│   ├── chart.py                # ChartData
│   └── dividends.py           # DividendData
├── pse/
│   ├── api.py                  # PSE endpoint URL constants
│   └── exceptions.py           # PSEError hierarchy (maps to HTTP status codes)
├── scripts/
│   ├── scrape.py                # fetch + parse logic for all 5 scrapers
│   ├── utils.py                  # safe parsing helpers (blank fields, TBA dates, etc.)
│   └── fetch_cmpys.py             # one-off script that built data/cmpy.json
└── tests/
    ├── fixtures/                  # committed HTML/JSON snapshots
    ├── test_scrape_parsing.py     # fixture-based regression tests (fast, offline)
    ├── test_api.py                # FastAPI TestClient + mocked scrapers
    ├── test_live_contract.py      # hits real PSE, shape-only assertions (manual)
    └── api_sweep.py                # load-tests every company against a running API
```

---

## Reliability, measured

A full sweep across every listed company (`api_sweep.py`), hitting all 4 per-symbol endpoints back-to-back with no delay and no caching, came back clean:

- **284 companies swept, 1,136 total calls, 100% success rate — zero failures.**
- **Median response time stayed under ~350ms** across every endpoint, even under continuous load.
- Overall average: **~358ms per call**, ~406 seconds total for the full sweep.

| Endpoint | Median | Success rate |
|---|---|---|
| `company-info` | 292ms | 100% |
| `stock-data` | 295ms | 100% |
| `chart` | 349ms | 100% |
| `dividends` | 281ms | 100% |

No caching or rate limiting is in place yet on this branch — every call hits PSE fresh. That's intentional for now; both are planned for a future version.

---

## Notes

- Daily chart data only — PSE's public endpoint returns one OHLCV bar per trading day, not intraday/tick-level data.
- Non-trading days and delisted/suspended companies may return partial or empty fields rather than an error; `status` on `/stock-data` tells you when a company isn't actively trading.
- This scrapes an unofficial API with no published rate limit or SLA — be a reasonable neighbor.