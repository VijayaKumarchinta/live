from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

def envelope(data: Any, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {"data": data}
    if meta is not None:
        out["meta"] = meta
    return out

def error(message: str, status: int = 400) -> tuple:
    return {"error": message}, status

def parse_ts(value: Optional[str], default: datetime) -> datetime:
    if not value:
        return default
    # Try ISO 8601 first
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        # Fall back to RFC 2822 (e.g., "Fri, 17 Apr 2026 06:39:53 GMT")
        try:
            dt = parsedate_to_datetime(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid timestamp: {value}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def parse_int(value: Optional[str], default: Optional[int] = None) -> Optional[int]:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"invalid integer: {value}") from exc

def parse_sensor_ids(value: Optional[str]) -> Optional[List[int]]:
    if not value:
        return None
    try:
        return [int(x) for x in value.split(",") if x.strip()]
    except ValueError as exc:
        raise ValueError(f"invalid sensor_ids: {value}") from exc