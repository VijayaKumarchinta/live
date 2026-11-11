import logging
from typing import Callable, List
import paho.mqtt.client as mqtt
from config import settings

logger = logging.getLogger(__name__)

class MqttSubscriber:
    def __init__(self, client_id: str, topics: List[str], on_message: Callable) -> None:
        self._topics = topics
        self._on_message_user = on_message
        self._client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, manual_ack=True)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect
        
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            for topic in self._topics:
                client.subscribe(topic, qos=settings.MQTT_QOS)
                logger.info("subscribed to %s (qos=%d)", topic, settings.MQTT_QOS)
        else:
            logger.error("subscriber connect failed: %s", reason_code)

    def _on_message(self, client, userdata, msg):
        try:
            self._on_message_user(client, userdata, msg)
        except Exception:
            logger.exception("on_message handler raised")

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            logger.warning("subscriber disconnected: %s", reason_code)

    def connect_and_loop(self) -> None:
        self._client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
        self._client.loop_forever()

    def stop(self) -> None:
        try:
            self._client.disconnect()
            self._client.loop_stop()
        except Exception:
            pass