# Line Speed 30 — IIoT Live Monitoring Dashboard

A production-ready, Phase 1–4 skeleton of the **Line Speed 30** industrial IoT dashboard: historical Excel backfill, queued MQTT telemetry ingestion into partitioned PostgreSQL, a Flask REST + WebSocket API, and a Vue 3 (Vite) frontend scaffold. Built entirely on the Windows command line.

## What exists right now

| Area | Status |
|---|---|
| Toolchain pre-flight | Python 3.14.7, Node 24.19.0, npm 11.17.0, PostgreSQL 18.6, Mosquitto 2.1.2, Git 2.45.1 |
| Project structure | Root + `database/`, `server/` (Python), `client/` (Vue), `archive/backfill/`, `ingest_spill/`, `logs/`, `tests/{unit,integration,end_to_end}/` |
| Server dependencies | Flask, flask-sock, SQLAlchemy 2.x, psycopg (v3), paho-mqtt, pandas, pyarrow, openpyxl, python-dotenv |
| Config | `server/config.py` — loads `server/.env`, exposes one `settings` singleton, validates required keys and types |
| Database layer | `server/app/db/{base,engine,session}.py` — `Base` declarative class, `writer_engine` and `reader_engine` with pool tuning and statement timeouts |
| Server entrypoint | `server/run.py` — Flask app factory, `GET /health` pings both engines, returns `{status, database}` |
| Roles & schemas | `iiot_writer` (WRITE on telemetry/audit, SELECT on config), `iiot_reader` (SELECT only), three schemas: `config`, `telemetry`, `audit` |
| DB scripts | `database/setup.sql`, `database/setup.sql (then schema_config.sql, schema_telemetry.sql, partitions.sql, ingest_cursor.sql, indexes.sql, seed.sql)`, `database/indexes.sql`, `database/partitions.sql`, `database/seed.sql` |
| Historical backfill | `server/services/loader/` (clean/normalizer/validator/backfill) ingested **68,448** rows from the cleaned Parquet into `telemetry.measurement_2026_04` |
| MQTT pipeline | `server/services/{simulator,ingester}/` — Paho publisher, replay simulator (`--time-base now|parquet`), subscriber, batch writer, ingester processor, ingester entrypoint |
| Frontend | `client/` — Vite + Vue 3 scaffold with `src/components/`, `src/stores/`, `src/services/`, `src/views/`, `src/router/`, `.env`, `.env.example`, `package.json`, `vite.config.js` |

## Why two PostgreSQL roles

The write and read paths are deliberately separated:

| Path | Driver | Constraint |
|---|---|---|
| Write path | Backfill loader + MQTT ingester | `INSERT` into `telemetry.measurement`, `INSERT` into audit tables |
| Read path | Flask REST API + WebSocket gap recovery | `SELECT` on measurements and config only |

`iiot_reader` is locked to `SELECT`. A bug in a read endpoint cannot corrupt history — PostgreSQL itself rejects the write. The writer credential lives only in the loader and ingester processes, so a leaked API `.env` cannot write data. Alarm acknowledgement (`POST /api/alarms/:id/ack`) is the single documented exception: a narrowly scoped write on `audit.alarm_event` only.

## Why three schemas

| Schema | Volume | Lifecycle |
|---|---|---|
| `telemetry` | Very high (one row per sensor per timestamp) | Partitioned by month, live partitions expire |
| `config` | Tiny (lines, sensors, setpoints) | Permanent, read-mostly |
| `audit` | Low-medium (imports, rejects, alarms) | Permanent, compliance |

Retention, partitioning, backup, and permissions each target exactly one concern. `telemetry.measurement` is the only partitioned table. The `iiot_writer` owns `telemetry` and `audit`; `config` is owned by `postgres`.

## Getting started

### 1. Pre-flight tools (Python 3.11+, Node 18+, PostgreSQL 15+)

```bash
python --version
node --version
npm --version
psql --version
mosquitto -h
git --version
```

### 2. Root files and folders

```bash
mkdir line-speed-30
cd line-speed-30
git init
mkdir -p database archive/backfill logs ingest_spill tests unit integration end_to_end
```

