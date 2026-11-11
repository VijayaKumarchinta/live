from __future__ import annotations

import argparse
import json
import logging
import math
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Dict

from config import settings
from services.simulator.publisher import MqttPublisher


logger = logging.getLogger(__name__)


# Sensor definitions: baseline, natural range, per-tick noise, and a slow sine component.
# sensor_id -> config
SENSORS: Dict[int, dict] = {
    1:  {"tag": "Burner Output Load",                       "base": 70.0,  "lo": 40.0,   "hi": 100.0, "noise": 1.5,  "sine_amp": 12.0, "sine_period": 900.0},
    2:  {"tag": "Burner PV",                                "base": 186.0, "lo": 175.0,  "hi": 195.0, "noise": 0.3,  "sine_amp": 2.0,  "sine_period": 1200.0},
    3:  {"tag": "Burner SP",                                "base": 185.0, "lo": 175.0,  "hi": 195.0, "noise": 0.05, "sine_amp": 3.0,  "sine_period": 1800.0},
    4:  {"tag": "{[PLC1]Input.Analogue.AT6802.O_Filtered}", "base": 33.0,  "lo": 20.0,   "hi": 45.0,  "noise": 0.5,  "sine_amp": 3.0,  "sine_period": 1500.0},
    5:  {"tag": "oil Level PV",                             "base": 176.0, "lo": 160.0,  "hi": 200.0, "noise": 0.4,  "sine_amp": 4.0,  "sine_period": 2400.0},
    6:  {"tag": "{[PLC1]Input.Analogue.TT4401.O_Filtered}", "base": 0.0,   "lo": 0.0,    "hi": 0.0,   "noise": 0.0,  "sine_amp": 0.0,  "sine_period": 1.0},
    7:  {"tag": "{[PLC1]Input.Analogue.TT5101.O_Filtered}", "base": 186.0, "lo": 178.0,  "hi": 194.0, "noise": 0.25, "sine_amp": 2.0,  "sine_period": 1000.0},
    8:  {"tag": "Air Inlet To Burner",                      "base": 119.0, "lo": 100.0,  "hi": 140.0, "noise": 1.0,  "sine_amp": 5.0,  "sine_period": 800.0},
    9:  {"tag": "Heat Exchanger Stack Temp",                "base": 505.0, "lo": 480.0,  "hi": 520.0, "noise": 1.5,  "sine_amp": 8.0,  "sine_period": 1500.0},
    10: {"tag": "APH Outlet",                               "base": 225.0, "lo": 210.0,  "hi": 240.0, "noise": 1.0,  "sine_amp": 6.0,  "sine_period": 1200.0},
    11: {"tag": "Ambient Air Temp",                         "base": 43.0,  "lo": 35.0,   "hi": 50.0,  "noise": 0.3,  "sine_amp": 2.0,  "sine_period": 3600.0},
    12: {"tag": "Oil Inlet Temperature",                    "base": 186.0, "lo": 178.0,  "hi": 195.0, "noise": 0.3,  "sine_amp": 3.0,  "sine_period": 1200.0},
    13: {"tag": "{[PLC1]Input.Analogue.TT6102.O_Filtered}", "base": 159.0, "lo": 145.0,  "hi": 175.0, "noise": 1.0,  "sine_amp": 5.0,  "sine_period": 1500.0},
    14: {"tag": "{[PLC1]Input.Analogue.TT7101.O_Filtered}", "base": 40.0,  "lo": 30.0,   "hi": 50.0,  "noise": 0.4,  "sine_amp": 2.0,  "sine_period": 900.0},
    15: {"tag": "{[PLC1]Input.Analogue.TT7102.O_Filtered}", "base": 40.0,  "lo": 30.0,   "hi": 50.0,  "noise": 0.4,  "sine_amp": 2.0,  "sine_period": 900.0},
    16: {"tag": "{[PLC1]Input.Analogue.TT7103.O_Filtered}", "base": 39.6,  "lo": 30.0,   "hi": 50.0,  "noise": 0.4,  "sine_amp": 2.0,  "sine_period": 900.0},
    17: {"tag": "Pump Loading",                             "base": 89.0,  "lo": 70.0,   "hi": 105.0, "noise": 1.5,  "sine_amp": 8.0,  "sine_period": 1200.0},
    18: {"tag": "Pump Load PV",                             "base": 180.6, "lo": 170.0,  "hi": 190.0, "noise": 0.3,  "sine_amp": 2.0,  "sine_period": 1500.0},
    19: {"tag": "Pump load SP",                             "base": 180.5, "lo": 175.0,  "hi": 185.0, "noise": 0.02, "sine_amp": 0.5,  "sine_period": 3600.0},
    20: {"tag": "{[PLC1]MoistureControl.I_MoistureHighSetpoint1}", "base": 1.24, "lo": 1.2, "hi": 1.3, "noise": 0.005, "sine_amp": 0.02, "sine_period": 3600.0},
    21: {"tag": "{[PLC1]MoistureControl.I_MoistureHighSetpoint2}", "base": 1.30, "lo": 1.25, "hi": 1.35, "noise": 0.005, "sine_amp": 0.02, "sine_period": 3600.0},
    22: {"tag": "{[PLC1]MoistureControl.I_MoistureLowSetpoint1}",  "base": 1.10, "lo": 1.05, "hi": 1.15, "noise": 0.005, "sine_amp": 0.02, "sine_period": 3600.0},
    23: {"tag": "{[PLC1]MoistureControl.I_MoistureLowSetpoint2}",  "base": 1.14, "lo": 1.09, "hi": 1.19, "noise": 0.005, "sine_amp": 0.02, "sine_period": 3600.0},
    24: {"tag": "{[PLC1]MoistureControl.O_SpeedPIDCV}",     "base": 0.24,  "lo": -0.5,   "hi": 0.6,   "noise": 0.02, "sine_amp": 0.1,  "sine_period": 900.0},
    25: {"tag": "Moisture PV",                              "base": 1.10,  "lo": 1.05,   "hi": 1.30,  "noise": 0.008,"sine_amp": 0.05, "sine_period": 1200.0},
    26: {"tag": "{[PLC1]MoistureControl.O_SpeedPIDSP}",     "base": 1.17,  "lo": 1.10,   "hi": 1.20,  "noise": 0.005,"sine_amp": 0.02, "sine_period": 1800.0},
    27: {"tag": "{[PLC1]MoistureControl.O_TempPIDCV}",      "base": 0.59,  "lo": -0.3,   "hi": 1.2,   "noise": 0.03, "sine_amp": 0.2,  "sine_period": 900.0},
    28: {"tag": "{[PLC1]MoistureControl.O_TempPIDPV}",      "base": 1.13,  "lo": 1.05,   "hi": 1.20,  "noise": 0.005,"sine_amp": 0.02, "sine_period": 1200.0},
    29: {"tag": "{[PLC1]MoistureControl.O_TempPIDSP}",      "base": 1.17,  "lo": 1.10,   "hi": 1.20,  "noise": 0.005,"sine_amp": 0.02, "sine_period": 1800.0},
    30: {"tag": "Paddle Speed",                             "base": 63.0,  "lo": 55.0,   "hi": 70.0,  "noise": 0.5,  "sine_amp": 3.0,  "sine_period": 900.0},
    31: {"tag": "{[PLC1]Valve.XV6601.OM_Open}",             "base": 0.0,   "lo": 0.0,    "hi": 1.0,   "noise": 0.0,  "sine_amp": 0.0,  "sine_period": 1.0},
    32: {"tag": "DeltaT",                                   "base": 25.5,  "lo": 20.0,   "hi": 30.0,  "noise": 0.2,  "sine_amp": 2.0,  "sine_period": 1200.0},
}


