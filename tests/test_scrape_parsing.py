# Fixture tests for parse functions in scripts.scrape. 
# Uses static HTML/JSON to verify that the parsing functions 
# These tests do not hit any PSE endpoints.

import json
import pytest
from pse.exceptions import CompanyNotFoundError
from scripts.scrape import (
    _parse_cmpy_info,
    _parse_stock_data,
    _parse_stock_chart,
    _parse_stock_dividends,
    _parse_dividends_page,
    lookup_cmpy,
)

FIXTURES = "tests/fixtures"

def read(filename):
    with open(f"{FIXTURES}/{filename}", "r", encoding="utf-8") as f:
        return f.read()

def test_parse_cmpy_info():
    html = read("cmpy_info_sample.html")
    result = _parse_cmpy_info(html)

    assert result.sector == "Property"
    assert result.subSector == "Property"
    assert result.website == "www.areit.com.ph"
    assert result.overview.startswith("AREIT, Inc. (AREIT) was incorporated on September 4, 2006")
    assert "Source: SEC Form 17-A (2024)" in result.overview

def test_parse_stock_data():
    html = read("stock_data_sample.html")
    result = _parse_stock_data(html)

    assert result.cmpyName == "AREIT, Inc."
    assert result.date == "2026-08-07"
    assert result.time == "14:50:00"
    assert result.lastTradedPrice == 37.75
    assert result.open == 37.50
    assert result.previousClose == 37.35
    assert result.previousCloseDate == "2026-08-06"
    assert result.change == 0.40
    assert result.percentChange == 1.06
    assert result.high == 37.75
    assert result.value == 17887475.00
    assert result.low == 37.25
    assert result.volume == 476300
    assert result.averagePrice == 37.56
    assert result.week52High == 45.50
    assert result.week52Low == 36.10


def test_parse_stock_chart():
    data = json.loads(read("stock_chart_sample.json"))
    result = _parse_stock_chart(data)

    assert len(result) == 24
    assert result[0]["CHART_DATE"] == "Jul 01, 2026 00:00:00"
    assert result[0]["OPEN"] == 37.35
    assert result[-1]["CHART_DATE"] == "Jul 31, 2026 00:00:00"
    assert result[-1]["CLOSE"] == 38.0


def test_parse_stock_chart_missing_key_returns_empty():
    assert _parse_stock_chart({}) == []


# ---------------------------------------------------------------------------
# _parse_stock_dividends
# ---------------------------------------------------------------------------

def test_parse_stock_dividends():
    html = read("stock_dividends_sample.html")
    result = _parse_stock_dividends(html)

    assert len(result) == 4

    first = result[0]
    assert first.securityType == "COMMON"
    assert first.dividendType == "Cash"
    assert first.dividendRate == 0.62
    assert first.exDividendDate == "2026-05-26"
    assert first.recordDate == "2026-05-28"
    assert first.paymentDate == "2026-06-11"

    last = result[-1]
    assert last.dividendRate == 0.59
    assert last.exDividendDate == "2025-08-28"
    assert last.paymentDate == "2025-09-12"


# ---------------------------------------------------------------------------
# _parse_dividends_page
# ---------------------------------------------------------------------------

def test_parse_dividends_page_current_year_only():
    html = read("dividends_page_sample.html")
    results, stop_pagination = _parse_dividends_page(html, current_year=2026)

    # 50 rows total: 2 dated 2027 (skipped as future), 48 dated 2026 (kept),
    # none dated 2025 on this page, so pagination doesn't stop.
    assert len(results) == 48
    assert stop_pagination is False

    first = results[0]
    assert first.companyName == "Asia United Bank Corporation"
    assert first.dividendRate == 0.50
    assert first.exDividendDate == "2026-12-01"

    last = results[-1]
    assert last.companyName == "MREIT, Inc."
    assert last.dividendRate == 0.263
    assert last.exDividendDate == "2026-08-13"


def test_parse_dividends_page_future_year_stops_immediately():
    html = read("dividends_page_sample.html")
    results, stop_pagination = _parse_dividends_page(html, current_year=2025)

    # First row on the page is 2027 (skipped as future), second row is also
    # 2027 (skipped), third row is 2026 — greater than current_year=2025,
    # so nothing here is < current_year either; every row on this page is
    # either future or equal-or-greater, meaning current_year=2025 never
    # matches "year == current_year", so results should be empty and
    # pagination never triggers a stop within this page.
    assert results == []
    assert stop_pagination is False


# ---------------------------------------------------------------------------
# lookup_cmpy
# ---------------------------------------------------------------------------

def test_lookup_cmpy_unknown_symbol_raises():
    with pytest.raises(CompanyNotFoundError):
        lookup_cmpy("NOT_A_REAL_TICKER")