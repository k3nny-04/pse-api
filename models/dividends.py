from dataclasses import dataclass

@dataclass
class DividendData:
    companyName: str = ""
    securityType: str = ""
    dividendType: str = ""
    dividendRate: float = 0.0
    exDividendDate: str = ""
    recordDate: str = ""
    paymentDate: str = ""