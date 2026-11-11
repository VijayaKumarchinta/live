from typing import List, Dict, Any
from sqlalchemy import text
from app.db.engine import reader_engine

def list_lines() -> List[Dict[str, Any]]:
    sql = text(
        "SELECT line_id, name, site, timezone, created_at "
        "FROM config.line ORDER BY line_id"
    )
    with reader_engine.connect() as conn:
        return [dict(r) for r in conn.execute(sql).mappings().all()]

def list_sensors(line_id: int) -> List[Dict[str, Any]]:
    sql = text(
        "SELECT sensor_id, line_id, tag, display_name, unit, zero_is_missing, created_at "
        "FROM config.sensor WHERE line_id = :line_id ORDER BY sensor_id"
    )
    with reader_engine.connect() as conn:
        return [dict(r) for r in conn.execute(sql, {"line_id": line_id}).mappings().all()]