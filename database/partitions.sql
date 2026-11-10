CREATE TABLE IF NOT EXISTS telemetry.measurement_2026_04
    PARTITION OF telemetry.measurement
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE TABLE IF NOT EXISTS telemetry.measurement_2026_05
    PARTITION OF telemetry.measurement
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE TABLE IF NOT EXISTS telemetry.measurement_2026_06
    PARTITION OF telemetry.measurement
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

CREATE TABLE IF NOT EXISTS telemetry.measurement_2026_07
    PARTITION OF telemetry.measurement
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

CREATE TABLE IF NOT EXISTS telemetry.measurement_2026_08
    PARTITION OF telemetry.measurement
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');

CREATE TABLE IF NOT EXISTS telemetry.measurement_2026_09
    PARTITION OF telemetry.measurement
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');

CREATE TABLE IF NOT EXISTS telemetry.measurement_2026_10
    PARTITION OF telemetry.measurement
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');

CREATE TABLE IF NOT EXISTS telemetry.measurement_2026_11
    PARTITION OF telemetry.measurement
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');

CREATE TABLE IF NOT EXISTS telemetry.measurement_2026_12
    PARTITION OF telemetry.measurement
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

CREATE TABLE IF NOT EXISTS telemetry.measurement_default
    PARTITION OF telemetry.measurement DEFAULT;