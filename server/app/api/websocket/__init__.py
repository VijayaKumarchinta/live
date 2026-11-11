from app.api.websocket.routes import init_ws, sock
from app.api.websocket import listener
from app.api.websocket import listener

def start_ws(app) -> None:
    init_ws(app)
    listener.start()

def stop_ws() -> None:
    listener.stop()

__all__ = ["start_ws", "stop_ws", "sock"]