### 3. Server skeleton (PowerShell)

```powershell
New-Item -ItemType Directory -Force -Path server\app\db, server\app\models, server\app\repositories, server\app\services, server\app\api\routes, server\app\api\websocket, server\services\loader, server\services\simulator, server\services\ingester, server\services\partition
New-Item -ItemType File -Path server\app\__init__.py, server\app\db\__init__.py, server\app\models\__init__.py, server\app\repositories\__init__.py, server\app\services\__init__.py, server\app\api\__init__.py, server\app\api\routes\__init__.py, server\app\api\websocket\__init__.py, server\services\__init__.py, server\services\loader\__init__.py, server\services\simulator\__init__.py, server\services\ingester\__init__.py, server\services\partition\__init__.py
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install flask flask-sock sqlalchemy psycopg2-binary paho-mqtt pandas pyarrow openpyxl python-dotenv
```

### 4. Database bootstrap

```powershell
psql -U postgres
```

At the `postgres=#` prompt:

```sql
CREATE ROLE iiot_writer LOGIN PASSWORD 'change_me';
CREATE ROLE iiot_reader LOGIN PASSWORD 'change_me';
CREATE DATABASE iiot_dashboard OWNER postgres;
\c iiot_dashboard
CREATE SCHEMA telemetry AUTHORIZATION iiot_writer;
CREATE SCHEMA audit AUTHORIZATION iiot_writer;
CREATE SCHEMA config AUTHORIZATION postgres;
GRANT USAGE ON SCHEMA config TO iiot_writer, iiot_reader;
GRANT USAGE ON SCHEMA telemetry TO iiot_reader;
GRANT USAGE ON SCHEMA audit TO iiot_reader;
GRANT CREATE ON SCHEMA config TO iiot_writer;
GRANT CREATE ON SCHEMA telemetry TO iiot_writer;
GRANT CREATE ON SCHEMA audit TO iiot_writer;
GRANT SELECT ON ALL TABLES IN SCHEMA config TO iiot_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA telemetry TO iiot_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA audit TO iiot_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE iiot_writer IN SCHEMA telemetry GRANT SELECT ON TABLES TO iiot_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE iiot_writer IN SCHEMA audit GRANT SELECT ON TABLES TO iiot_reader;
\q
```

### 5. Server `.env`

```powershell
Copy-Item .env.example server\.env
notepad server\.env
```

Replace `change_me` with the passwords you set on the roles in Step 4. Run `python -c "import secrets; print(secrets.token_hex(32))"` and paste the output into `FLASK_SECRET_KEY`.

### 6. Verify the database layer

```powershell
.\.venv\Scripts\Activate.ps1
python -c "from config import settings; print('writer:', settings.DATABASE_URL_WRITER.split('@')[0]); print('reader:', settings.DATABASE_URL_READER.split('@')[0])"
python -c "from app.db.engine import reader_engine, writer_engine; from sqlalchemy import text; print('reader:', reader_engine.connect().execute(text('SELECT current_user')).scalar()); print('writer:', writer_engine.connect().execute(text('SELECT current_user')).scalar())"
python run.py
```

In another terminal: `curl http://127.0.0.1:8000/health` → expect `{"database":{"reader":"ok","writer":"ok"},"status":"healthy"}`.

### 7. Frontend scaffold

```powershell
cd ..
npm create vite@latest client -- --template vue
cd client
npm install
npm install pinia vue-router axios echarts
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
echo "VITE_WS_URL=ws://localhost:8000/ws/v1" > .env.example
```

### 8. Database scripts

Import in this order against `iiot_dashboard`:

```powershell
$env:PGPASSWORD="your_postgres_superuser_password"
psql -U postgres -d iiot_dashboard -f database\setup.sql
psql -U postgres -d iiot_dashboard -f database\schema.sql
psql -U postgres -d iiot_dashboard -f database\indexes.sql
psql -U postgres -d iiot_dashboard -f database\partitions.sql
psql -U postgres -d iiot_dashboard -f database\seed.sql
Remove-Item Env:\PGPASSWORD
```

## Point-in-time state of database

