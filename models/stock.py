from dataclasses import dataclass

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
    cmpyName: str = ""
    date: str = ""
    time: str = ""
    lastTradedPrice: float = 0.0
    open: float = 0.0
    previousClose: float = 0.0
    previousCloseDate: str = ""
    change: float = 0.0
    percentChange: float = 0.0
    high: float = 0.0
    value: float = 0.0
    low: float = 0.0
    volume: int = 0
    averagePrice: float = 0.0
    week52High: float = 0.0
    week52Low: float = 0.0

