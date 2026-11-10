from flask import Flask, jsonify
from config import settings
from app.db.engine import reader_engine, writer_engine

def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.FLASK_SECRET_KEY

    @app.get("/health")
    def health():
        from sqlalchemy import text

        db_status = "ok"
        try:
            with reader_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:
            db_status = f"error: {type(exc).__name__}"

        writer_status = "ok"
        try:
            with writer_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as exc:
            writer_status = f"error: {type(exc).__name__}"

        return jsonify(
            status="healthy" if db_status == "ok" and writer_status == "ok" else "degraded",
            database={"reader": db_status, "writer": writer_status},
        )
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host=settings.API_HOST, port=settings.API_PORT, debug=settings.FLASK_DEBUG)
