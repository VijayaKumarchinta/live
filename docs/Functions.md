# Line Speed 30 — Function Reference

Every function in the codebase (Phases 0–4), what it does, and why it exists. One line each.

---

## `server/config.py`

| Function | What it does | Why |
| --- | --- | --- |
| `_req(key)` | Reads a required env var; raises if missing or empty | Fail fast on startup instead of crashing deep in a query |
| `_int(key, default)` | Reads an int env var with a fallback | Type-coerce at the config layer so downstream code trusts types |
| `_float(key, default)` | Reads a float env var with a fallback | Same reason, for float settings |
| `Settings` (class body) | Loads and groups all config values by concern | Single source of truth; every module imports `settings` instead of touching `os.getenv` |
| `settings = Settings()` | Instantiated once at import | Singleton prevents drift between components |

---

## `server/app/db/base.py`

| Function | What it does | Why |
|---|---|---|
| `class Base(DeclarativeBase)` | SQLAlchemy 2.0 declarative base | Common ancestor for all future ORM models (Phase 6+) |

---

## `server/app/db/engine.py`

| Function | What it does | Why |
| --- | --- | --- |
| `_connect_args()` | Builds `connect_timeout` + statement/idle-in-transaction timeouts | Prevent hung connects, runaway queries, and leaked transactions |
| `_make_engine(url)` | Factory that returns a pooled SQLAlchemy engine | One helper so both engines share identical tuning |
| `writer_engine = _make_engine(...)` | Pool for `iiot_writer` (INSERT/UPDATE on telemetry/audit, SELECT on config) | The ingestion path owns this engine |
| `reader_engine = _make_engine(...)` | Pool for `iiot_reader` (SELECT only) | The display path owns this engine; cannot write by design |

---

## `server/app/db/session.py`

| Function | What it does | Why |
| --- | --- | --- |
| `WriterSession = sessionmaker(...)` | Session factory bound to `writer_engine` | ORM sessions for config/audit writes (Phase 6+) |
| `ReaderSession = sessionmaker(...)` | Session factory bound to `reader_engine` | ORM sessions for reads (Phase 6+) |

---

## `server/run.py`

| Function | What it does | Why |
| --- | --- | --- |
| `create_app()` | Flask app factory with `SECRET_KEY` set | Convention that supports Phase 6 blueprints and test isolation |
| `health()` | `GET /health` — pings both engines, returns `{status, database}` | Fast connectivity + auth check for both roles; no table access |
| `app = create_app()` | Module-level app instance | WSGI-compatible entry point |
| `if __name__ == "__main__"` block | Starts the dev server | Local development only |

---

## `server/services/loader/clean.py`

| Function | What it does | Why |
| --- | --- | --- |
| `sha256_of(path)` | 64 KB-chunked SHA-256 of a file | Stable file identity for idempotency and audit |
| `clean()` | Reads Excel, renames `;Date`→`Date`, drops `Millitm`, merges `Date`+`Time` → aware `ts`, coerces sensor columns to numeric, reports NaN, drops duplicate `ts`, reorders `ts` first | One-time Excel → canonical DataFrame transformation |
| `main()` | Calls `clean()`, writes Parquet, prints shape / range / SHA-256 of both files | CLI entry point for the one-shot cleaning step |

---

## `server/services/loader/validator.py`

| Function | What it does | Why |
| --- | --- | --- |
| `class ValidationResult` | Dataclass with `ok`, `errors`, `rejected_row_indices`, `rejected_reasons` | Structured return value that separates fatal errors from recoverable row-level rejects |
| `validate_dataframe(df, sensor_columns)` | Runs 4 checks: `ts` exists, sensors exist, not empty, no null `ts` | Gatekeeper between reading and writing; catches schema and quality issues before DB |

---

## `server/services/loader/normalizer.py`

| Function | What it does | Why |
|---|---|---|
| `normalize(df, line_id, sensor_map, source, tz)` | Wide → long transform; one dict per non-null sensor cell per row | Converts 2,139 wide rows into 68,448 long-format measurement dicts for bulk insert |

---

## `server/services/loader/backfill.py`

