from flask import Blueprint, jsonify
from app.repositories import config_repo
from app.services import telemetry_service

bp = Blueprint("lines", __name__, url_prefix="/api")

@bp.get("/lines")
def get_lines():
    return jsonify(telemetry_service.envelope(config_repo.list_lines()))