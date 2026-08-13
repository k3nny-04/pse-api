from datetime import datetime
import re

def safe_float(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def safe_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

def safe_parse_date(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw or raw.upper() == "TBA":
        return ""
    try:
        return datetime.strptime(raw, "%b %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        return ""

def extract_dividend_rate(raw: str) -> float:
    if not raw:
        return 0.0
    per_share = re.search(r"([\d,]+\.?\d*)\s*(?:per\s*share|/\s*share)", raw, re.IGNORECASE)
    if per_share:
        return float(per_share.group(1).replace(",", ""))
    generic = re.search(r"[\d,.]+", raw)
    return float(generic.group().replace(",", "")) if generic else 0.0