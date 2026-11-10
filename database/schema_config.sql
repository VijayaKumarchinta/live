CREATE TABLE IF NOT EXISTS config.line (
    line_id     SMALLINT PRIMARY KEY,
    name        VARCHAR(64) NOT NULL UNIQUE,
    site        VARCHAR(64) NOT NULL,
    timezone    VARCHAR(64) NOT NULL DEFAULT 'Asia/Kolkata',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS config.sensor (
    sensor_id    SMALLINT PRIMARY KEY,
    line_id      SMALLINT NOT NULL REFERENCES config.line(line_id) ON DELETE CASCADE,
    tag          VARCHAR(64) NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    unit         VARCHAR(32) NOT NULL,
    zero_is_missing BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (line_id, tag)
);

CREATE TABLE IF NOT EXISTS config.setpoint_config (
    setpoint_id  SMALLINT PRIMARY KEY,
    line_id      SMALLINT NOT NULL REFERENCES config.line(line_id) ON DELETE CASCADE,
    sensor_id    SMALLINT REFERENCES config.sensor(sensor_id) ON DELETE SET NULL,
    name         VARCHAR(64) NOT NULL,
    low_limit    DOUBLE PRECISION,
    high_limit   DOUBLE PRECISION,
    hysteresis   DOUBLE PRECISION NOT NULL DEFAULT 0,
    dwell_seconds INT NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS config.engineering_note (
    note_id      BIGSERIAL PRIMARY KEY,
    line_id      SMALLINT REFERENCES config.line(line_id) ON DELETE CASCADE,
    sensor_id    SMALLINT REFERENCES config.sensor(sensor_id) ON DELETE SET NULL,
    body         TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);