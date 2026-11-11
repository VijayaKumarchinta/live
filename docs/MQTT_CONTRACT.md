# Line Speed 30 — MQTT Message Contract

**Version:** 1.0
**Status:** Locked before Phase 5 implementation
**Binding on:** `services/simulator/replay_simulator.py` (producer) and `services/ingester/processor.py` (consumer)

## Topic

    plant/{line_id}/{machine_id}/telemetry

- Producer publishes to: `plant/30/1/telemetry`
- Consumer subscribes to: `plant/30/+/telemetry` (QoS 1)

## Machine Identity

For the scope of this project, each line has exactly one machine. `machine_id` is always `1` for line 30. The topic template includes `{machine_id}` for forward compatibility only. There is no `config.machine` table in this scope.

## Message Envelope

    {
      "schema_version": "1.0",
      "message_id": "<UUID v4>",
      "line_id": 30,
      "machine_id": 1,
      "timestamp": "2026-11-11T10:15:23+05:30",
      "sequence": 42,
      "measurements": [
        { "tag": "Burner Output Load", "value": 91.2, "quality": 0 }
      ]
    }

## Field Rules

| Field | Type | Required | Rule |
|---|---|---|---|
| schema_version | string | yes | Must equal "1.0" |
| message_id | string | yes | UUID v4, unique per message |
| line_id | int | yes | Must match config.line |
| machine_id | int | yes | Must be 1 for this project |
| timestamp | string | yes | ISO-8601 with offset, second precision |
| sequence | int | yes | Monotonic per simulator run, starting at 1 |
| measurements | array | yes | At least one entry |
| measurements[].tag | string | yes | Must match config.sensor.tag |
| measurements[].value | float | yes | Must be finite (no NaN, no Inf) |
| measurements[].quality | int | no | Defaults to 0 |

## Timestamp Strategy (Locked)

| Decision | Value |
|---|---|
| Time base | Wall-clock now at simulator start + i x 10 seconds per row |
| Precision | Second |
| Timezone | Asia/Kolkata from settings.PLANT_TZ |
| Loop behaviour | Second pass uses now + (loop_count x run_duration) + i x 10s; never repeats a timestamp |

## Duplicate Protection Layers

1. Producer: message_id UUID v4, unique per publish
2. Ingester in-memory: deque of last 1000 message_ids
3. Ingester persistent: audit.ingest_cursor.last_processed_sequence per line_id
4. Database: ON CONFLICT (line_id, sensor_id, ts) DO NOTHING

## Failure Semantics

| Failure | Behaviour |
|---|---|
| Invalid JSON | audit.import_reject row; ACK |
| Unknown schema_version | audit.import_reject row; ACK |
| Missing required field | audit.import_reject row; ACK |
| Unknown sensor tag | Drop measurement; log; continue |
| Non-finite value | Drop measurement; log; continue |
| DB unavailable | Retry with backoff; on overflow, write to ingest_spill; ACK after spill |
| Queue full | Do NOT ACK; QoS 1 redelivers |
| Process kill mid-batch | Resume from ingest_cursor.last_processed_sequence |

## Deferred

Authentication (Phase 12), TLS (Phase 13), Compression (not needed at this volume), Schema version 2.0+ (future).