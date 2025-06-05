import csv
import json
import requests
from pse.api import FND_CMPY_URL

def get_cmpy_id(cmpy_symbol: str) -> str:
    try:
        response = requests.get(FND_CMPY_URL, params={"term": cmpy_symbol}, timeout=5)
        response.raise_for_status()
        data = response.json()
        return "" if not data else str(data[0]["cmpyId"])
    except requests.RequestException:
        return "" 

def main():
    with open("../data/listed_company_directory.csv", mode='r', encoding='utf-8') as company_file:
        cmpy_list = list(csv.reader(company_file))[1:]  

    result = {}
    for cmpy in cmpy_list:
        symbol = cmpy[1].strip()
        cmpy_id = get_cmpy_id(symbol)
        result[symbol] = cmpy_id
        print(f"Processed {symbol}: {cmpy_id}")

    with open('../data/cmpy.json', 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
