from dataclasses import dataclass

@dataclass
class ChartData:
    open: float = 0.0
    value: float = 0.0
    close: float = 0.0
    chartDate: str = ""
    high: float = 0.0
    low: float = 0.0

