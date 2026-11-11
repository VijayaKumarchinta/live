import json
import sys
from websocket import create_connection

def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8000/ws/live?line_id=30"
    print(f"connecting to {url}", flush=True)
    ws = create_connection(url, timeout=None)
    try:
        while True:
            msg = ws.recv()
            try:
                obj = json.loads(msg)
            except Exception:
                obj = msg
            print(obj, flush=True)
    except KeyboardInterrupt:
        print("\nclosing", flush=True)
    finally:
        ws.close()

if __name__ == "__main__":
    main()