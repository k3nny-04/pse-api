from dataclasses import dataclass
from typing import Optional

label_map = {
    "Last Traded Price": "lastTradedPrice",
    "Open": "open",
    "Previous Close and Date": ("previousClose", "previousCloseDate"),
    "Change(% Change)": ("change", "percentChange"),
    "High": "high",
    "Value": "value",
    "Low": "low",
    "Volume": "volume",
    "Average Price": "averagePrice",
    "52-Week High": "week52High",
    "52-Week Low": "week52Low"
}

float_args = ["lastTradedPrice", "open", "previousClose", "change", "percentChange", "high", "value", "low", "averagePrice", "week52High", "week52Low"]

@dataclass
class StockData:
    cmpyName: str
    date: str
    time: str
    lastTradedPrice: float
    open: float
    previousClose: float
    previousCloseDate: str
    change: float
    percentChange: float
    high: float
    value: float
    low: float
    volume: int
    averagePrice: float
    week52High: float
    week52Low: float
