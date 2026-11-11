from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import text

from app.db.engine import reader_engine


def latest(line_id: int, source: int = 2) -> List[Dict[str, Any]]:
    sql = text(
        "SELECT DISTINCT ON (m.sensor_id) "
        "  m.sensor_id, s.tag, s.display_name, s.unit, m.ts, m.value, m.quality "
        "FROM telemetry.measurement m "
        "JOIN config.sensor s ON s.sensor_id = m.sensor_id "
        "WHERE m.line_id = :line_id AND m.source = :source "
        "ORDER BY m.sensor_id, m.ts DESC"
    )
    with reader_engine.connect() as conn:
        return [dict(r) for r in conn.execute(sql, {"line_id": line_id, "source": source}).mappings().all()]


def range_rows(
    line_id: int,
    sensor_ids: Optional[List[int]],
    ts_from: datetime,
    ts_to: datetime,
    limit: int,
    source: int = 2,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {
        "line_id": line_id,
        "ts_from": ts_from,
        "ts_to": ts_to,
        "limit": limit,
        "source": source,
    }
    where = [
        "line_id = :line_id",
        "source = :source",
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
    source: int = 2,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"line_id": line_id, "sensor_id": sensor_id, "source": source}
    where = ["line_id = :line_id", "sensor_id = :sensor_id", "source = :source"]
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
    source: int = 2,
) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {
        "line_id": line_id,
        "limit": limit,
        "offset": offset,
        "source": source,
    }
    where = ["line_id = :line_id", "source = :source"]
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
    by_sensor_sql = text(
        "SELECT source, sensor_id, "
        "       min(value) AS min, max(value) AS max, avg(value) AS avg "
        "FROM telemetry.measurement "
        "WHERE line_id = :line_id "
        "GROUP BY source, sensor_id "
        "ORDER BY source, sensor_id"
    )
    with reader_engine.connect() as conn:
        row = conn.execute(sql, {"line_id": line_id}).mappings().first()
        sources = {int(r["source"]): int(r["n"]) for r in conn.execute(src_sql, {"line_id": line_id}).mappings().all()}
        by_sensor = [dict(r) for r in conn.execute(by_sensor_sql, {"line_id": line_id}).mappings().all()]
    out = dict(row) if row else {"rows": 0, "sensors": 0, "min_ts": None, "max_ts": None}
    out["sources"] = sources
    out["sensors_by_id"] = by_sensor
    return out
def hourly_summary(line_id: int, source: int = 2) -> List[Dict[str, Any]]:
    sql = text(
        "SELECT "
        "  date_trunc('hour', ts) AS hour_bucket, "
        "  count(DISTINCT ts) AS n_samples, "
        "  min(ts) AS first_ts, "
        "  max(ts) AS last_ts, "
        "  avg(value) FILTER (WHERE sensor_id = 32) AS delta_t_avg, "
        "  avg(value) FILTER (WHERE sensor_id = 12) AS oil_temp_avg, "
        "  avg(value) FILTER (WHERE sensor_id = 1)  AS burner_avg, "
        "  avg(value) FILTER (WHERE sensor_id = 25) AS moisture_avg, "
        "  min(value) FILTER (WHERE sensor_id = 25) AS moisture_min, "
        "  max(value) FILTER (WHERE sensor_id = 25) AS moisture_max, "
        "  count(*) FILTER (WHERE sensor_id = 25 AND (value < 1.10 OR value > 1.30)) AS out_of_band, "
        "  count(*) FILTER (WHERE sensor_id = 1 AND value >= 99.9) AS burner_at_100 "
        "FROM telemetry.measurement "
        "WHERE line_id = :line_id AND source = :source "
        "GROUP BY hour_bucket "
        "ORDER BY hour_bucket"
    )
    with reader_engine.connect() as conn:
        return [dict(r) for r in conn.execute(sql, {"line_id": line_id, "source": source}).mappings().all()]
def history_pivot(line_id: int, limit: int = 12, source: int = 2) -> List[Dict[str, Any]]:
    sql = text(
        "WITH latest_ts AS ("
        "  SELECT DISTINCT ts FROM telemetry.measurement "
        "  WHERE line_id = :line_id AND source = :source "
        "  ORDER BY ts DESC LIMIT :limit"
        ") "
        "SELECT m.ts, m.sensor_id, m.value "
        "FROM telemetry.measurement m "
        "JOIN latest_ts ON latest_ts.ts = m.ts "
        "WHERE m.line_id = :line_id AND m.source = :source "
        "ORDER BY m.ts DESC, m.sensor_id"
    )
    with reader_engine.connect() as conn:
        rows = [dict(r) for r in conn.execute(sql, {"line_id": line_id, "source": source, "limit": limit}).mappings().all()]
    by_ts: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        k = r["ts"].isoformat()
        by_ts.setdefault(k, {"ts": r["ts"], "sensors": {}})
        by_ts[k]["sensors"][r["sensor_id"]] = r["value"]
    return list(by_ts.values())