from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from config import settings

def _connect_args() -> dict:
    return {
        "connect_timeout": settings.DB_CONNECT_TIMEOUT,
        "options": (
            f"-c statement_timeout={settings.DB_STATEMENT_TIMEOUT_MS} "
            f"-c idle_in_transaction_session_timeout={settings.DB_STATEMENT_TIMEOUT_MS * 2}"
        ),
    }

def _make_engine(url: str) -> Engine:
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        future=True,
        connect_args=_connect_args(),
    )

writer_engine: Engine = _make_engine(settings.DATABASE_URL_WRITER)
reader_engine: Engine = _make_engine(settings.DATABASE_URL_READER)
