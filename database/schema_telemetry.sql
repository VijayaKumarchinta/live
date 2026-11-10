CREATE TABLE IF NOT EXISTS telemetry.measurement (
    line_id   SMALLINT NOT NULL,
    sensor_id SMALLINT NOT NULL,
    ts        TIMESTAMPTZ NOT NULL,
    value     DOUBLE PRECISION,
    quality   SMALLINT NOT NULL DEFAULT 0,
    source    SMALLINT NOT NULL,
    PRIMARY KEY (line_id, sensor_id, ts)
) PARTITION BY RANGE (ts);

CREATE TABLE IF NOT EXISTS audit.backfill_batch (
    batch_id        BIGSERIAL PRIMARY KEY,
    source_file     TEXT NOT NULL,
    file_sha256     CHAR(64) NOT NULL UNIQUE,
    line_id         SMALLINT NOT NULL REFERENCES config.line(line_id),
    total_rows      INTEGER NOT NULL DEFAULT 0,
    inserted_rows   INTEGER NOT NULL DEFAULT 0,
    skipped_rows    INTEGER NOT NULL DEFAULT 0,
    rejected_rows   INTEGER NOT NULL DEFAULT 0,
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS audit.import_reject (
    reject_id   BIGSERIAL PRIMARY KEY,
    batch_id    BIGINT REFERENCES audit.backfill_batch(batch_id) ON DELETE CASCADE,
    source_row  INTEGER NOT NULL,
    reason      TEXT NOT NULL,
    payload     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit.alarm_event (
    alarm_id    BIGSERIAL PRIMARY KEY,
    line_id     SMALLINT NOT NULL REFERENCES config.line(line_id),
    sensor_id   SMALLINT REFERENCES config.sensor(sensor_id) ON DELETE SET NULL,
    rule_type   VARCHAR(32) NOT NULL,
    severity    VARCHAR(16) NOT NULL DEFAULT 'warning',
    state       VARCHAR(16) NOT NULL DEFAULT 'pending',
    dedup_key   VARCHAR(128) NOT NULL,
    message     TEXT NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL,
    acknowledged_at TIMESTAMPTZ,
    cleared_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (dedup_key)
);

CREATE TABLE IF NOT EXISTS audit.partition_job (
    job_id      BIGSERIAL PRIMARY KEY,
    run_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    action      VARCHAR(32) NOT NULL,
    target      VARCHAR(128) NOT NULL,
    status      VARCHAR(16) NOT NULL,
    detail      TEXT
);