from flask import Blueprint, jsonify
from sqlalchemy import text
from app.db.engine import reader_engine, writer_engine

bp = Blueprint("health", __name__)

def _probe(engine) -> str:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        return f"error: {type(exc).__name__}"

@bp.get("/health")
def health():
    db_status = _probe(reader_engine)
    writer_status = _probe(writer_engine)
    return jsonify(
        status="healthy" if db_status == "ok" and writer_status == "ok" else "degraded",
        database={"reader": db_status, "writer": writer_status},
    )