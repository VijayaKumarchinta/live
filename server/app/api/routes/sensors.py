from flask import Blueprint, jsonify, request
from app.repositories import config_repo
from app.services import telemetry_service

bp = Blueprint("sensors", __name__, url_prefix="/api")

@bp.get("/sensors")
def get_sensors():
    try:
        line_id = telemetry_service.parse_int(request.args.get("line_id"))
    except ValueError as exc:
        return jsonify(*telemetry_service.error(str(exc)))
    if line_id is None:
        return jsonify(*telemetry_service.error("line_id is required"))
    rows = config_repo.list_sensors(line_id)
    return jsonify(telemetry_service.envelope(rows, {"line_id": line_id, "count": len(rows)}))