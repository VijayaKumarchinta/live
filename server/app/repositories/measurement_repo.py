from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from app.db.engine import reader_engine

def latest(line_id: int) -> List[Dict[str, Any]]:
    sql = text(
        "SELECT DISTINCT ON (m.sensor_id) "
        "  m.sensor_id, s.tag, s.display_name, s.unit, m.ts, m.value, m.quality "
        "FROM telemetry.measurement m "
        "JOIN config.sensor s ON s.sensor_id = m.sensor_id "
        "WHERE m.line_id = :line_id AND m.source = 2 "
        "ORDER BY m.sensor_id, m.ts DESC"
    )
    with reader_engine.connect() as conn:
        return [dict(r) for r in conn.execute(sql, {"line_id": line_id}).mappings().all()]

def range_rows(
    line_id: int,
    sensor_ids: Optional[List[int]],
    ts_from: datetime,
    ts_to: datetime,
    limit: int,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {
        "line_id": line_id,
        "ts_from": ts_from,
        "ts_to": ts_to,
        "limit": limit,
    }
    where = [
        "line_id = :line_id",
        "ts >= :ts_from",
        "ts <= :ts_to",
    ]
    if sensor_ids:
        where.append("sensor_id = ANY(:sensor_ids)")
        params["sensor_ids"] = sensor_ids
    sql = text(
        "SELECT sensor_id, ts, value "
        "FROM telemetry.measurement "
        f"WHERE {' AND '.join(where)} "
        "ORDER BY ts ASC, sensor_id ASC "
        "LIMIT :limit"
    )
    with reader_engine.connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).mappings().all()]

def hourly_profile(
    line_id: int,
    sensor_id: int,
    ts_from: Optional[datetime],
    ts_to: Optional[datetime],
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"line_id": line_id, "sensor_id": sensor_id}
    where = ["line_id = :line_id", "sensor_id = :sensor_id"]
    if ts_from is not None:
        where.append("ts >= :ts_from")
        params["ts_from"] = ts_from
    if ts_to is not None:
        where.append("ts <= :ts_to")
        params["ts_to"] = ts_to
    sql = text(
        "SELECT EXTRACT(HOUR FROM ts AT TIME ZONE 'Asia/Kolkata')::int AS hour, "
        "       avg(value) AS avg, "
        "       min(value) AS min, "
        "       max(value) AS max, "
        "       count(*) AS count "
        "FROM telemetry.measurement "
        f"WHERE {' AND '.join(where)} "
        "GROUP BY hour "
        "ORDER BY hour"
    )
    with reader_engine.connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).mappings().all()]

def history(
    line_id: int,
    limit: int,
    offset: int,
    sensor_id: Optional[int],
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"line_id": line_id, "limit": limit, "offset": offset}
    where = ["line_id = :line_id"]
    if sensor_id is not None:
        where.append("sensor_id = :sensor_id")
        params["sensor_id"] = sensor_id
    sql = text(
        "SELECT sensor_id, ts, value, quality, source "
        "FROM telemetry.measurement "
        f"WHERE {' AND '.join(where)} "
        "ORDER BY ts DESC, sensor_id ASC "
        "LIMIT :limit OFFSET :offset"
    )
    with reader_engine.connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).mappings().all()]

def stats(line_id: int) -> Dict[str, Any]:
    sql = text(
        "SELECT count(*) AS rows, "
        "       count(DISTINCT sensor_id) AS sensors, "
        "       min(ts) AS min_ts, "
        "       max(ts) AS max_ts "
        "FROM telemetry.measurement "
        "WHERE line_id = :line_id"
    )
    src_sql = text(
        "SELECT source, count(*) AS n "
        "FROM telemetry.measurement "
        "WHERE line_id = :line_id "
        "GROUP BY source ORDER BY source"
    )
    with reader_engine.connect() as conn:
        row = conn.execute(sql, {"line_id": line_id}).mappings().first()
        sources = {int(r["source"]): int(r["n"]) for r in conn.execute(src_sql, {"line_id": line_id}).mappings().all()}
    out = dict(row) if row else {"rows": 0, "sensors": 0, "min_ts": None, "max_ts": None}
    out["sources"] = sources
    return out