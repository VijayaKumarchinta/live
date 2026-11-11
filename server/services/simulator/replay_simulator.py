import argparse
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator
from zoneinfo import ZoneInfo
import pandas as pd
from config import settings
from services.simulator.publisher import MqttPublisher

logger = logging.getLogger(__name__)

def iter_records(parquet_path: Path, line_id: int, machine_id: int, time_base: str, tz: str, start_sequence: int, loop_offset_seconds: int) -> Iterator[dict]:
    df = pd.read_parquet(parquet_path)
    if "ts" not in df.columns:
        raise RuntimeError("parquet missing 'ts' column")
    sensor_columns = [c for c in df.columns if c != "ts"]
    now = datetime.now(ZoneInfo(tz))
    step = timedelta(seconds=10)
    seq = start_sequence
    for i in range(len(df)):
        row = df.iloc[i]
        ts = now + timedelta(seconds=loop_offset_seconds) + step * i if time_base == "now" else pd.Timestamp(row["ts"]).to_pydatetime()
        measurements = [
            {"tag": col, "value": float(row[col]), "quality": 0}
            for col in sensor_columns
            if not pd.isna(row[col])
        ]
        if not measurements:
            continue
        yield {
            "schema_version": "1.0",
            "message_id": str(uuid.uuid4()),
            "line_id": line_id,
            "machine_id": machine_id,
            "timestamp": ts.isoformat(),
            "sequence": seq,
            "measurements": measurements,
        }
        seq += 1

def run(parquet_path: Path, line_id: int, machine_id: int, time_base: str, loop: bool, delay: float, max_rows: int | None, start_sequence: int) -> int:
    pub = MqttPublisher(client_id=f"line-speed-30-simulator-{line_id}-{machine_id}")
    pub.connect()
    topic = settings.MQTT_TOPIC_TEMPLATE.format(line_id=line_id, machine_id=machine_id)
    logger.info("publishing to %s (time_base=%s)", topic, time_base)
    total = 0
    loop_count = 0
    try:
        while True:
            for record in iter_records(parquet_path, line_id, machine_id, time_base, settings.PLANT_TZ, start_sequence + total, loop_count * 10 * 2139):
                pub.publish(topic, json.dumps(record), qos=settings.MQTT_QOS)
                total += 1
                if max_rows and total >= max_rows:
                    logger.info("reached max_rows=%d", max_rows)
                    return total
                if delay > 0:
                    import time
                    time.sleep(delay)
            if not loop:
                break
            loop_count += 1
            logger.info("loop mode: restarting (loop=%d)", loop_count)
    finally:
        pub.disconnect()
    return total

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="MQTT replay simulator")
    parser.add_argument("--file", required=True)
    parser.add_argument("--line", type=int, default=30)
    parser.add_argument("--machine", type=int, default=1)
    parser.add_argument("--time-base", choices=["parquet", "now"], default="now")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--start-sequence", type=int, default=1)
    args = parser.parse_args()
    path = Path(args.file).resolve()
    if not path.exists():
        raise SystemExit(f"file not found: {path}")
    total = run(path, args.line, args.machine, args.time_base, args.loop, args.delay, args.max_rows, args.start_sequence)
    print(json.dumps({"published": total}, indent=2))


if __name__ == "__main__":
    main()