from datetime import datetime


def parse_date(s: str) -> datetime:
    """Parse ISO-like date or date-time strings to datetime (UTC-naive)."""
    if not s:
        return datetime.min
    s = s.strip().replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.min