CREATE TABLE IF NOT EXISTS telemetry.measurement_2026_11
    PARTITION OF telemetry.measurement
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');

CREATE TABLE IF NOT EXISTS telemetry.measurement_2026_12
    PARTITION OF telemetry.measurement
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

CREATE TABLE IF NOT EXISTS telemetry.measurement_default
    PARTITION OF telemetry.measurement DEFAULT;
