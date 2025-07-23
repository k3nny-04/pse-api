from dataclasses import dataclass

@dataclass
class DividendData:
    companyName: str
    securityType: str
    dividendType: str
    dividendRate: float
    exDividendDate: str
    recordDate: str
    paymentDate: str