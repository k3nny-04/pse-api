# Live contract tests for scrape functions in scripts.scrape.
# Check that the shape of the returned data is correct. 
# These tests hit PSE endpoints.

from datetime import datetime
from scripts.scrape import (
    scrape_cmpy_info,
    scrape_stock_data,
    scrape_stock_chart,
    scrape_stock_dividends,
    _fetch_dividends_page,
    _parse_dividends_page,
)

# AREIT 
CMPY_ID = "679"
SECURITY_ID = "655"


def test_scrape_cmpy_info_shape():
    result = scrape_cmpy_info(CMPY_ID)

    assert result.overview.strip() != ""
    assert result.sector.strip() != ""
    assert result.subSector.strip() != ""
    # Website can be blank


def test_scrape_stock_data_shape():
    result = scrape_stock_data(CMPY_ID)

    assert result.cmpyName.strip() != ""
    assert result.lastTradedPrice > 0
    assert result.open > 0
    assert result.high >= result.low
    assert result.high >= result.lastTradedPrice or result.lastTradedPrice >= result.low
    assert result.volume >= 0
    assert result.value >= 0
    datetime.strptime(result.date, "%Y-%m-%d")  
    datetime.strptime(result.time, "%H:%M:%S")


def test_scrape_stock_chart_shape():
    result = scrape_stock_chart(CMPY_ID, SECURITY_ID, "07-01-2026", "08-01-2026")

    assert isinstance(result, list)
    assert len(result) > 0

    for entry in result:
        for key in ("OPEN", "CLOSE", "HIGH", "LOW", "VALUE", "CHART_DATE"):
            assert key in entry
        datetime.strptime(entry["CHART_DATE"], "%b %d, %Y %H:%M:%S")


def test_scrape_stock_dividends_shape():
    result = scrape_stock_dividends(CMPY_ID)

    assert isinstance(result, list)
    assert len(result) > 0

    for d in result:
        assert d.securityType.strip() != ""
        assert d.dividendType.strip() != ""
        assert d.dividendRate >= 0
        datetime.strptime(d.exDividendDate, "%Y-%m-%d")
        datetime.strptime(d.recordDate, "%Y-%m-%d")
        datetime.strptime(d.paymentDate, "%Y-%m-%d")


def test_dividends_page_shape():
    # Single page only 
    html = _fetch_dividends_page(1)
    results, _ = _parse_dividends_page(html, current_year=datetime.now().year)

    assert isinstance(results, list)

    for d in results:
        assert d.companyName.strip() != ""
        assert d.dividendRate >= 0
        datetime.strptime(d.exDividendDate, "%Y-%m-%d")