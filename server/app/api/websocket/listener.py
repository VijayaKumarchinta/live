import json
import logging
import os
import select
import threading
from typing import Optional
import psycopg
from psycopg import Connection
from config import settings
from app.api.websocket.hub import hub

logger = logging.getLogger(__name__)

CHANNEL = "telemetry_live"


def _normalise_dsn(url: str) -> str:
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql://" + url[len("postgresql+psycopg2://"):]
    if url.startswith("postgresql+psycopg://"):
        return "postgresql://" + url[len("postgresql+psycopg://"):]
    if url.startswith("postgresql+asyncpg://"):
        raise RuntimeError("listener requires a sync DSN, not asyncpg")
    return url


class ListenerThread(threading.Thread):
    def __init__(self) -> None:
        super().__init__(name="pg-listen-telemetry_live", daemon=True)
        self._stop = threading.Event()
        self._conn: Optional[Connection] = None

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                self._connect_and_listen()
            except Exception as exc:
                logger.warning("listener crashed (%s); reconnecting in 2s", type(exc).__name__)
                if self._stop.wait(2.0):
                    return
            finally:
                self._close()

    def _connect_and_listen(self) -> None:
        dsn = _normalise_dsn(settings.DATABASE_URL_WRITER)
        self._conn = psycopg.connect(dsn, autocommit=True)
        with self._conn.cursor() as cur:
            cur.execute(f"LISTEN {CHANNEL};")
        logger.info("listening on channel %s (pid=%d)", CHANNEL, os.getpid())

        fd = self._conn.fileno()
        while not self._stop.is_set():
            r, _, _ = select.select([fd], [], [], 1.0)
            if not r:
                continue
            for notify in self._conn.notifies(timeout=0.0, stop_after=100):
                try:
                    payload = json.loads(notify.payload)
                except Exception:
                    payload = {"raw": notify.payload}
                payload.setdefault("type", "telemetry")
                sent = hub.broadcast(payload)
                logger.debug(
                    "notify line=%s seq=%s sent_to=%d",
                    payload.get("line_id"),
                    payload.get("last_seq"),
                    sent,
                )

    def _close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def stop(self) -> None:
        self._stop.set()
        self._close()

_listener: Optional[ListenerThread] = None

def start() -> None:
    global _listener
    if _listener is not None and _listener.is_alive():
        return
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true" and os.environ.get("FLASK_DEBUG") in ("1", "true"):
        logger.info("reloader parent: skipping listener (child will start it)")
        return
    _listener = ListenerThread()
    _listener.start()


def stop() -> None:
    global _listener
    if _listener is not None:
        _listener.stop()
        _listener = None