| Item | Value |
|---|---|
| Database | `iiot_dashboard` on `localhost:5432` |
| Roles | `iiot_writer`, `iiot_reader` (passwords match `server/.env`) |
| Schemas | `config` (postgres), `telemetry` (iiot_writer), `audit` (iiot_writer) |
| Partitions on `telemetry.measurement` | `measurement_2026_04` … `measurement_2026_12` + `measurement_default` |
| `telemetry.measurement` | 68,448 rows (all `source=1`, April 2026) |
| `measurement_default` | 0 |

## Frontend tree

```text
client/
├── .env
├── .env.example
├── package.json
├── vite.config.js
└── src/
    ├── App.vue
    ├── assets/
    ├── components/
    │   ├── charts/
    │   ├── kpi/
    │   ├── layout/
    │   ├── alarms/
    │   └── common/
    ├── router/
    ├── services/
    ├── stores/
    └── views/
```

## Remaining phases (in build order)

| Phase | What it adds |
|---|---|
| 5 — Live MQTT pipeline | Simulator, publisher, subscriber, ingester, batch writer, spill manager |
| 6 — Flask REST + WebSocket | Measurement/config repositories, telemetry service, line/sensor/telemetry/alarm/health routes, WebSocket handler + broadcaster |
| 7 — Vue Live dashboard | Pinia stores, ECharts line chart, KPI cards, 5-second refresh |
| 8 — Historical replay | Date-range picker, timeline scrubber, aggregates + min/max envelope |
| 9 — Alarm engine | Threshold, rate-of-change, cross-variable rules, dedup, state machine, ack endpoint |
| 10 — Partition scheduler | Monthly partition creation, retention pruning, `_default` leakage alarms |
| 11 — Failure recovery | DB-down, broker-restart, WebSocket-disconnect, partition-miss scenarios |
| 12 — Hardening backend | Secrets rotation, auth, CORS whitelist, rate limiting, structured logs |
| 13 — Hardening live pipeline | Spill-file persistence, dead-letter queue, TLS/MQTT auth, backpressure |
| 14 — Deployment and handoff | Architecture docs, operations guide, API docs, deployment wrappers |

## Reference commands

```powershell
# Server
cd F:\line-speed-30\server
.\.venv\Scripts\Activate.ps1
Invoke-RestMethod http://127.0.0.1:8000/health | ConvertTo-Json -Depth 4
python run.py

# Database
$env:PGPASSWORD="your_postgres_superuser_password"
psql -U postgres -d iiot_dashboard -c "SELECT source, count(*) FROM telemetry.measurement GROUP BY source ORDER BY source;"
psql -U postgres -d iiot_dashboard -c "SELECT count(*) FROM telemetry.measurement_default;"
Remove-Item Env:\PGPASSWORD

# Client
cd F:\line-speed-30\client
npm run dev
```

## Known issues and deferred fixes

| # | Issue | Impact | Deferred to |
|---|---|---|---|
| 1 | `audit.backfill_batch` has `UNIQUE(file_sha256)` | Blocks retry after a failed batch | Phase 12 — partial unique index `WHERE status = 'completed'` |
| 2 | No spill-file persistence in ingester | Live data lost during PostgreSQL downtime | Phase 13 |
| 3 | Ingester drops measurements when queue is full | Acceptable at current scale | Phase 13 — add queue_drop counter |
| 4 | No authentication on `/health` | Fine for local dev | Phase 12 — token or IP allowlist |
| 5 | `.env` contains `change_me` passwords | Must not leak in production | Phase 12 — rotate, use secrets manager |

## Notes

- No Alembic migrations. Schema changes are SQL scripts in `database/`, executed in order.
- Redis and Celery are intentionally not used; the queue is an in-process `queue.Queue` plus bounded queue settings in `.env`.
- The MQTT topic template is `plant/{line_id}/{machine_id}/telemetry` (simulator: `plant/30/1/telemetry`, ingester: `plant/30/+/telemetry`).
- Source window is 10 minutes; live messages are re-derived from the same Parquet with wall-clock timestamps, preserving the 10-second spacing in the payload `ts` field.