| Function | What it does | Why |
| --- | --- | --- |
| `sha256_of(path)` | Same chunked SHA-256 as `clean.py` | Reused for Parquet identity |
| `load_sensor_registry(line_id)` | Reads 32 `(tag, sensor_id)` pairs from `config.sensor` | Tag → sensor_id bridge used by `normalize` |
| `already_imported(file_sha256)` | SELECT from `audit.backfill_batch WHERE sha AND status='completed'` | Idempotency: skip re-imports of the same file |
| `create_batch(source_file, sha, line_id)` | INSERT audit row with `status='running'`, RETURNING `batch_id` | Paper trail starts before any measurement write |
| `finalize_batch(batch_id, ...)` | UPDATE audit row with counts + `status` + `completed_at=NOW()` | Paper trail closes whether import succeeded or failed |
| `insert_measurements(rows)` | Chunked `INSERT ... ON CONFLICT DO NOTHING` in one transaction | Fast, atomic, duplicate-safe bulk insert |
| `run_backfill(parquet_path, line_id)` | Orchestrates: SHA → idempotency → read → registry → validate → normalize → create batch → insert → finalize → return summary | The ingestion entry point; ties every loader function together |

---

## `server/services/loader/run.py`

| Function | What it does | Why |
|---|---|---|
| `main()` | Argparse `--file` and `--line`, calls `run_backfill`, prints JSON result | CLI wrapper so the loader can be invoked as `python -m services.loader.run` |

---

## Database scripts (`database/*.sql`)

Not functions, but each script is a "run once" step in a defined order:

| File | What it does | Why |
| --- | --- | --- |
| `setup.sql` | Creates roles, database, schemas, grants | Bootstrap that must run before any schema |
| `schema_config.sql` | Creates `config.line`, `sensor`, `setpoint_config`, `engineering_note` | Small, human-maintained reference data |
| `schema_telemetry.sql` | Creates `telemetry.measurement` (partitioned) + 4 `audit.*` tables | High-volume partitioned measurements and the audit trail |
| `indexes.sql` | PK, partial live index, sensor-time index, alarm/audit indexes | Query performance without over-indexing |
| `partitions.sql` | 2026 monthly partitions + `_default` fallback | Route rows by `ts`; default catches unexpected dates |
| `seed.sql` | 1 line + 32 sensors matching Excel column names | Make `config.sensor.tag` match every Parquet sensor column |

---

## Pipeline Runtime Order (Phases 0–4)

setup.sql → schema_config.sql → schema_telemetry.sql

indexes.sql → partitions.sql → seed.sql

services.loader.clean → produces Parquet

services.loader.run → backfills 68,448 rows (source=1)

run.py → /health sanity check

---

## Data Shape Summary

| Stage | Shape | Row count |
| --- | --- | --- |
| Excel `Line_Speed_30` sheet | 35 cols × 2,139 | 2,139 |
| Cleaned DataFrame | 33 cols (`ts` + 32 sensors) × 2,139 | 2,139 |
| `normalize` output | Dicts `{line_id, sensor_id, ts, value, quality, source}` | 68,448 |
| `telemetry.measurement` (source=1) | Same columns | 68,448 |
| `measurement_2026_04` | Same columns | 68,448 |
| `measurement_default` | Same columns | 0 |

---

## Roles and Their Touches

| Role | Reads | Writes |
| --- | --- | --- |
| `iiot_writer` | `config.*`, `audit.backfill_batch` | `telemetry.measurement`, `audit.*` |
| `iiot_reader` | All tables | Nothing |
| `postgres` (manual) | All | Config schema, grants, DDL |

---

## Deferred to Phase 5+

| File / function | Phase |
| --- | --- |
| `services/simulator/publisher.py` | 5 |
| `services/simulator/replay_simulator.py` | 5 |
| `services/ingester/subscriber.py` | 5 |
| `services/ingester/batch_writer.py` | 5 |
| `services/ingester/processor.py` | 5 |
| `services/ingester/run.py` | 5 |
| `app/repositories/*`, `app/api/routes/*` | 6 |
| `app/api/websocket/*` | 6 |
| `client/src/*` | 7–9 |
