import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

def _req(key: str) -> str:
    value = os.getenv(key)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value

def _int(key: str, default: int) -> int:
    raw = os.getenv(key)
    return int(raw) if raw not in (None, "") else default

def _float(key: str, default: float) -> float:
    raw = os.getenv(key)
    return float(raw) if raw not in (None, "") else default

class Settings:
    DATABASE_URL_WRITER: str = _req("DATABASE_URL_WRITER")
    DATABASE_URL_READER: str = _req("DATABASE_URL_READER")

    DB_CONNECT_TIMEOUT: int = _int("DB_CONNECT_TIMEOUT", 5)
    DB_POOL_SIZE: int = _int("DB_POOL_SIZE", 5)
    DB_MAX_OVERFLOW: int = _int("DB_MAX_OVERFLOW", 10)
    DB_POOL_TIMEOUT: int = _int("DB_POOL_TIMEOUT", 5)
    DB_STATEMENT_TIMEOUT_MS: int = _int("DB_STATEMENT_TIMEOUT_MS", 15000)

    MQTT_HOST: str = _req("MQTT_HOST")
    MQTT_PORT: int = _int("MQTT_PORT", 1883)
    MQTT_USERNAME: str = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "")
    MQTT_CA_CERT: str = os.getenv("MQTT_CA_CERT", "")
    MQTT_CLIENT_CERT: str = os.getenv("MQTT_CLIENT_CERT", "")
    MQTT_CLIENT_KEY: str = os.getenv("MQTT_CLIENT_KEY", "")
    MQTT_TOPIC_TEMPLATE: str = _req("MQTT_TOPIC_TEMPLATE")
    MQTT_QOS: int = _int("MQTT_QOS", 1)

    SOURCE_WINDOW_MINUTES: int = _int("SOURCE_WINDOW_MINUTES", 10)
    DASHBOARD_RENDER_INTERVAL_S: int = _int("DASHBOARD_RENDER_INTERVAL_S", 5)
    PLANT_TZ: str = os.getenv("PLANT_TZ", "Asia/Kolkata")
    CUTOVER_TS: str = _req("CUTOVER_TS")
    RETENTION_MONTHS: int = _int("RETENTION_MONTHS", 12)

    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = _int("API_PORT", 8000)
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "0") == "1"
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

    WS_HEARTBEAT_S: int = _int("WS_HEARTBEAT_S", 30)
    WS_CLIENT_QUEUE_MAX: int = _int("WS_CLIENT_QUEUE_MAX", 1000)
    INGEST_QUEUE_MAX: int = _int("INGEST_QUEUE_MAX", 10000)

    ARCHIVE_DIR: str = os.getenv("ARCHIVE_DIR", "./archive/backfill")
    SPILL_DIR: str = os.getenv("SPILL_DIR", "./ingest_spill")
    LOG_DIR: str = os.getenv("LOG_DIR", "./logs")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
