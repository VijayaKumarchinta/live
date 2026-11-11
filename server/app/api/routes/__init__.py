from flask import Flask
from app.api.routes import health, lines, sensors, telemetry

def register_blueprints(app: Flask) -> None:
    app.register_blueprint(health.bp)
    app.register_blueprint(lines.bp)
    app.register_blueprint(sensors.bp)
    app.register_blueprint(telemetry.bp)