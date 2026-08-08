import json
import os
import requests

from pse.api import *

FIXTURE_DIR = "tests/fixtures"
os.makedirs(FIXTURE_DIR, exist_ok=True)

# AREIT
CMPY_ID = "679"
SECURITY_ID = "655"


def save(filename: str, content: str):
    path = os.path.join(FIXTURE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {path} ({len(content)} bytes)")


def capture_cmpy_info():
    resp = requests.get(CMPY_INFO_URL, params={"cmpy_id": CMPY_ID}, timeout=10)
    resp.raise_for_status()
    save("cmpy_info_sample.html", resp.text)


def capture_stock_data():
    resp = requests.get(STOCK_DATA_URL, params={"cmpy_id": CMPY_ID}, timeout=10)
    resp.raise_for_status()
    save("stock_data_sample.html", resp.text)


def capture_stock_chart():
    payload = {
        "cmpy_id": CMPY_ID,
        "security_id": SECURITY_ID,
        "startDate": "07-01-2026",
        "endDate": "08-01-2026",
    }
    resp = requests.post(STOCK_CHRT_TAB_DATA_URL, json=payload, timeout=10)
    resp.raise_for_status()
    save("stock_chart_sample.json", json.dumps(resp.json(), indent=2))


def capture_stock_dividends():
    resp = requests.get(STOCK_DIV_URL, params={"cmpy_id": CMPY_ID}, timeout=10)
    resp.raise_for_status()
    save("stock_dividends_sample.html", resp.text)


def capture_dividends_page():
    payload = {
        "pageNum": 1,
        "sortMode": "date",
        "dateSortType": "DESC",
        "cmpySortType": "ASC",
    }
    resp = requests.post(DIV_LIST_URL, data=payload, timeout=10)
    resp.raise_for_status()
    save("dividends_page_sample.html", resp.text)

if __name__ == "__main__":
    capture_cmpy_info()
    capture_stock_data()
    capture_stock_chart()
    capture_stock_dividends()
    capture_dividends_page()