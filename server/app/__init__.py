import logging
from flask import Flask
from config import settings
from app.api.routes import register_blueprints
from app.api.websocket import start_ws, stop_ws

def _configure_logging() -> None:
    level_name = getattr(settings, "LOG_LEVEL", "INFO") or "INFO"
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )

def create_app() -> Flask:
    _configure_logging()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.FLASK_SECRET_KEY

    register_blueprints(app)
    start_ws(app)
    
    return app