CREATE TABLE IF NOT EXISTS audit.ingest_cursor (
    line_id                   SMALLINT PRIMARY KEY,
    last_processed_sequence   BIGINT NOT NULL DEFAULT 0,
    last_processed_message_id VARCHAR(64),
    last_processed_ts         TIMESTAMPTZ,
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);