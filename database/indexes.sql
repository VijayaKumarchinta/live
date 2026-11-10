CREATE INDEX IF NOT EXISTS ix_measurement_live_ts
    ON telemetry.measurement (ts DESC)
    WHERE source = 2;

CREATE INDEX IF NOT EXISTS ix_measurement_sensor_ts
    ON telemetry.measurement (sensor_id, ts DESC);

CREATE INDEX IF NOT EXISTS ix_alarm_event_state
    ON audit.alarm_event (state, triggered_at DESC);

CREATE INDEX IF NOT EXISTS ix_alarm_event_line_ts
    ON audit.alarm_event (line_id, triggered_at DESC);

CREATE INDEX IF NOT EXISTS ix_import_reject_batch
    ON audit.import_reject (batch_id);
