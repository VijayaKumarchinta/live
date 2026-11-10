from datetime import datetime
from typing import Dict, List
import pandas as pd

def normalize(
    df: pd.DataFrame,
    line_id: int,
    sensor_map: Dict[str, int],
    source: int,
    tz: str,
) -> List[dict]:
    if "ts" not in df.columns:
        raise ValueError("dataframe missing 'ts' column")

    rows: List[dict] = []
    for idx, ts in zip(df.index, df["ts"]):
        if pd.isna(ts):
            continue
        ts_py: datetime = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else ts
        for column, sensor_id in sensor_map.items():
            value = df.at[idx, column]
            if pd.isna(value):
                continue
            rows.append(
                {
                    "line_id": line_id,
                    "sensor_id": sensor_id,
                    "ts": ts_py,
                    "value": float(value),
                    "quality": 0,
                    "source": source,
                }
            )
    return rows