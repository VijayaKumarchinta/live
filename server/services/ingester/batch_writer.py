import json
import logging
from datetime import datetime
from typing import Dict, List
from sqlalchemy import text
from app.db.engine import writer_engine

logger = logging.getLogger(__name__)

BATCH_SIZE = 500
SOURCE_LIVE = 2
NOTIFY_CHANNEL = "telemetry_live"

def load_sensor_map(line_id: int) -> Dict[str, int]:
    with writer_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT tag, sensor_id FROM config.sensor WHERE line_id = :line_id"),
            {"line_id": line_id},
        ).all()
    return {row.tag: row.sensor_id for row in rows}

def load_cursor(line_id: int) -> int:
    with writer_engine.connect() as conn:
        row = conn.execute(
            text("SELECT last_processed_sequence FROM audit.ingest_cursor WHERE line_id = :line_id"),
            {"line_id": line_id},
        ).first()
    return int(row.last_processed_sequence) if row else 0

def insert_batch(line_id: int, rows: List[dict], last_sequence: int, last_message_id: str, last_ts: datetime) -> int:
    if not rows:
        return 0
    inserted = 0
    stmt = text(
        "INSERT INTO telemetry.measurement (line_id, sensor_id, ts, value, quality, source) "
        "VALUES (:line_id, :sensor_id, :ts, :value, :quality, :source) "
        "ON CONFLICT (line_id, sensor_id, ts) DO NOTHING"
    )
    cursor_stmt = text(
        "INSERT INTO audit.ingest_cursor (line_id, last_processed_sequence, last_processed_message_id, last_processed_ts, updated_at) "
        "VALUES (:line_id, :seq, :mid, :ts, NOW()) "
        "ON CONFLICT (line_id) DO UPDATE SET "
        "last_processed_sequence = EXCLUDED.last_processed_sequence, "
        "last_processed_message_id = EXCLUDED.last_processed_message_id, "
        "last_processed_ts = EXCLUDED.last_processed_ts, updated_at = NOW()"
    )
    with writer_engine.begin() as conn:
        for start in range(0, len(rows), BATCH_SIZE):
            chunk = rows[start:start + BATCH_SIZE]
            result = conn.execute(stmt, chunk)
            inserted += result.rowcount or 0
        conn.execute(
            cursor_stmt,
            {"line_id": line_id, "seq": last_sequence, "mid": last_message_id, "ts": last_ts},
        )
        payload = json.dumps(
            {
                "line_id": line_id,
                "last_seq": last_sequence,
                "inserted": inserted,
                "ts": last_ts.isoformat() if last_ts is not None else None,
            },
            default=str,
        )
        conn.execute(
            text("SELECT pg_notify(:channel, :payload)"),
            {"channel": NOTIFY_CHANNEL, "payload": payload},
        )
    return inserted