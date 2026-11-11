import json
import logging
from flask import request
from flask_sock import Sock
from app.api.websocket.hub import hub

logger = logging.getLogger(__name__)
sock = Sock()

def init_ws(app) -> None:
    sock.init_app(app)

    @sock.route("/ws/live")
    def ws_live(ws):
        line_id = request.args.get("line_id", type=int)
        hub.register(ws)
        try:
            ws.send(json.dumps({
                "type": "hello",
                "line_id": line_id,
                "clients": hub.count(),
            }))
            while True:
                msg = ws.receive(timeout=None)
                if msg is None:
                    break
        except Exception:
            pass
        finally:
            hub.unregister(ws)