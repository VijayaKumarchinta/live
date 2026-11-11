import logging
import time
import paho.mqtt.client as mqtt
from config import settings

logger = logging.getLogger(__name__)

class MqttPublisher:
    def __init__(self, client_id: str = "line-speed-30-publisher") -> None:
        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
        self._connected = False
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self._connected = True
            logger.info("publisher connected to %s:%s", settings.MQTT_HOST, settings.MQTT_PORT)
        else:
            self._connected = False
            logger.error("publisher connect failed: %s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self._connected = False
        logger.warning("publisher disconnected: %s", reason_code)

    def connect(self, retries: int = 10, delay: float = 2.0) -> None:
        for attempt in range(1, retries + 1):
            try:
                self._client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
                self._client.loop_start()
                for _ in range(50):
                    if self._connected:
                        return
                    time.sleep(0.1)
                logger.warning("connect attempt %d/%d timed out", attempt, retries)
            except Exception as exc:
                logger.warning("connect attempt %d/%d failed: %s", attempt, retries, exc)
            time.sleep(delay)
        raise RuntimeError("could not connect to MQTT broker")

    def publish(self, topic: str, payload: str, qos: int = 1) -> None:
        if not self._connected:
            raise RuntimeError("publisher is not connected")
        info = self._client.publish(topic, payload=payload, qos=qos)
        info.wait_for_publish(timeout=5.0)

    def disconnect(self) -> None:
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            pass