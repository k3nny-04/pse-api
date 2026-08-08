from dataclasses import dataclass

@dataclass
class CompanyData:
    overview: str = ""
    sector: str = ""
    subSector: str = ""
    website: str = ""