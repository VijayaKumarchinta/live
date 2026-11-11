from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "server"
if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))


@pytest.fixture(scope="session")
def parquet_path() -> Path:
    p = ROOT / "archive" / "backfill" / "line_speed_30_clean.parquet"
    if not p.exists():
        pytest.skip(f"cleaned parquet not found: {p}")
    return p