class LiveSensorModel:
    """Each sensor drifts within [lo, hi] around its base + a slow sine + noise."""

    def __init__(self) -> None:
        self._state: Dict[int, float] = {sid: s["base"] for sid, s in SENSORS.items()}
        self._t0 = time.monotonic()

    def step(self) -> Dict[int, float]:
        now_s = time.monotonic() - self._t0
        for sid, cfg in SENSORS.items():
            prev = self._state[sid]
            sine = cfg["sine_amp"] * math.sin(2 * math.pi * now_s / cfg["sine_period"] + sid * 0.3)
            target = cfg["base"] + sine
            noise = random.gauss(0, cfg["noise"])
            new = prev + (target - prev) * 0.15 + noise
            new = max(cfg["lo"], min(cfg["hi"], new))
            self._state[sid] = new
        return dict(self._state)


def build_message(line_id: int, machine_id: int, sequence: int, values: Dict[int, float]) -> dict:
    return {
        "schema_version": "1.0",
        "message_id": str(uuid.uuid4()),
        "line_id": line_id,
        "machine_id": machine_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": sequence,
        "measurements": [
            {"tag": SENSORS[sid]["tag"], "value": round(v, 4), "quality": 0}
            for sid, v in values.items()
        ],
    }


def run(line_id: int, machine_id: int, interval: float, start_sequence: int, max_ticks: int) -> int:
    pub = MqttPublisher(client_id=f"line-speed-30-live-{line_id}-{machine_id}")
    pub.connect()
    topic = settings.MQTT_TOPIC_TEMPLATE.format(line_id=line_id, machine_id=machine_id)
    logger.info("live simulator publishing to %s every %.1fs", topic, interval)

    model = LiveSensorModel()
    tick_count = 0
    seq = start_sequence
    try:
        while True:
            values = model.step()
            msg = build_message(line_id, machine_id, seq, values)
            pub.publish(topic, json.dumps(msg), qos=settings.MQTT_QOS)
            logger.info("tick %d · seq=%d · burner=%.2f moisture=%.3f", tick_count, seq, values[1], values[25])
            tick_count += 1
            seq += 1
            if max_ticks and tick_count >= max_ticks:
                logger.info("reached max_ticks=%d", max_ticks)
                break
            time.sleep(interval)
    finally:
        pub.disconnect()
    return tick_count


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    p = argparse.ArgumentParser(description="Live MQTT simulator — emits evolving sensor values")
    p.add_argument("--line", type=int, default=30)
    p.add_argument("--machine", type=int, default=1)
    p.add_argument("--interval", type=float, default=5.0, help="seconds between messages")
    p.add_argument("--start-sequence", type=int, default=1)
    p.add_argument("--max-ticks", type=int, default=0, help="0 = run forever")
    a = p.parse_args()
    n = run(a.line, a.machine, a.interval, a.start_sequence, a.max_ticks)
    print(json.dumps({"ticks": n}, indent=2))


if __name__ == "__main__":
    main()