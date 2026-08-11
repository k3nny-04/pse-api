import re
import requests
import json

from bs4 import BeautifulSoup
from datetime import datetime
from models.chart import ChartData
from models.stock import StockData, label_map, float_args
from models.dividends import DividendData
from models.company import CompanyData
from pse.api import *
from pse.exceptions import (
    CompanyNotFoundError,
    PSEBadRequestError,
    PSEUnavailableError,
    PSEParseError,
)

with open("data/cmpy.json", 'r', encoding='utf-8') as json_file:
    cmpy_list = json.load(json_file)

def _request(method, url, **kwargs):
    try:
        response = method(url, timeout=10, **kwargs)
        response.raise_for_status()
        return response
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        if status == 400:
            raise PSEBadRequestError(f"PSE rejected request to {url}: {e}") from e
        raise PSEUnavailableError(f"PSE returned error for {url}: {e}") from e
    except requests.RequestException as e:
        raise PSEUnavailableError(f"Error reaching PSE at {url}: {e}") from e

def lookup_cmpy(ticker_symbol: str, return_entire_object: bool = False):
    if ticker_symbol not in cmpy_list:
        raise CompanyNotFoundError(f"Ticker symbol {ticker_symbol} not found in cmpy_list.")

    if return_entire_object:
        return cmpy_list[ticker_symbol]
    else:
        return cmpy_list[ticker_symbol].get("cmpyId")


# ----------------------------------------------------------------------
# FETCH FUNCTIONS
# ----------------------------------------------------------------------
def _fetch_cmpy_info(cmpy_id: str) -> str:
    response = _request(requests.get, CMPY_INFO_URL, params={"cmpy_id": cmpy_id})
    return response.text

def _fetch_stock_data(cmpy_id: str) -> str:
    response = _request(requests.get, STOCK_DATA_URL, params={"cmpy_id": cmpy_id})
    return response.text

def _fetch_stock_chart(cmpy_id: str, sec_id: str, start_date: str, end_date: str) -> dict:
    if not sec_id:
        raise CompanyNotFoundError(f"No security_id available for cmpy_id {cmpy_id}")

    payload = {
        "cmpy_id": cmpy_id,
        "security_id": sec_id,
        "startDate": start_date,
        "endDate": end_date,
    }

    response = _request(requests.post, STOCK_CHRT_TAB_DATA_URL, json=payload)
    return response.json()

def _fetch_stock_dividends(cmpy_id: str) -> str:
    response = _request(requests.get, STOCK_DIV_URL, params={"cmpy_id": cmpy_id})
    return response.text

def _fetch_dividends_page(page_num: int) -> str:
    payload = {
        "pageNum": page_num,
        "sortMode": "date",
        "dateSortType": "DESC",
        "cmpySortType": "ASC"
    }
    response = _request(requests.post, DIV_LIST_URL, data=payload)
    return response.text


# ----------------------------------------------------------------------
# PARSE FUNCTIONS
# ----------------------------------------------------------------------
def _parse_cmpy_info(html: str) -> CompanyData:
    try:
        soup = BeautifulSoup(html, "html.parser")
        content_div = soup.find("div", id="dataList")

        overview = ""
        sector = ""
        subSector = ""
        website = ""

        tables = content_div.find_all("table", class_="view")
        for table in tables:
            caption = table.find("caption")
            if not caption:
                continue
            cap = caption.get_text(strip=True)

            if "Company Description" in cap:
                td = table.find("td")
                if td:
                    overview = td.get_text(" ", strip=True).replace("\xa0", " ")

            elif "Security Information" in cap:
                trs = table.find_all("tr")
                if trs:
                    sector = trs[0].find("td").get_text(strip=True)
                    subSector = trs[1].find("td").get_text(" ", strip=True).replace("\xa0", " ")

            elif "Contact Information" in cap:
                trs = table.find_all("tr")
                if trs:
                    website = trs[-1].find("td").get_text(" ", strip=True).replace("\xa0", " ")

        return CompanyData(
            overview=overview,
            sector=sector,
            subSector=subSector,
            website=website,
        )
    except Exception as e:
        raise PSEParseError(f"Error parsing company info: {e}") from e

