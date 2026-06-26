import re
import requests
import json

from bs4 import BeautifulSoup
from datetime import datetime
from models.stock import StockData, label_map, float_args
from models.dividends import DividendData
from pse.api import *

with open("data/cmpy.json", 'r', encoding='utf-8') as json_file:
    cmpy_list = json.load(json_file)
cmpy_list_values = cmpy_list.values()


def scrape_stock_data(cmpy_id: str) -> StockData:
    try:
        response = requests.get(STOCK_DATA_URL, params={"cmpy_id": cmpy_id}, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching stock data for cmpy_id {cmpy_id}: {e}")
        return StockData()

    try:
        soup = BeautifulSoup(response.text, "html.parser")
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
                    date = values[idx][(par_idx+1):-1]
                    date_formatted = datetime.strptime(date, "%b %d %Y")

                    stock_args[label_map[label][0]] = float(close)
                    stock_args[label_map[label][1]] = str(date_formatted.date())
                    continue

                if label == "Change(% Change)":
                    change = stock_args["lastTradedPrice"] - stock_args["previousClose"]
                    percent_change = change / stock_args["lastTradedPrice"] * 100

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
        print(f"Error parsing stock data for cmpy_id {cmpy_id}: {e}")
        return StockData()

def scrape_stock_chart(cmpy_id: str, start_date: str, end_date: str) -> list[dict]:
    sec_id = None
    for entry in cmpy_list_values:
        if entry.get("cmpyId") == cmpy_id:
            sec_id = entry.get("security_id")
            break

    payload = {
        "cmpy_id": cmpy_id,        
        "security_id": sec_id,     
        "startDate": start_date,
        "endDate": end_date 
    }

    try:
        response = requests.post(STOCK_CHRT_TAB_DATA_URL, json=payload, timeout=10)
        response.raise_for_status()
        return response.json().get("chartData", [])
    except requests.RequestException as e:
        print(f"Error fetching stock chart data for cmpy_id {cmpy_id}: {e}")
        return []

def scrape_stock_dividends(cmpy_id: str) -> list[DividendData]:
    try:
        response = requests.get(STOCK_DIV_URL, params={"cmpy_id": cmpy_id}, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching stock dividends for cmpy_id {cmpy_id}: {e}")
        return []
    
    try:
        soup = BeautifulSoup(response.text, "html.parser")
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
            
            data = DividendData(
                companyName="",
                securityType=cols[0],
                dividendType=cols[1],
                dividendRate=rate,
                exDividendDate=ex_div_date,
                recordDate=record_date,
                paymentDate=payment_date,
            )
            results.append(data)

        return results
    except Exception as e:
        print(f"Error parsing stock dividends for cmpy_id {cmpy_id}: {e}")
        return []
    
def scrape_dividends() -> list[DividendData]:
    current_year = datetime.now().year
    results = []
    page_num = 1

    try:
        while True:
            payload = {
                "pageNum": page_num,
                "sortMode": "date",
                "dateSortType": "DESC",
                "cmpySortType": "ASC"
            }

            try:
                response = requests.post(DIV_LIST_URL, data=payload, timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error fetching dividend page {page_num}: {e}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", class_="list")
            rows = table.find_all("tr")[1:]  
            
            stop_pagination = False
            for row in rows:
                try:
                    cols = [td.get_text(strip=True).replace("\xa0", " ") for td in row.find_all("td")]
                    if len(cols) < 7:
                        continue

                    # Parse ex-dividend date to decide what to do with the row
                    ex_div_dt = datetime.strptime(cols[4], "%b %d, %Y")
                    year = ex_div_dt.year

                    if year > current_year:
                        # Future dividend (e.g., 2026) — skip but keep scanning
                        continue
                    elif year < current_year:
                        # We’ve reached older data — stop this page and all further pages
                        stop_pagination = True
                        break

                    # Parse dividend rate (extract numeric value)
                    match = re.search(r"[\d,.]+", cols[3])
                    rate = float(match.group().replace(",", "")) if match else 0.0

                    # Convert dates to YYYY-MM-DD
                    record_date = datetime.strptime(cols[5], "%b %d, %Y").strftime("%Y-%m-%d")
                    payment_date = datetime.strptime(cols[6], "%b %d, %Y").strftime("%Y-%m-%d")

                    data = DividendData(
                        companyName=cols[0],
                        securityType=cols[1],
                        dividendType=cols[2],
                        dividendRate=rate,
                        exDividendDate=ex_div_dt.strftime("%Y-%m-%d"),
                        recordDate=record_date,
                        paymentDate=payment_date,
                    )
                    results.append(data)
                except Exception as e:
                    print(f"Error parsing row on page {page_num}: {e}")
                    continue

            if stop_pagination:
                print("Reached dividends outside current year. Stopping.")
                break

            page_num += 1

    except Exception as e:
        print(f"Unexpected error: {e}")

    return results

print(scrape_dividends())