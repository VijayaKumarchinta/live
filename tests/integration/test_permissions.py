from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.db.engine import reader_engine, writer_engine


def _scalar(engine, sql: str, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def _execute(engine, sql: str, **params):
    with engine.begin() as conn:
        conn.execute(text(sql), params)


# ---------- Writer role ----------

def test_writer_can_read_config():
    n = _scalar(writer_engine, "SELECT count(*) FROM config.sensor WHERE line_id = 30")
    assert n == 32


def test_writer_can_read_line():
    n = _scalar(writer_engine, "SELECT count(*) FROM config.line WHERE line_id = 30")
    assert n == 1


def test_writer_cannot_insert_into_config():
    with pytest.raises(ProgrammingError):
        _execute(
            writer_engine,
            "INSERT INTO config.sensor VALUES (9999, 30, 'x', 'x', 'x', false, NOW())",
        )


def test_writer_can_insert_and_delete_telemetry():
    ts = "2026-04-15T23:59:59+05:30"
    _execute(
        writer_engine,
        "INSERT INTO telemetry.measurement (line_id, sensor_id, ts, value, quality, source) "
        "VALUES (:line_id, :sensor_id, :ts, :value, :quality, :source) "
        "ON CONFLICT DO NOTHING",
        line_id=30,
        sensor_id=1,
        ts=ts,
        value=0.0,
        quality=0,
        source=1,
    )
    n = _scalar(
        writer_engine,
        "SELECT count(*) FROM telemetry.measurement WHERE line_id = 30 AND sensor_id = 1 AND ts = :ts",
        ts=ts,
    )
    assert n == 1

    _execute(
        writer_engine,
        "DELETE FROM telemetry.measurement WHERE line_id = 30 AND sensor_id = 1 AND ts = :ts",
        ts=ts,
    )
    n = _scalar(
        writer_engine,
        "SELECT count(*) FROM telemetry.measurement WHERE line_id = 30 AND sensor_id = 1 AND ts = :ts",
        ts=ts,
    )
    assert n == 0


def test_writer_can_read_and_write_ingest_cursor():
    _execute(
        writer_engine,
        "INSERT INTO audit.ingest_cursor (line_id, last_processed_sequence) "
        "VALUES (30, 999) ON CONFLICT (line_id) DO UPDATE SET last_processed_sequence = EXCLUDED.last_processed_sequence",
    )
    seq = _scalar(
        writer_engine,
        "SELECT last_processed_sequence FROM audit.ingest_cursor WHERE line_id = 30",
    )
    assert seq == 999


# ---------- Reader role ----------

def test_reader_can_read_config():
    n = _scalar(reader_engine, "SELECT count(*) FROM config.sensor WHERE line_id = 30")
    assert n == 32


def test_reader_can_read_telemetry():
    n = _scalar(reader_engine, "SELECT count(*) FROM telemetry.measurement")
    assert n >= 68448


def test_reader_can_read_audit():
    n = _scalar(reader_engine, "SELECT count(*) FROM audit.backfill_batch")
    assert n >= 0


def test_reader_cannot_insert_telemetry():
    with pytest.raises(ProgrammingError):
        _execute(
            reader_engine,
            "INSERT INTO telemetry.measurement (line_id, sensor_id, ts, value, quality, source) "
            "VALUES (30, 1, NOW(), 0, 0, 1)",
        )


def test_reader_cannot_insert_config():
    with pytest.raises(ProgrammingError):
        _execute(
            reader_engine,
            "INSERT INTO config.sensor VALUES (9998, 30, 'x', 'x', 'x', false, NOW())",
        )


# ---------- Both roles ----------

def test_writer_cannot_write_config_line():
    with pytest.raises(ProgrammingError):
        _execute(
            writer_engine,
            "INSERT INTO config.line (line_id, name, site, timezone) "
            "VALUES (999, 'x', 'x', 'Asia/Kolkata')",
        )