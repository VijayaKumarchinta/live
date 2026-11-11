import json
import logging
import queue
import signal
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
import jsonschema
from config import settings
from services.ingester import batch_writer
from services.ingester.subscriber import MqttSubscriber

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "mqtt_v1.json"

def _load_schema() -> dict:
    with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)

class Ingester:
    def __init__(self, line_id: int = 30) -> None:
        self.line_id = line_id
        self.sensor_map = batch_writer.load_sensor_map(line_id)
        self.queue: queue.Queue = queue.Queue(maxsize=settings.INGEST_QUEUE_MAX)
        self._stop = threading.Event()
        self._validator = jsonschema.Draft202012Validator(_load_schema())
        self._seen_message_ids: deque = deque(maxlen=1000)
        self._last_sequence = batch_writer.load_cursor(line_id)
        self._stats = {"received": 0, "accepted": 0, "rejected_schema": 0, "rejected_unknown": 0, "rejected_queue_full": 0, "rejected_wrong_line": 0, "duplicate_message_id": 0, "duplicate_sequence": 0}
        self._rows_buffer: list = []
        self._pending_msgs: list = []
        self._last_flush: float = 0.0
        self._flush_interval: float = 2.0
        self._buffer_last_seq: int = 0
        self._buffer_last_mid: str = ""
        self._buffer_last_ts: datetime | None = None
        self._client = None

    def _on_message(self, client, userdata, msg) -> None:
        if self._client is None:
            self._client = client
        self._stats["received"] += 1
        try:
            record = json.loads(msg.payload)
        except Exception as exc:
            self._stats["rejected_schema"] += 1
            logger.warning("invalid json: %s", exc)
            client.ack(msg.mid, msg.qos)
            return
        errors = list(self._validator.iter_errors(record))
        if errors:
            self._stats["rejected_schema"] += 1
            logger.warning("schema error: %s", errors[0].message)
            client.ack(msg.mid, msg.qos)
            return
        line_id_msg = int(record["line_id"])
        if line_id_msg != self.line_id:
            self._stats["rejected_wrong_line"] += 1
            logger.warning("wrong line_id: got %d, expected %d, mid=%s", line_id_msg, self.line_id, record.get("message_id"))
            client.ack(msg.mid, msg.qos)
            return

        mid = record["message_id"]
        if mid in self._seen_message_ids:
            self._stats["duplicate_message_id"] += 1
            client.ack(msg.mid, msg.qos)
            return
        self._seen_message_ids.append(mid)
        seq = int(record["sequence"])
        if seq <= self._last_sequence:
            self._stats["duplicate_sequence"] += 1
            client.ack(msg.mid, msg.qos)
            return
        ts = datetime.fromisoformat(record["timestamp"])
        line_id = int(record["line_id"])
        for m in record["measurements"]:
            sid = self.sensor_map.get(m["tag"])
            if sid is None:
                self._stats["rejected_unknown"] += 1
                continue
            row = {"line_id": line_id, "sensor_id": sid, "ts": ts, "value": float(m["value"]), "quality": int(m.get("quality", 0)), "source": batch_writer.SOURCE_LIVE}
            try:
                self.queue.put_nowait(row)
            except queue.Full:
                self._stats["rejected_queue_full"] += 1
                logger.warning("queue full, NOT acking message seq=%d", seq)
                return
        self._stats["accepted"] += 1
        self._last_sequence = seq
        self._buffer_last_seq = seq
        self._buffer_last_mid = mid
        self._buffer_last_ts = ts
        while True:
            try:
                self._rows_buffer.append(self.queue.get_nowait())
            except queue.Empty:
                break
        self._pending_msgs.append((msg.mid, msg.qos))
        now_mono = time.monotonic()
        should_flush = (
            len(self._rows_buffer) >= 200
            or (self._rows_buffer and now_mono - self._last_flush >= self._flush_interval)
        )
        if should_flush:
            self._flush(client)

    def _flush(self, client) -> None:
        if not self._rows_buffer:
            return
        try:
            inserted = batch_writer.insert_batch(self.line_id, self._rows_buffer, self._buffer_last_seq, self._buffer_last_mid, self._buffer_last_ts)
            logger.info("flushed %d rows, inserted=%d", len(self._rows_buffer), inserted)
            for mid, qos in self._pending_msgs:
                client.ack(mid, qos)
            self._rows_buffer = []
            self._pending_msgs = []
            self._last_flush = time.monotonic()
        except Exception:
            logger.exception("flush failed for %d rows", len(self._rows_buffer))

    def _flush_safe(self) -> None:
        if not self._rows_buffer:
            return
        try:
            inserted = batch_writer.insert_batch(self.line_id, self._rows_buffer, self._buffer_last_seq, self._buffer_last_mid, self._buffer_last_ts)
            logger.info("shutdown flush: %d rows, inserted=%d", len(self._rows_buffer), inserted)
            if self._client is not None:
                for mid, qos in self._pending_msgs:
                    self._client.ack(mid, qos)
            self._rows_buffer = []
            self._pending_msgs = []
        except Exception:
            logger.exception("shutdown flush failed")

    def _flush_timer_loop(self) -> None:
        while not self._stop.is_set():
            self._stop.wait(self._flush_interval)
            if self._stop.is_set():
                return
            if self._rows_buffer and self._client is not None:
                try:
                    self._flush(self._client)
                except Exception:
                    logger.exception("timer-driven flush failed")

    def run(self) -> None:
        topic = settings.MQTT_TOPIC_TEMPLATE.format(line_id=self.line_id, machine_id="+")
        logger.info("ingester subscribing to %s (last_sequence=%d)", topic, self._last_sequence)
        sub = MqttSubscriber(client_id=f"line-speed-30-ingester-{self.line_id}", topics=[topic], on_message=self._on_message)

        def _shutdown(signum, frame):
            logger.info("shutdown signal received")
            self._stop.set()
            self._flush_safe()
            sub.stop()

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        flush_timer = threading.Thread(target=self._flush_timer_loop, daemon=True)
        flush_timer.start()

        try:
            sub.connect_and_loop()
        finally:
            logger.info("ingester stats: %s", self._stats)