import json
import logging
import threading
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)

class ClientHub:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._clients: Set[Any] = set()

    def register(self, ws) -> None:
        with self._lock:
            self._clients.add(ws)
        logger.info("ws client registered (%d total)", self.count())

    def unregister(self, ws) -> None:
        with self._lock:
            self._clients.discard(ws)
        logger.info("ws client unregistered (%d total)", self.count())

    def count(self) -> int:
        with self._lock:
            return len(self._clients)

    def broadcast(self, payload: Dict[str, Any]) -> int:
        text = json.dumps(payload, default=str)
        with self._lock:
            clients: List[Any] = list(self._clients)
        dead = []
        sent = 0
        for ws in clients:
            try:
                ws.send(text)
                sent += 1
            except Exception:
                dead.append(ws)
        if dead:
            with self._lock:
                for ws in dead:
                    self._clients.discard(ws)
            logger.info("pruned %d dead ws clients", len(dead))
        return sent

hub = ClientHub()