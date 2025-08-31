import csv
import re
import json
import requests
from pse.api import FND_CMPY_URL, STOCK_DATA_URL
from bs4 import BeautifulSoup

def get_cmpy_data(cmpy_symbol: str) -> str:
    try:
        response = requests.get(FND_CMPY_URL, params={"term": cmpy_symbol}, timeout=5)
        response.raise_for_status()
        data = response.json()
        return None if not data else data[0]
    except requests.RequestException:
        return None
    
def get_security_id(cmpy_id: str) -> str:
    response = requests.get(STOCK_DATA_URL, params={"cmpy_id": cmpy_id},  timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    script_tags = soup.find_all("script", type="text/javascript")

    if not script_tags or len(script_tags) < 2:
        return ""
    
    parsed_script = script_tags[1].string
    if parsed_script and "getDiscData" in parsed_script:
        match = re.search(r'sendData\.security_id\s*=\s*"(\d+)"', parsed_script)
        if match:
            return match.group(1)

    return ""

def populate_cmpy_data():
    with open("data/listed_company_directory.csv", mode='r', encoding='utf-8') as company_file:
        cmpy_list = list(csv.reader(company_file))[1:]  

    result = {}
    for cmpy in cmpy_list:
        symbol = cmpy[1].strip()
        cmpy_data = get_cmpy_data(symbol)
        result[symbol] = cmpy_data
        print(f"Processed {symbol}: {cmpy_data["cmpyId"] if cmpy_data else "Not Found"}")

    with open('data/cmpy.json', 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, indent=4, ensure_ascii=False)

def populate_security_ids():
    with open('data/cmpy.json', 'r', encoding='utf-8') as json_file:
        cmpy_data = json.load(json_file)

    for symbol, data in cmpy_data.items():
        if data:
            cmpy_id = data.get("cmpyId")
            security_id = get_security_id(cmpy_id)
            data["security_id"] = security_id
            print(f"Updated {symbol}: security_id={security_id}")

    with open('data/cmpy.json', 'w', encoding='utf-8') as json_file:
        json.dump(cmpy_data, json_file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    populate_cmpy_data()
    populate_security_ids()

