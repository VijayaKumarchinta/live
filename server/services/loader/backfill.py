from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List

import pandas as pd
from sqlalchemy import text

from app.db.engine import writer_engine
from config import settings
from services.loader.normalizer import normalize
from services.loader.validator import validate_dataframe


SOURCE_HISTORICAL = 1
BATCH_SIZE = 1000


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sensor_registry(line_id: int) -> Dict[str, int]:
    with writer_engine.connect() as conn:
        rows = conn.execute(
            text("SELECT tag, sensor_id FROM config.sensor WHERE line_id = :line_id"),
            {"line_id": line_id},
        ).all()
    return {row.tag: row.sensor_id for row in rows}


def already_imported(file_sha256: str) -> bool:
    with writer_engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT batch_id FROM audit.backfill_batch "
                "WHERE file_sha256 = :sha AND status = 'completed'"
            ),
            {"sha": file_sha256},
        ).first()
    return row is not None


def create_batch(source_file: str, file_sha256: str, line_id: int) -> int:
    with writer_engine.begin() as conn:
        row = conn.execute(
            text(
                "INSERT INTO audit.backfill_batch "
                "(source_file, file_sha256, line_id, status) "
                "VALUES (:source_file, :sha, :line_id, 'running') "
                "RETURNING batch_id"
            ),
            {"source_file": source_file, "sha": file_sha256, "line_id": line_id},
        ).first()
    return int(row.batch_id)


def finalize_batch(
    batch_id: int,
    total: int,
    inserted: int,
    skipped: int,
    rejected: int,
    status: str,
) -> None:
    with writer_engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE audit.backfill_batch SET "
                "total_rows = :total, inserted_rows = :inserted, "
                "skipped_rows = :skipped, rejected_rows = :rejected, "
                "status = :status, completed_at = NOW() "
                "WHERE batch_id = :batch_id"
            ),
            {
                "batch_id": batch_id,
                "total": total,
                "inserted": inserted,
                "skipped": skipped,
                "rejected": rejected,
                "status": status,
            },
        )


def insert_measurements(rows: List[dict]) -> int:
    if not rows:
        return 0
    total = 0
    stmt = text(
        "INSERT INTO telemetry.measurement "
        "(line_id, sensor_id, ts, value, quality, source) "
        "VALUES (:line_id, :sensor_id, :ts, :value, :quality, :source) "
        "ON CONFLICT (line_id, sensor_id, ts) DO NOTHING"
    )
    with writer_engine.begin() as conn:
        for start in range(0, len(rows), BATCH_SIZE):
            chunk = rows[start : start + BATCH_SIZE]
            result = conn.execute(stmt, chunk)
            total += result.rowcount or 0
    return total


def run_backfill(parquet_path: Path, line_id: int) -> dict:
    file_sha = sha256_of(parquet_path)
    if already_imported(file_sha):
        return {"status": "skipped", "reason": "already imported", "sha256": file_sha}

    df = pd.read_parquet(parquet_path)
    if "ts" not in df.columns:
        raise RuntimeError("parquet missing 'ts' column; run clean.py first")

    registry = load_sensor_registry(line_id)
    sensor_columns = [c for c in df.columns if c in registry]
    if not sensor_columns:
        raise RuntimeError("no parquet columns match any registered sensor tag")

    validation = validate_dataframe(df, sensor_columns)
    if not validation.ok and not validation.rejected_row_indices:
        raise RuntimeError("; ".join(validation.errors))

    if validation.rejected_row_indices:
        df = df.drop(index=validation.rejected_row_indices).reset_index(drop=True)

    sensor_map = {col: registry[col] for col in sensor_columns}
    rows = normalize(df, line_id, sensor_map, SOURCE_HISTORICAL, settings.PLANT_TZ)

    batch_id = create_batch(str(parquet_path), file_sha, line_id)
    try:
        inserted = insert_measurements(rows)
        skipped = len(rows) - inserted
        finalize_batch(
            batch_id,
            len(df),
            inserted,
            skipped,
            len(validation.rejected_row_indices),
            "completed",
        )
    except Exception:
        finalize_batch(batch_id, len(df), 0, 0, 0, "failed")
        raise

    return {
        "status": "completed",
        "batch_id": batch_id,
        "source_rows": int(len(df)),
        "inserted": int(inserted),
        "skipped": int(skipped),
        "rejected": int(len(validation.rejected_row_indices)),
        "sha256": file_sha,
    }