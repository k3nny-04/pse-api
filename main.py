from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from scripts.scrape import (
    lookup_cmpy,
    scrape_cmpy_info,
    scrape_stock_data,
    scrape_stock_chart,
    scrape_stock_dividends,
    scrape_dividends,
)
from pse.exceptions import (
    PSEError,
    CompanyNotFoundError,
    PSEBadRequestError,
    PSEUnavailableError,
    PSEParseError,
)
from models.company import CompanyData
from models.stock import StockData
from models.dividends import DividendData
from models.chart import ChartData

app = FastAPI(title="PSE Scraper API")

STATUS_MAP = {
    CompanyNotFoundError: 404,
    PSEBadRequestError: 422,
    PSEUnavailableError: 502,
    PSEParseError: 502,
}


@app.exception_handler(PSEError)
def pse_error_handler(request, exc: PSEError):
    status_code = STATUS_MAP.get(type(exc), 500)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})

@app.get("/company-info/{symbol}") 
def get_company_info(symbol: str) -> CompanyData:
    cmpy_id = lookup_cmpy(symbol.upper())
    return scrape_cmpy_info(cmpy_id)

@app.get("/stock-data/{symbol}")
def get_stock_data(symbol: str) -> StockData:
    cmpy_id = lookup_cmpy(symbol.upper())
    return scrape_stock_data(cmpy_id)

@app.get("/chart/{symbol}")
def get_chart(
    symbol: str,
    start_date: str = Query(..., description="MM-DD-YYYY"),
    end_date: str = Query(..., description="MM-DD-YYYY"),
) -> list[ChartData]:
    record = lookup_cmpy(symbol.upper(), return_entire_object=True)
    cmpy_id = record.get("cmpyId")
    sec_id = record.get("security_id")

    try:
        start_dt = datetime.strptime(start_date, "%m-%d-%Y")
        end_dt = datetime.strptime(end_date, "%m-%d-%Y")
    except ValueError as e:
        raise PSEBadRequestError(f"Invalid date format, expected MM-DD-YYYY: {e}") from e

    if end_dt < start_dt:
        raise PSEBadRequestError(f"end_date {end_date} is before start_date {start_date}")

    return scrape_stock_chart(cmpy_id, sec_id, start_date, end_date)

@app.get("/dividends/{symbol}")
def get_dividends_for_symbol(symbol: str) -> list[DividendData]:
    cmpy_id = lookup_cmpy(symbol.upper())
    return scrape_stock_dividends(cmpy_id)

@app.get("/dividends")
def get_all_dividends() -> list[DividendData]:
    return scrape_dividends()