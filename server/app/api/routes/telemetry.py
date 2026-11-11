from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from app.repositories import measurement_repo
from app.services import telemetry_service

bp = Blueprint("telemetry", __name__, url_prefix="/api")

MAX_RANGE_LIMIT = 5000
MAX_HISTORY_LIMIT = 1000
DEFAULT_SOURCE = 2

def _parse_source(raw):
    if raw is None or raw == "":
        return DEFAULT_SOURCE, None
    try:
        s = int(raw)
    except ValueError:
        return None, f"invalid source: {raw}"
    if s not in (1, 2):
        return None, f"source must be 1 or 2, got {s}"
    return s, None

@bp.get("/latest")
def get_latest():
    try:
        line_id = telemetry_service.parse_int(request.args.get("line_id"))
    except ValueError as exc:
        return jsonify(*telemetry_service.error(str(exc)))
    if line_id is None:
        return jsonify(*telemetry_service.error("line_id is required"))
    source, err = _parse_source(request.args.get("source"))
    if err:
        return jsonify(*telemetry_service.error(err))
    rows = measurement_repo.latest(line_id, source=source)
    return jsonify(telemetry_service.envelope(rows, {"line_id": line_id, "source": source, "count": len(rows)}))

@bp.get("/range")
def get_range():
    try:
        line_id = telemetry_service.parse_int(request.args.get("line_id"))
        sensor_ids = telemetry_service.parse_sensor_ids(request.args.get("sensor_ids"))
        limit = telemetry_service.parse_int(request.args.get("limit"), 5000)
    except ValueError as exc:
        return jsonify(*telemetry_service.error(str(exc)))
    if line_id is None:
        return jsonify(*telemetry_service.error("line_id is required"))
    if limit is None or limit <= 0 or limit > MAX_RANGE_LIMIT:
        return jsonify(*telemetry_service.error(f"limit must be 1..{MAX_RANGE_LIMIT}"))
    source, err = _parse_source(request.args.get("source"))
    if err:
        return jsonify(*telemetry_service.error(err))
    default_to = datetime.now(timezone.utc)
    default_from = default_to - timedelta(hours=1)
    try:
        ts_to = telemetry_service.parse_ts(request.args.get("to"), default_to)
        ts_from = telemetry_service.parse_ts(request.args.get("from"), default_from)
    except ValueError as exc:
        return jsonify(*telemetry_service.error(str(exc)))
    if ts_from > ts_to:
        return jsonify(*telemetry_service.error("from must be <= to"))
    rows = measurement_repo.range_rows(line_id, sensor_ids, ts_from, ts_to, limit, source=source)
    meta = {
        "line_id": line_id,
        "source": source,
        "sensor_ids": sensor_ids or "all",
        "from": ts_from.isoformat(),
        "to": ts_to.isoformat(),
        "count": len(rows),
    }
    return jsonify(telemetry_service.envelope(rows, meta))

@bp.get("/hourly")
def get_hourly():
    try:
        line_id = telemetry_service.parse_int(request.args.get("line_id"))
        sensor_id = telemetry_service.parse_int(request.args.get("sensor_id"))
    except ValueError as exc:
        return jsonify(*telemetry_service.error(str(exc)))
    if line_id is None:
        return jsonify(*telemetry_service.error("line_id is required"))
    if sensor_id is None:
        return jsonify(*telemetry_service.error("sensor_id is required"))
    source, err = _parse_source(request.args.get("source"))
    if err:
        return jsonify(*telemetry_service.error(err))
    ts_from = request.args.get("from")
    ts_to = request.args.get("to")
    try:
        dt_from = telemetry_service.parse_ts(ts_from, None) if ts_from else None
        dt_to = telemetry_service.parse_ts(ts_to, None) if ts_to else None
    except ValueError as exc:
        return jsonify(*telemetry_service.error(str(exc)))
    rows = measurement_repo.hourly_profile(line_id, sensor_id, dt_from, dt_to, source=source)
    meta = {
        "line_id": line_id,
        "source": source,
        "sensor_id": sensor_id,
        "from": dt_from.isoformat() if dt_from else None,
        "to": dt_to.isoformat() if dt_to else None,
        "count": len(rows),
    }
    return jsonify(telemetry_service.envelope(rows, meta))


@bp.get("/history")
def get_history():
    try:
        line_id = telemetry_service.parse_int(request.args.get("line_id"))
        sensor_id = telemetry_service.parse_int(request.args.get("sensor_id"))
        limit = telemetry_service.parse_int(request.args.get("limit"), 100)
        offset = telemetry_service.parse_int(request.args.get("offset"), 0)
    except ValueError as exc:
        return jsonify(*telemetry_service.error(str(exc)))
    if line_id is None:
        return jsonify(*telemetry_service.error("line_id is required"))
    if limit is None or limit <= 0 or limit > MAX_HISTORY_LIMIT:
        return jsonify(*telemetry_service.error(f"limit must be 1..{MAX_HISTORY_LIMIT}"))
    if offset is None or offset < 0:
        return jsonify(*telemetry_service.error("offset must be >= 0"))
    source, err = _parse_source(request.args.get("source"))
    if err:
        return jsonify(*telemetry_service.error(err))
    rows = measurement_repo.history(line_id, limit, offset, sensor_id, source=source)
    meta = {
        "line_id": line_id,
        "source": source,
        "sensor_id": sensor_id,
        "limit": limit,
        "offset": offset,
        "count": len(rows),
    }
    return jsonify(telemetry_service.envelope(rows, meta))

@bp.get("/stats")
def get_stats():
    try:
        line_id = telemetry_service.parse_int(request.args.get("line_id"))
    except ValueError as exc:
        return jsonify(*telemetry_service.error(str(exc)))
    if line_id is None:
        return jsonify(*telemetry_service.error("line_id is required"))
    data = measurement_repo.stats(line_id)
    return jsonify(telemetry_service.envelope(data, {"line_id": line_id}))

@bp.get("/hourly-summary")
def get_hourly_summary():
    try:
        line_id = telemetry_service.parse_int(request.args.get("line_id"))
    except ValueError as exc:
        return jsonify(*telemetry_service.error(str(exc)))
    if line_id is None:
        return jsonify(*telemetry_service.error("line_id is required"))
    source, err = _parse_source(request.args.get("source"))
    if err:
        return jsonify(*telemetry_service.error(err))
    rows = measurement_repo.hourly_summary(line_id, source=source)
    return jsonify(telemetry_service.envelope(rows, {"line_id": line_id, "source": source, "count": len(rows)}))

@bp.get("/history-pivot")
def get_history_pivot():
    try:
        line_id = telemetry_service.parse_int(request.args.get("line_id"))
        limit = telemetry_service.parse_int(request.args.get("limit"), 12)
    except ValueError as exc:
        return jsonify(*telemetry_service.error(str(exc)))
    if line_id is None:
        return jsonify(*telemetry_service.error("line_id is required"))
    if limit is None or limit <= 0 or limit > 100:
        return jsonify(*telemetry_service.error("limit must be 1..100"))
    source, err = _parse_source(request.args.get("source"))
    if err:
        return jsonify(*telemetry_service.error(err))
    rows = measurement_repo.history_pivot(line_id, limit=limit, source=source)
    return jsonify(telemetry_service.envelope(rows, {"line_id": line_id, "source": source, "limit": limit, "count": len(rows)}))