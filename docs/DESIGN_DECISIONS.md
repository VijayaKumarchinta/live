# Line Speed 30 — Design Decisions Locked Before Phase 5

## Gate 1 — Replay Timestamp and Event Identity

Decision: Live rows use wall-clock now + i x 10s, second precision, Asia/Kolkata.

Rationale: PK is (line_id, sensor_id, ts). Historical rows have April 2026 timestamps. Replaying with original timestamps would collide on PK and ON CONFLICT DO NOTHING would insert 0 rows. Using now gives distinct timestamps.

Duplicate protection:

- message_id UUID v4 on every message
- In-memory deque(maxlen=1000) of recent message_ids
- audit.ingest_cursor.last_processed_sequence per line_id (survives restart)
- DB ON CONFLICT DO NOTHING as last line of defence

Loop semantics: Second pass uses now + (loop_count x run_duration) + i x 10s. Never reuses a timestamp.

## Gate 2 — MQTT JSON Contract

Decision: Documented in docs/MQTT_CONTRACT.md v1.0, enforced with jsonschema in both producer and consumer.

Rationale: Producer and consumer are separate processes. Without a written contract they drift. The contract has schema_version for future evolution.

## Gate 3 — Machine-to-Line Mapping

Decision: One machine per line for this scope. machine_id = 1 constant for line 30. No config.machine table.

Rationale: No multi-machine line in the project. Topic template includes {machine_id} for forward compatibility only. Documented in MQTT_CONTRACT.md section Machine Identity.

## Gate 4 — MQTT ACK Timing

Decision: ACK only after the transaction that inserts the measurements and updates ingest_cursor commits successfully.

Rationale: If ACK arrives before commit and the process crashes, the message is lost. Combined with ON CONFLICT and ingest_cursor, this becomes effectively exactly-once.

## Gate 5 — Queue-Full Behaviour

Decision: If INGEST_QUEUE_MAX is exceeded, the message is not ACKed. QoS 1 redelivers it. Do not drop silently.

Rationale: Silent drop is data loss. Queue-full applies backpressure.

## Gate 6 — Backfill Retry

Decision: Convert audit.backfill_batch.file_sha256 UNIQUE to a partial unique index WHERE status = 'completed'.

Rationale: Current UNIQUE blocks retry after a failed batch. The partial index preserves idempotency for completed imports while allowing retries.

## Deferred to Later Phases

| Concern | Phase |
| --- | --- |
| Cross-process WebSocket bridge | 6 |
| Cursor-based WebSocket recovery | 6 |
| Spill file replay | 13 |
| TLS, MQTT auth | 13 |
| API authentication | 12 |
| Materialized aggregates | 11 |