def _parse_stock_data(html: str) -> StockData:
    try:
        soup = BeautifulSoup(html, "html.parser")
        content_div = soup.find("div", id="contents")

        cmpy_name = content_div.find("div", class_="compInfo").p.string
        dt_str = content_div.find("form").span.string[6:]
        dt_formatted = datetime.strptime(dt_str, "%b %d, %Y %I:%M %p")

        stock_args = {
            "cmpyName": cmpy_name,
            "date": str(dt_formatted.date()),
            "time": str(dt_formatted.time()),
        }

        tab_elem = content_div.find_all("table")[1]
        rows = tab_elem.find_all("tr")
        for row in rows:
            labels = [x.string for x in row.find_all("th")]
            values = [x.get_text(strip=True).replace("\xa0", '').replace(',', '') for x in row.find_all("td")]

            for idx, label in enumerate(labels):
                if label not in label_map.keys():
                    continue

                if label == "Previous Close and Date":
                    space_idx = values[idx].find(' ')
                    close = values[idx][:space_idx]
                    par_idx = values[idx].find('(')
                    date = values[idx][(par_idx + 1):-1]
                    date_formatted = datetime.strptime(date, "%b %d %Y")

                    stock_args[label_map[label][0]] = float(close)
                    stock_args[label_map[label][1]] = str(date_formatted.date())
                    continue

                if label == "Change(% Change)":
                    change = stock_args["lastTradedPrice"] - stock_args["previousClose"]
                    percent_change = change / stock_args["previousClose"] * 100

                    stock_args[label_map[label][0]] = round(float(change), 2)
                    stock_args[label_map[label][1]] = round(float(percent_change), 2)
                    continue

                if label == "Volume":
                    values[idx] = int(values[idx])

                if label_map[label] in float_args:
                    values[idx] = float(values[idx])

                stock_args[label_map[label]] = values[idx]

        return StockData(**stock_args)
    except Exception as e:
        raise PSEParseError(f"Error parsing stock data: {e}") from e

def _parse_stock_chart(data: dict) -> list[ChartData]:
    try:
        raw_rows = data.get("chartData", [])
        return [
            ChartData(
                open = row.get("OPEN"),
                value = row.get("VALUE"),
                close = row.get("CLOSE"),
                chartDate = row.get("CHART_DATE", ""),
                high = row.get("HIGH"),
                low = row.get("LOW"),
            )
            for row in raw_rows
        ]
    except Exception as e:
        raise PSEParseError(f"Error parsing stock chart data: {e}") from e

def _parse_stock_dividends(html: str) -> list[DividendData]:
    try:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="list")

        if not table:
            return []

        rows = table.find_all("tr")[1:]
        results = []

        for row in rows:
            cols = [td.get_text(strip=True).replace("\xa0", " ") for td in row.find_all("td")]
            if len(cols) < 6:
                continue

            match = re.search(r"[\d,.]+", cols[2])
            rate = float(match.group().replace(",", "")) if match else 0.0
            ex_div_date = datetime.strptime(cols[3], "%b %d, %Y").strftime("%Y-%m-%d")
            record_date = datetime.strptime(cols[4], "%b %d, %Y").strftime("%Y-%m-%d")
            payment_date = datetime.strptime(cols[5], "%b %d, %Y").strftime("%Y-%m-%d")

            results.append(DividendData(
                companyName="",
                securityType=cols[0],
                dividendType=cols[1],
                dividendRate=rate,
                exDividendDate=ex_div_date,
                recordDate=record_date,
                paymentDate=payment_date,
            ))

        return results
    except Exception as e:
        raise PSEParseError(f"Error parsing stock dividends: {e}") from e

