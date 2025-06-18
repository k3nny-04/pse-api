from bs4 import BeautifulSoup
from datetime import datetime
from models.stock import StockData, label_map, float_args

def scrape_stock_data(html_doc: str) -> StockData:
    stock_args = {}
    soup = BeautifulSoup(html_doc, "html.parser")

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
                date = values[idx][(space_idx+2):-1]
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



with open("stockData.html", mode='r') as file:
    content = file.read()

res = scrape_stock_data(content)
print(res)