def _parse_dividends_page(html: str, current_year: int) -> tuple[list[DividendData], bool]:
    try:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="list")
        rows = table.find_all("tr")[1:]
    except Exception as e:
        raise PSEParseError(f"Error parsing dividends page: {e}") from e

    results = []
    stop_pagination = False

    for row in rows:
        try:
            cols = [td.get_text(strip=True).replace("\xa0", " ") for td in row.find_all("td")]
            if len(cols) < 7:
                continue

            ex_div_dt = datetime.strptime(cols[4], "%b %d, %Y")
            year = ex_div_dt.year

            if year > current_year:
                continue
            elif year < current_year:
                stop_pagination = True
                break

            match = re.search(r"[\d,.]+", cols[3])
            rate = float(match.group().replace(",", "")) if match else 0.0

            record_date = datetime.strptime(cols[5], "%b %d, %Y").strftime("%Y-%m-%d")
            payment_date = datetime.strptime(cols[6], "%b %d, %Y").strftime("%Y-%m-%d")

            results.append(DividendData(
                companyName=cols[0],
                securityType=cols[1],
                dividendType=cols[2],
                dividendRate=rate,
                exDividendDate=ex_div_dt.strftime("%Y-%m-%d"),
                recordDate=record_date,
                paymentDate=payment_date,
            ))
        except Exception as e:
            print(f"Error parsing row: {e}")
            continue

    return results, stop_pagination


# ----------------------------------------------------------------------
# SCRAPE FUNCTIONS
# ----------------------------------------------------------------------
def scrape_cmpy_info(cmpy_id: str) -> CompanyData:
    html = _fetch_cmpy_info(cmpy_id)
    return _parse_cmpy_info(html)

def scrape_stock_data(cmpy_id: str) -> StockData:
    html = _fetch_stock_data(cmpy_id)
    return _parse_stock_data(html)

def scrape_stock_chart(cmpy_id: str, sec_id: str, start_date: str, end_date: str) -> list[dict]:
    data = _fetch_stock_chart(cmpy_id, sec_id, start_date, end_date)
    return _parse_stock_chart(data)

def scrape_stock_dividends(cmpy_id: str) -> list[DividendData]:
    html = _fetch_stock_dividends(cmpy_id)
    return _parse_stock_dividends(html)

def scrape_dividends() -> list[DividendData]:
    current_year = datetime.now().year
    results = []
    page_num = 1

    while True:
        html = _fetch_dividends_page(page_num)
        page_results, stop_pagination = _parse_dividends_page(html, current_year)
        results.extend(page_results)

        if stop_pagination:
            break

        page_num += 1

    return results


# my_stocks = ["SCC", "DMC", "AREIT", "TEL", "MBT", "RCR"]
# Test for scrape_stock_data function
# for stock in my_stocks:
#     cmpy_id = cmpy_list.get(stock, {}).get("cmpyId")
#     if cmpy_id:
#         stock_data = scrape_stock_data(cmpy_id)
#         print(stock_data)
#     else:
#         print(f"Company ID for {stock} not found in cmpy_list.")

# Test for scrape_stock_dividends function
# for stock in my_stocks:
#     cmpy_id = cmpy_list.get(stock, {}).get("cmpyId")
#     if cmpy_id:
#         dividends = scrape_stock_dividends(cmpy_id)
#         print(f"Dividends for {stock}:")
#         for dividend in dividends:
#             print(dividend)
#     else:
#         print(f"Company ID for {stock} not found in cmpy_list.")

# print(scrape_stock_data("128"))
# cmpy = lookup_cmpy("AREIT", return_entire_object=True)
# cmpy_id = cmpy.get("cmpyId")
# sec_id = cmpy.get("security_id")
# print(scrape_stock_chart(cmpy_id, sec_id, "08-03-2026", "08-07-2026"))
# print(scrape_stock_dividends("114"))

# print(scrape_cmpy_info(lookup_cmpy("AREIT")))